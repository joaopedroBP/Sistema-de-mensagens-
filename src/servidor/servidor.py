import zmq
import message_pb2
import time
import os

SERVER_ID = os.getenv("SERVER_ID", "1")
LOG_DIR = "data"
LOG_FILE = os.path.join(LOG_DIR, f"storage_server_{SERVER_ID}.txt")

def save_event(event_type, user, detail=""):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    with open(LOG_FILE, "a") as f:
        line = f"[{timestamp}] {event_type} | User: {user} | Info: {detail}\n"
        f.write(line)

context = zmq.Context()

# Conexoes
socket_rep = context.socket(zmq.REP)
socket_rep.connect("tcp://broker:5556")

socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://proxy_pubsub:5557")

socket_ref = context.socket(zmq.REQ)
socket_ref.connect("tcp://referencia:5559")

socket_peer_rep = context.socket(zmq.REP)
socket_peer_rep.bind("tcp://*:5560")

socket_sub_servers = context.socket(zmq.SUB)
socket_sub_servers.connect("tcp://proxy_pubsub:5558")
socket_sub_servers.setsockopt_string(zmq.SUBSCRIBE, "servers")
socket_sub_servers.setsockopt_string(zmq.SUBSCRIBE, "replicacao")

# Registro inicial na referencia
socket_ref.send_string(f"nome:{SERVER_ID}")
resposta_rank = socket_ref.recv_string()
meu_rank = int(resposta_rank.split(":")[1])
print(f"--- Servidor {SERVER_ID} Iniciado | Rank: {meu_rank} ---")

channels = set()
counter = 0
coordenador = None
ultimo_heartbeat = time.time()

def iniciar_eleicao():
    global coordenador
    print(f"[{SERVER_ID}] Iniciando eleicao...")
    
    socket_ref.send_string("list")
    res_lista = socket_ref.recv_string()
    lista_servidores = {}
    if res_lista.startswith("lista:"):
        for p in res_lista.split(":")[1].split(";"):
            if p:
                n, r = p.split(",")
                lista_servidores[n] = int(r)

    maiores = [n for n, r in lista_servidores.items() if r > meu_rank]
    alguem_respondeu = False
    
    for vizinho in maiores:
        req = context.socket(zmq.REQ)
        req.setsockopt(zmq.RCVTIMEO, 2000)
        req.connect(f"tcp://servidor{vizinho}:5560")
        try:
            req.send_string("eleicao")
            if req.recv_string() == "OK":
                alguem_respondeu = True
        except:
            pass
        finally:
            req.close()
            
    if not alguem_respondeu:
        print(f"[{SERVER_ID}] VENCI A ELEICAO! Sou o Coordenador.")
        coordenador = SERVER_ID
        socket_pub.send_multipart([b"servers", SERVER_ID.encode('utf-8')])

iniciar_eleicao()
ultimo_heartbeat = time.time()  

while True:
    try:
        raw_data = socket_rep.recv(flags=zmq.NOBLOCK)
        
        req = message_pb2.Message()
        req.ParseFromString(raw_data)
        
        # Regra 2 do Relogio Lógico: Atualiza com o maior valor recebido
        counter = max(counter, req.counter)
        
        res = message_pb2.Message()
        res.timestamp = int(time.time())
        res.type = message_pb2.Message.RESPONSE
        res.username = req.username
        
        if req.type == message_pb2.Message.LOGIN:
            save_event("LOGIN", req.username)
            msg_rep = f"{SERVER_ID}|LOGIN|{req.username}|"
            socket_pub.send_multipart([b"replicacao", msg_rep.encode('utf-8')])
            res.message = "LOGIN_OK"

        elif req.type == message_pb2.Message.CREATE_CHANNEL:
            if req.channel and req.channel not in channels:
                channels.add(req.channel)
                save_event("CHANNEL_CREATED", req.username, req.channel)
                msg_rep = f"{SERVER_ID}|CHANNEL_CREATED|{req.username}|{req.channel}"
                socket_pub.send_multipart([b"replicacao", msg_rep.encode('utf-8')])
                res.message = "CHANNEL_OK"
            else:
                res.message = "ERROR: Channel already exists"

        elif req.type == message_pb2.Message.LIST_CHANNELS:
            res.channels.extend(list(channels))
            res.message = "LIST_OK"

        elif req.type == message_pb2.Message.PUBLISH:
            if req.channel in channels:
                save_event("PUBLISHED", req.username, f"Canal: {req.channel}")
                
                msg_rep = f"{SERVER_ID}|PUBLISHED|{req.username}|Canal: {req.channel}"
                socket_pub.send_multipart([b"replicacao", msg_rep.encode('utf-8')])
                
                # Regra 1 do Relogio Lógico: Incrementa antes de enviar para o Proxy
                counter += 1
                req.counter = counter 
                topic = req.channel.encode('utf-8')
                socket_pub.send_multipart([topic, req.SerializeToString()])
                res.message = "PUBLISH_OK"
            else:
                res.message = "ERROR: Channel does not exist"

        # Regra 1: Incrementa antes de enviar a resposta ao cliente
        counter += 1
        res.counter = counter
        socket_rep.send(res.SerializeToString())

    except zmq.error.Again:
        pass

    agora = time.time()
    if agora - ultimo_heartbeat >= 5:
        try:
            socket_ref.send_string(f"heartbeat:{SERVER_ID}", flags=zmq.NOBLOCK)
            socket_ref.recv_string()
        except zmq.error.Again:
            pass  
        ultimo_heartbeat = agora

        if coordenador and coordenador != SERVER_ID:
            req_hora = context.socket(zmq.REQ)
            req_hora.setsockopt(zmq.RCVTIMEO, 2000)
            req_hora.connect(f"tcp://servidor{coordenador}:5560")
            try:
                req_hora.send_string("relogio")
                hora = req_hora.recv_string()
                print(f"[{SERVER_ID}] Berkeley: Hora sincronizada com o coordenador: {hora}")
            except:
                print(f"[{SERVER_ID}] Coordenador sumiu! Puxando nova eleicao...")
                coordenador = None
                iniciar_eleicao()
                ultimo_heartbeat = time.time() 
            finally:
                req_hora.close()

    try:
        msg_peer = socket_peer_rep.recv_string(flags=zmq.NOBLOCK)
        if msg_peer == "relogio":
            socket_peer_rep.send_string(str(int(time.time())))
        elif msg_peer == "eleicao":
            socket_peer_rep.send_string("OK")
            iniciar_eleicao()
            ultimo_heartbeat = time.time()
    except zmq.error.Again:
        pass

    try:
        topico = socket_sub_servers.recv(flags=zmq.NOBLOCK)
        conteudo = socket_sub_servers.recv()
        
        if topico == b"servers":
            novo_rei = conteudo.decode('utf-8')
            coordenador = novo_rei
            print(f"[{SERVER_ID}] Recebi o aviso: O novo Coordenador e o {coordenador}")
            
        elif topico == b"replicacao":
            partes = conteudo.decode('utf-8').split('|')
            origem = partes[0]
            
            if origem != SERVER_ID:
                evento = partes[1]
                usuario = partes[2]
                detalhe = partes[3] if len(partes) > 3 else ""
                
                if evento == "CHANNEL_CREATED":
                    channels.add(detalhe)
                
                save_event(f"REPLICA_{evento}", usuario, detalhe)

    except zmq.error.Again:
        pass

    time.sleep(0.01)

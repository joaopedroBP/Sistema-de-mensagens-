import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5559")

servidores = {}
proximo_rank = 1

print("--- Serviço de Referência (Coordenador) Iniciado ---")

while True:
    if socket.poll(1000): 
        msg = socket.recv_string()
        partes = msg.split(":")
        comando = partes[0]
        
        if comando == "nome":
            nome_srv = partes[1]
            if nome_srv not in servidores:
                servidores[nome_srv] = {"rank": proximo_rank, "last_beat": time.time()}
                proximo_rank += 1
            rank = servidores[nome_srv]["rank"]
            socket.send_string(f"rank:{rank}")
            print(f"[NOVO] {nome_srv} registrado com Rank {rank}")

        elif comando == "list":
            lista_str = ";".join([f"{nome},{dados['rank']}" for nome, dados in servidores.items()])
            socket.send_string(f"lista:{lista_str}")

        elif comando == "heartbeat":
            nome_srv = partes[1]
            if nome_srv in servidores:
                servidores[nome_srv]["last_beat"] = time.time()
                hora_certa = int(time.time())
                socket.send_string(f"OK:{hora_certa}")
            else:
                socket.send_string("ERROR: Servidor desconhecido")

    agora = time.time()
    mortos = [nome for nome, dados in servidores.items() if (agora - dados["last_beat"]) > 15]
    for morto in mortos:
        print(f"[ALERTA] Servidor {morto} não enviou heartbeat. Removendo da lista.")
        del servidores[morto]

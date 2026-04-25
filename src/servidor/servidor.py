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

socket_rep = context.socket(zmq.REP)
socket_rep.connect("tcp://broker:5556")

socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://proxy_pubsub:5557")

socket_ref = context.socket(zmq.REQ)
socket_ref.connect("tcp://referencia:5559")

socket_ref.send_string(f"nome:{SERVER_ID}")
resposta_rank = socket_ref.recv_string()
meu_rank = int(resposta_rank.split(":")[1])
print(f"--- Servidor {SERVER_ID} Iniciado | Rank: {meu_rank} ---")

channels = set()
counter = 0
mensagens_processadas = 0

while True:
    raw_data = socket_rep.recv()
    mensagens_processadas += 1
    
    req = message_pb2.Message()
    req.ParseFromString(raw_data)
    
    counter = max(counter, req.counter)
    
    res = message_pb2.Message()
    res.timestamp = int(time.time())
    res.type = message_pb2.Message.RESPONSE
    res.username = req.username
    
    if req.type == message_pb2.Message.LOGIN:
        save_event("LOGIN", req.username)
        res.message = "LOGIN_OK"

    elif req.type == message_pb2.Message.CREATE_CHANNEL:
        if req.channel and req.channel not in channels:
            channels.add(req.channel)
            save_event("CHANNEL_CREATED", req.username, req.channel)
            res.message = "CHANNEL_OK"
        else:
            res.message = "ERROR: Channel already exists or invalid"

    elif req.type == message_pb2.Message.LIST_CHANNELS:
        res.channels.extend(list(channels))
        res.message = "LIST_OK"

    elif req.type == message_pb2.Message.PUBLISH:
        if req.channel in channels:
            save_event("PUBLISHED", req.username, f"Canal: {req.channel} | Msg: {req.message}")
            
            counter += 1
            req.counter = counter 
            
            topic = req.channel.encode('utf-8')
            socket_pub.send_multipart([topic, req.SerializeToString()])
            
            res.message = "PUBLISH_OK"
        else:
            res.message = "ERROR: Channel does not exist"

    counter += 1
    res.counter = counter
    socket_rep.send(res.SerializeToString())

    if mensagens_processadas % 10 == 0:
        socket_ref.send_string("list")
        res_lista = socket_ref.recv_string()
        
        socket_ref.send_string(f"heartbeat:{SERVER_ID}")
        res_beat = socket_ref.recv_string()
        if res_beat.startswith("OK"):
            hora_referencia = int(res_beat.split(":")[1])
            print(f"[{SERVER_ID}] Heartbeat OK | Hora Ref: {hora_referencia} | Lista: {res_lista.split(':')[1]}")

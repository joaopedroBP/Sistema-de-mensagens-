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

channels = set()
counter = 0
print(f"--- Servidor {SERVER_ID} Iniciado (REP: broker, PUB: proxy_pubsub) ---")

while True:
    raw_data = socket_rep.recv()
    
    req = message_pb2.Message()
    req.ParseFromString(raw_data)
    
    res = message_pb2.Message()
    res.timestamp = int(time.time())
    res.type = message_pb2.Message.RESPONSE
    res.username = req.username
    res.counter = counter
    
    if req.type == message_pb2.Message.LOGIN:
        save_event("LOGIN", req.username)
        res.message = "LOGIN_OK"
        counter += 1

    elif req.type == message_pb2.Message.CREATE_CHANNEL:
        if req.channel and req.channel not in channels:
            channels.add(req.channel)
            save_event("CHANNEL_CREATED", req.username, req.channel)
            res.message = "CHANNEL_OK"
            counter += 1
        else:
            res.message = "ERROR: Channel already exists or invalid"

    elif req.type == message_pb2.Message.LIST_CHANNELS:
        res.channels.extend(list(channels))
        res.message = "LIST_OK"
        counter += 1

    elif req.type == message_pb2.Message.PUBLISH:
        print(f"[{SERVER_ID}] Recebeu msg de {req.username} para o canal {req.channel}")
        
        if req.channel in channels:
            # Salva no disco
            save_event("PUBLISHED", req.username, f"Canal: {req.channel} | Msg: {req.message}")
            
            topic = req.channel.encode('utf-8')
            socket_pub.send_multipart([topic, raw_data])
            
            res.message = "PUBLISH_OK"
            counter += 1
        else:
            res.message = "ERROR: Channel does not exist"

    socket_rep.send(res.SerializeToString())

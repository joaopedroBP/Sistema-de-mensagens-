import zmq
import message_pb2
import time
import os

SERVER_ID = os.getenv("SERVER_ID", "1")
LOG_DIR = "data"
LOG_FILE = os.path.join(LOG_DIR, f"storage_server_{SERVER_ID}.txt")

def save_event(event_type, user, detail=""):
    """Função para persistir os dados em disco conforme requisito do projeto."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    with open(LOG_FILE, "a") as f:
        line = f"[{timestamp}] {event_type} | User: {user} | Info: {detail}\n"
        f.write(line)

context = zmq.Context()
socket = context.socket(zmq.REP)

socket.connect("tcp://broker:5556")

channels = set()

print(f"--- Servidor {SERVER_ID} Iniciado e Conectado ao Broker ---")

while True:
    raw_data = socket.recv()
    
    req = message_pb2.Message()
    req.ParseFromString(raw_data)
    
    res = message_pb2.Message()
    res.timestamp = int(time.time())
    res.type = message_pb2.Message.RESPONSE
    res.username = req.username  # Devolve o nome para o bot exibir no log
    
    if req.type == message_pb2.Message.LOGIN:
        print(f"[{SERVER_ID}] LOGIN recebido: {req.username}")
        save_event("LOGIN", req.username)
        res.message = "LOGIN_OK"

    elif req.type == message_pb2.Message.CREATE_CHANNEL:
        print(f"[{SERVER_ID}] CREATE_CHANNEL: {req.channel} (por {req.username})")
        
        if req.channel and req.channel not in channels:
            channels.add(req.channel)
            save_event("CHANNEL_CREATED", req.username, req.channel)
            res.message = "CHANNEL_OK"
        else:
            res.message = "ERROR: Channel already exists or invalid name"

    elif req.type == message_pb2.Message.LIST_CHANNELS:
        print(f"[{SERVER_ID}] LIST_CHANNELS solicitado por: {req.username}")
        # O campo 'channels' no protobuf é 'repeated', usamos extend para passar a lista
        res.channels.extend(list(channels))
        res.message = "LIST_OK"

    # Envia a resposta de volta
    socket.send(res.SerializeToString())

import zmq
import message_pb2
import time

context = zmq.Context()

socket = context.socket(zmq.REP)
socket.connect("tcp://broker:5556") # Conecta no BACKEND do broker

print("Servidor rodando (REP)...")

while True:
    data = socket.recv()
    
    msg = message_pb2.Message()
    msg.ParseFromString(data)
    print(f"Recebido: user={msg.username}")

    response = message_pb2.Message()
    response.type = msg.type
    response.username = msg.username
    response.message = "Login realizado com sucesso"
    response.timestamp = int(time.time())

    socket.send(response.SerializeToString())

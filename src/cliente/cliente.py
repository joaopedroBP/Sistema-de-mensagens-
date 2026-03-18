import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REQ)

socket.connect("tcp://servidor:5555")

time.sleep(1)

usr = "joao"
timestamp = int(time.time())

msg = f"Login:{usr}:{timestamp}"
print("Mensagem enviada!", flush=True)

socket.send_string(msg)

reply = socket.recv_string()
print(f"Resposta recebida: {reply}", flush=True)

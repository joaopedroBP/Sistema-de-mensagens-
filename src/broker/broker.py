import zmq

context = zmq.Context()
poller = zmq.Poller()

# Socket para os clientes (REQ)
client_socket = context.socket(zmq.ROUTER)
client_socket.bind("tcp://*:5555")
poller.register(client_socket, zmq.POLLIN)

# Socket para os servidores (REP)
server_socket = context.socket(zmq.DEALER)
server_socket.bind("tcp://*:5556")
poller.register(server_socket, zmq.POLLIN)

client_count = 0
server_count = 0

while True:
    socks = dict(poller.poll())

    # Mensagens dos clientes
    if socks.get(client_socket) == zmq.POLLIN:
        client_count += 1
        # Receber todos os frames da mensagem do cliente
        frames = []
        while True:
            frame = client_socket.recv()
            frames.append(frame)
            if not client_socket.getsockopt(zmq.RCVMORE):
                break

        # Encaminhar todos os frames para o servidor
        for i, frame in enumerate(frames):
            if i < len(frames) - 1:
                server_socket.send(frame, zmq.SNDMORE)
            else:
                server_socket.send(frame)

        print(f"Client messages: {client_count}", flush=True)

    # Mensagens dos servidores
    if socks.get(server_socket) == zmq.POLLIN:
        server_count += 1
        # Receber todos os frames da mensagem do servidor
        frames = []
        while True:
            frame = server_socket.recv()
            frames.append(frame)
            if not server_socket.getsockopt(zmq.RCVMORE):
                break

        # Encaminhar todos os frames para o cliente
        for i, frame in enumerate(frames):
            if i < len(frames) - 1:
                client_socket.send(frame, zmq.SNDMORE)
            else:
                client_socket.send(frame)

        print(f"Server messages: {server_count}", flush=True)

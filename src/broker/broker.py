import zmq

context = zmq.Context()

# Clientes conectam aqui (ROUTER preserva a identidade do cliente REQ)
frontend = context.socket(zmq.ROUTER)
frontend.bind("tcp://*:5555")

# Servidores conectam aqui
backend = context.socket(zmq.DEALER)
backend.bind("tcp://*:5556")

print("Broker rodando (ROUTER <-> DEALER)...")

# O proxy gerencia a passagem de mensagens e os IDs de retorno automaticamente
zmq.proxy(frontend, backend)

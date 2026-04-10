import zmq

context = zmq.Context()

# Clientes conectam aqui 
frontend = context.socket(zmq.ROUTER)
frontend.bind("tcp://*:5555")

# Servidores conectam aqui
backend = context.socket(zmq.DEALER)
backend.bind("tcp://*:5556")

print("Broker rodando (ROUTER <-> DEALER)...")

zmq.proxy(frontend, backend)

import zmq

context = zmq.Context()

pub = context.socket(zmq.XPUB)
pub.bind("tcp://*:5558")

sub = context.socket(zmq.XSUB)
sub.bind("tcp://*:5557")

try:
    zmq.proxy(sub,pub)
except KeyboardInterrupt:
    print("Desligando o proxy...")
finally:
    pub.close()
    sub.close()
    context.close()   
    



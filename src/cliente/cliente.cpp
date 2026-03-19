#include <zmq.hpp>
#include <iostream>
#include <thread>
#include <chrono>
#include "message.pb.h"

using namespace std;

int main() {
    zmq::context_t context(1);

    zmq::socket_t socket(context, zmq::socket_type::req);
    socket.connect("tcp://broker:5555");  // conecta na porta ROUTER do broker

    int i = 0;

    while (true) {
        chat::Message msg;
        msg.set_type(chat::Message::LOGIN);
        msg.set_username("joao");
        msg.set_timestamp(time(nullptr));

        string serialized;
        msg.SerializeToString(&serialized);

        zmq::message_t request(serialized.size());
        memcpy(request.data(), serialized.data(), serialized.size());

        cout << "Enviando login " << i << "..." << endl;

        // envia pro broker
        socket.send(request, zmq::send_flags::none);

        // recebe resposta do broker
        zmq::message_t reply;
        socket.recv(reply, zmq::recv_flags::none);

        chat::Message response;
        response.ParseFromArray(reply.data(), reply.size());

        cout << "Resposta: " << response.message() << endl;

        i++;
        this_thread::sleep_for(chrono::seconds(1));
    }

    return 0;
}

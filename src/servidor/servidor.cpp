#include <zmq.hpp>
#include <iostream>
#include <string>
#include <ctime>
#include <cstring>
using namespace std;


int main(){
    zmq::context_t context(1);
    zmq::socket_t socket(context,ZMQ_REP);

    socket.bind("tcp://*:5555");

    while(true){
        zmq::message_t request;

        socket.recv(request, zmq::recv_flags::none);

        string msg(static_cast<char*>(request.data()), request.size());

        time_t now = std::time(nullptr);

        cout << "[RECEBIDO] " << now << " | " << msg << endl;

        // Resposta
        string reply = "LOGIN_OK";

        zmq::message_t response(reply.size());
        memcpy(response.data(), reply.c_str(), reply.size());

        socket.send(response, zmq::send_flags::none);

        cout << "[ENVIADO] " << now << " | " << reply << endl;
    }
    return 0;
}

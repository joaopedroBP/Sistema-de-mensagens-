#include <zmq.hpp>
#include <iostream>
#include <thread>
#include <chrono>

using namespace std;

int main() {
    zmq::context_t context(1);

    zmq::socket_t socket(context, zmq::socket_type::req);
    socket.connect("tcp://broker:5555");

    int i = 0;

    while (true) {
        zmq::message_t request(5);
        memcpy(request.data(), "Hello", 5);

        std::cout << "Mensagem " << i << ": " << std::flush;

        socket.send(request, zmq::send_flags::none);

        zmq::message_t reply;
        socket.recv(reply, zmq::recv_flags::none);

        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        std::cout << reply_str << endl;

        i++;
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    return 0;
}

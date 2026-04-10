#include <zmq.hpp>
#include <iostream>
#include <thread>
#include <chrono>
#include <unistd.h>
#include "message.pb.h"

using namespace std;

// Função para exibir as trocas de mensagens de forma legível 
void log_message(const string& action, const chat::Message& msg) {
    cout << "\n========================================" << endl;
    cout << "  " << action << endl;
    cout << "----------------------------------------" << endl;
    cout << "  User:      " << msg.username() << endl;
    cout << "  Status:    " << msg.message() << endl;
    cout << "  Timestamp: " << msg.timestamp() << endl;
    
    if (msg.channels_size() > 0) {
        cout << "  Canais Disponíveis:" << endl;
        for(int i = 0; i < msg.channels_size(); i++) {
            cout << "    - " << msg.channels(i) << endl;
        }
    }
    cout << "========================================\n" << endl;
}

int main() {
    zmq::context_t context(1);
    zmq::socket_t socket(context, zmq::socket_type::req);
    socket.connect("tcp://broker:5555");

    // Tenta ler o nome definido no docker-compose, se não existir usa o PID
    const char* env_user = getenv("BOT_NAME");
    string user = (env_user) ? string(env_user) : "bot_cpp_" + to_string(getpid());
    
    int state = 0; 
    cout << ">>> " << user << " iniciado e aguardando broker..." << endl;

    while (true) {
        chat::Message req;
        req.set_username(user);
        req.set_timestamp(time(nullptr));

        //Login -> Criar Canal -> Listar
        if (state == 0) {
            req.set_type(chat::Message::LOGIN);
        } else if (state == 1) {
            req.set_type(chat::Message::CREATE_CHANNEL);
            req.set_channel("canal_geral");
        } else {
            req.set_type(chat::Message::LIST_CHANNELS);
        }

        string serialized;
        req.SerializeToString(&serialized);
        socket.send(zmq::buffer(serialized), zmq::send_flags::none);

        zmq::message_t reply;
        auto res_recv = socket.recv(reply, zmq::recv_flags::none);

        if (res_recv) {
            chat::Message res;
            res.ParseFromArray(reply.data(), reply.size());
            log_message("RESPOSTA RECEBIDA", res);

            // Avança o estado até chegar em 2 (Listar)
            if (state < 2){
		state++;
	    }
        }

        // Delay para facilitar o acompanhamento no terminal
        this_thread::sleep_for(chrono::seconds(5));
    }
    return 0;
}

#include <zmq.hpp>
#include <iostream>
#include <chrono>
#include <unistd.h>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <ctime>
#include "message.pb.h"

using namespace std;

chat::Message enviar_requisicao(zmq::socket_t& socket, chat::Message& requisicao, int& relogio_logico) {
    relogio_logico++;
    requisicao.set_counter(relogio_logico);

    string serializada;
    requisicao.SerializeToString(&serializada);
    socket.send(zmq::buffer(serializada), zmq::send_flags::none);

    zmq::message_t resposta_bruta;
    if (socket.recv(resposta_bruta, zmq::recv_flags::none)) {}

    chat::Message resposta;
    resposta.ParseFromArray(resposta_bruta.data(), resposta_bruta.size());
    
    relogio_logico = std::max(relogio_logico, (int)resposta.counter());
    return resposta;
}

enum EstadoBot {
    SINCRONIZAR_CANAIS,
    AVALIAR_REGRAS,
    PUBLICANDO
};

int main() {
    srand(time(nullptr));

    zmq::context_t contexto(1);
    
    zmq::socket_t socket_req(contexto, zmq::socket_type::req);
    socket_req.connect("tcp://broker:5555");

    zmq::socket_t socket_sub(contexto, zmq::socket_type::sub);
    socket_sub.connect("tcp://proxy_pubsub:5558");
    
    int relogio_logico = 0;
    
    const char* env_usuario = getenv("BOT_NAME");
    string usuario = (env_usuario) ? string(env_usuario) : "bot_" + to_string(getpid());
        
    chat::Message requisicao;
    requisicao.set_username(usuario);
    requisicao.set_type(chat::Message::LOGIN);
    requisicao.set_timestamp(time(nullptr));
    
    enviar_requisicao(socket_req, requisicao, relogio_logico);
    cout << ">>> " << usuario << " Logado com sucesso!" << endl;

    EstadoBot estado_atual = SINCRONIZAR_CANAIS;
    vector<string> canais_disponiveis;
    vector<string> canais_inscritos;
    
    int mensagens_enviadas = 0;
    string canal_alvo = "";
    
    auto ultimo_envio = chrono::steady_clock::now() - chrono::seconds(2); 

    while (true) {
        
        zmq::message_t mensagem_topico;
        if (socket_sub.recv(mensagem_topico, zmq::recv_flags::dontwait)) {
            zmq::message_t mensagem_dados;
            
            if (socket_sub.recv(mensagem_dados, zmq::recv_flags::none)) {} 
            
            chat::Message mensagem_publicada;
            mensagem_publicada.ParseFromArray(mensagem_dados.data(), mensagem_dados.size());

            relogio_logico = std::max(relogio_logico, (int)mensagem_publicada.counter());

            auto tempo_recebimento = chrono::duration_cast<chrono::seconds>(chrono::system_clock::now().time_since_epoch()).count();

            cout << "\n========================================" << endl;
            cout << "  NOVA MENSAGEM RECEBIDA [" << mensagem_publicada.channel() << "]" << endl;
            cout << "----------------------------------------" << endl;
            cout << "  De:       " << mensagem_publicada.username() << endl;
            cout << "  Msg:      " << mensagem_publicada.message() << endl;
            cout << "  T. Envio: " << mensagem_publicada.timestamp() << endl;
            cout << "  T. Recv:  " << tempo_recebimento << endl;
            cout << "  COUNT:    " << mensagem_publicada.counter() << endl;
            cout << "========================================\n" << endl;
        }

        switch (estado_atual) {
            case SINCRONIZAR_CANAIS: {
                requisicao.set_type(chat::Message::LIST_CHANNELS);
                chat::Message resposta = enviar_requisicao(socket_req, requisicao, relogio_logico);
                
                canais_disponiveis.clear();
                for (int i = 0; i < resposta.channels_size(); i++) {
                    canais_disponiveis.push_back(resposta.channels(i));
                }
                estado_atual = AVALIAR_REGRAS;
                break;
            }

            case AVALIAR_REGRAS: {
                if (canais_disponiveis.size() < 5) {
                    requisicao.set_type(chat::Message::CREATE_CHANNEL);
                    requisicao.set_channel("canal_" + to_string(rand() % 1000));
                    enviar_requisicao(socket_req, requisicao, relogio_logico);
                    estado_atual = SINCRONIZAR_CANAIS; 
                } 
                else if (canais_inscritos.size() < 3) {
                    for (const auto& canal : canais_disponiveis) {
                        if (find(canais_inscritos.begin(), canais_inscritos.end(), canal) == canais_inscritos.end()) {
                            socket_sub.set(zmq::sockopt::subscribe, canal);
                            canais_inscritos.push_back(canal);
                            cout << "[!] " << usuario << " se inscreveu no canal: " << canal << endl;
                            break;
                        }
                    }
                    estado_atual = SINCRONIZAR_CANAIS; 
                } 
                else {
                    canal_alvo = canais_disponiveis[rand() % canais_disponiveis.size()];
                    mensagens_enviadas = 0;
                    cout << "\n>>> " << usuario << " iniciando 10 publicacoes no [" << canal_alvo << "]\n" << endl;
                    estado_atual = PUBLICANDO;
                }
                break;
            }

            case PUBLICANDO: {
                auto agora = chrono::steady_clock::now();
                auto tempo_passado = chrono::duration_cast<chrono::milliseconds>(agora - ultimo_envio).count();

                if (tempo_passado >= 1000) {
                    requisicao.set_type(chat::Message::PUBLISH);
                    requisicao.set_channel(canal_alvo);
                    requisicao.set_message("Mensagem de teste " + to_string(mensagens_enviadas + 1));
                    requisicao.set_timestamp(time(nullptr));
                    
                    enviar_requisicao(socket_req, requisicao, relogio_logico);
                    
                    ultimo_envio = agora;
                    mensagens_enviadas++;

                    if (mensagens_enviadas >= 10) {
                        estado_atual = SINCRONIZAR_CANAIS;
                    }
                }
                break;
            }
        }

        usleep(10000);
    }

    return 0;
}

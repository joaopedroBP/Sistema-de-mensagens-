# Projeto BBS/IRC Moderno - Parte 2

## 1. Introdução
Esta segunda etapa expande o sistema para suportar a troca de mensagens em tempo real dentro dos canais criados. O foco desta versão é a implementação do padrão Publish/Subscribe (Pub/Sub), permitindo o envio e recebimento assíncrono de mensagens entre os clientes, além de garantir a precisão dos timestamps de envio e recebimento.

## 2. Escolhas Técnicas

### Arquitetura de Comunicação
Para separar o tráfego de controle do tráfego de mensagens, a arquitetura foi dividida:
* **Broker (REQ/REP):** Continua lidando com as requisições de controle (Login, Criar Canal, Listar Canais).
* **Proxy Pub/Sub (XPUB/XSUB):** Foi adicionado um novo nó central exclusivo para o roteamento de mensagens. Ele recebe as publicações validadas pelos servidores e faz o repasse (broadcast) apenas para os clientes inscritos nos respectivos canais.

### Cliente (C++)
O maior desafio no cliente foi permitir o envio de mensagens (com intervalo de 1 segundo) e a escuta de novas mensagens simultaneamente, sem atrasar o registro de chegada (timestamp).
* Para fazer a comunicação simultânea no servidor foi usado um **Event Loop não-bloqueante**.
* A leitura de mensagens do proxy é feita de forma contínua usando a flag `dontwait` do ZeroMQ.
* O intervalo de 1 segundo entre as postagens é controlado checando o tempo decorrido via relógio do sistema (`std::chrono`), evitando o uso de funções de pausa que travariam a recepção de mensagens.

### Servidor (Python)
Para otimizar o repasse das mensagens do servidor para o Proxy, adotou-se o uso do `send_multipart` do ZeroMQ. O servidor envia a mensagem dividida em duas partes: o tópico (nome do canal em texto) e o payload (a mensagem original em binário Protobuf), evitando a necessidade de remontar o pacote no meio do caminho.

## 3. Persistência de Dados
A estratégia de armazenamento individual em Volumes do Docker foi mantida. Agora, além de registrar os logins e as criações de canais, cada servidor grava todas as publicações aprovadas em seu próprio arquivo de texto (`storage_server_X.txt`). O registro inclui o evento `PUBLISHED`, o autor, o canal alvo e o conteúdo da mensagem, garantindo o histórico completo das conversas no disco do hospedeiro.

## 4. Como Executar
O processo de execução permanece o mesmo. Para subir toda a infraestrutura com a nova funcionalidade de mensageria, basta utilizar o comando:

```bash
docker-compose up --build
```

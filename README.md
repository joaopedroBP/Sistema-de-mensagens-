# Projeto BBS/IRC Moderno - Parte 1

## 1. Introdução
Este projeto é a primeira etapa de um sistema de troca de mensagens distribuído, inspirado nos sistemas BBS e IRC. Esta versão inicial foca no processo de **Login**, **Criação de Canais** e **Listagem de Canais** utilizando containers Docker e comunicação via ZeroMQ.

## 2. Escolhas Técnicas

### Linguagens de Programação
* **Servidor e Broker (Python):** A escolha pelo Python deve-se ao fato de ser a linguagem principal utilizada em aula, o que facilitou a implementação da lógica de persistência e do roteamento de mensagens (Broker).
* **Cliente (C++):** O cliente foi desenvolvido em C++ por ser uma linguagem com a qual o desenvolvedor possui maior familiaridade e domínio.Utiliza-se a biblioteca `cppzmq` e o suporte nativo ao Protobuf para garantir a performance e a integração.

### Serialização (Protocol Buffers)
Inicialmente, foi considerada a utilização do *MessagePack*, porém, devido a dificuldades de implementação, optou-se pelo **Protobuf**. O Protobuf foi mais fácil de configurar para o projeto e se mostrou bem robusto para a comunicação entre os clientes e os servidores.

### Comunicação (ZeroMQ)
O projeto utiliza o padrão de mensagens **REQ/REP** mediado por um **Broker**. Essa arquitetura permite que múltiplos clientes e múltiplos servidores operem simultaneamente sem que um conheça o endereço IP direto do outro, garantindo escalabilidade e desacoplamento.

## 3. Persistência de Dados
Conforme exigido, a persistência é feita de forma individual por cada servidor:
* Os dados são gravados em arquivos de texto (`.txt`) dentro do diretório `/data` de cada servidor.
* Utilizou-se **Volumes do Docker** para mapear as pastas internas dos containers (`/app/data`) para pastas locais no hospedeiro (`data_srv1` e `data_srv2`).
* Isso garante que, mesmo que os containers sejam removidos, o histórico de logins e canais criados permaneça salvo no disco.

## 4. Como Executar
Para subir todo o ecossistema (Broker, 2 Servidores e 2 Clientes), utilize o comando:
```bash
docker-compose up --build
```

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

# Projeto BBS/IRC Moderno - Parte 3

## 1. Introdução
A terceira etapa do projeto adiciona mecanismos de sincronização e controle de estado distribuído. Foram implementados Relógios Lógicos em todos os processos para garantir a ordenação dos eventos de forma unificada, além de um novo serviço de Referência (Coordenador) responsável por monitorar a disponibilidade dos servidores físicos na rede.

## 2. Escolhas Técnicas

### Relógio Lógico de Lamport
Para resolver a ordenação de eventos de forma distribuída, adotou-se o algoritmo de Lamport nos clientes (C++) e servidores (Python):
* O contador lógico é incrementado sempre antes do envio de qualquer requisição ou publicação.
* Ao receber uma mensagem, o processo extrai o relógio embutido no pacote e atualiza o seu próprio contador interno utilizando a lógica do maior valor recebido (`novo_relogio = max(relogio_local, relogio_recebido)`).

### Serviço de Referência (Coordenador)
Foi introduzido um novo nó na arquitetura (`referencia.py`), operando com sockets REQ/REP. Este atua como um registro centralizado que:
* Cadastra novos servidores na inicialização, atribuindo um Rank numérico.
* Mantém em memória e fornece a lista atualizada de servidores operantes.
* Fornece um timestamp físico de referência durante as validações de conectividade.

### Heartbeat e Manutenção da Lista
Para garantir a tolerância a falhas na listagem de servidores, adotou-se o envio de sinais periódicos (Heartbeats).
* Os servidores realizam uma requisição de heartbeat ao nó de Referência a cada 10 mensagens processadas.
* O nó de Referência possui uma rotina de monitorização que audita o tempo decorrido desde o último heartbeat de cada servidor. Caso a ausência de comunicação ultrapasse 15 segundos, o coordenador assume a inoperância do nó e remove-o da lista de servidores disponíveis.

## 3. Teste de Monitorização e Falhas
Para validar o funcionamento da deteção de falhas pelo processo de referência, foi estabelecido um procedimento de teste de inoperância intencional:
1. Com o ecossistema a operar normalmente, abra um segundo terminal no sistema hospedeiro.
2. Force o encerramento de um dos servidores em execução (neste caso, o Servidor 2) com o comando:
```bash
   docker stop servidor2
```
3. No terminal principal, o sistema continuará a processar as requisições ativas através do Servidor 1. Após cerca de 15 segundos sem receber heartbeats do nó interrompido, o container de Referência registará automaticamente a falha de comunicação e emitirá a notificação de remoção do servidor inativo da sua lista interna de controlo.

## 4. Como Executar
A inicialização requer a compilação do novo container de Referência e do código atualizado dos clientes/servidores. O comando permanece o mesmo:
```bash
docker-compose up --build
```
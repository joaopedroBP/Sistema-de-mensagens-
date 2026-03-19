# Projeto BBS/IRC Moderno - Parte 1

## 1. Introdução
Este projeto é a primeira etapa de um sistema de troca de mensagens distribuído, inspirado nos sistemas BBS e IRC. Esta versão inicial foca no processo de **Login**, **Criação de Canais** e **Listagem de Canais** utilizando containers Docker e comunicação via ZeroMQ.

## 2. Escolhas Técnicas

### Linguagens de Programação
*   **Servidor e Broker (Python):** A escolha pelo Python deve-se ao fato de ser a linguagem principal utilizada em aula, o que facilitou a implementação da lógica de persistência e do roteamento de mensagens (Broker).
*   **Cliente (C++):** O cliente foi desenvolvido em C++ por ser uma linguagem com a qual o desenvolvedor possui maior familiaridade e domínio.Utiliza-se a biblioteca `cppzmq` e o suporte nativo ao Protobuf para garantir a performance e a integração.

### Serialização (Protocol Buffers)
Inicialmente, foi considerada a utilização do *MessagePack*, porém, devido a dificuldades de implementação, optou-se pelo **Protobuf**. O Protobuf foi mais fácil de configurar para o projeto e se mostrou bem robusto para a comunicação entre os clientes e os servidores.
### Comunicação (ZeroMQ)
O projeto utiliza o padrão de mensagens **REQ/REP** mediado por um **Broker**. Essa arquitetura permite que múltiplos clientes e múltiplos servidores operem simultaneamente sem que um conheça o endereço IP direto do outro, garantindo escalabilidade e desacoplamento.

## 3. Persistência de Dados
Conforme exigido, a persistência é feita de forma individual por cada servidor:
*   Os dados são gravados em arquivos de texto (`.txt`) dentro do diretório `/data` de cada servidor.
*   Utilizou-se **Volumes do Docker** para mapear as pastas internas dos containers (`/app/data`) para pastas locais no hospedeiro (`data_srv1` e `data_srv2`).
*   Isso garante que, mesmo que os containers sejam removidos, o histórico de logins e canais criados permaneça salvo no disco.

## 4. Como Executar
Para subir todo o ecossistema (Broker, 2 Servidores e 2 Clientes), utilize o comando:
```bash
docker-compose up --build
```

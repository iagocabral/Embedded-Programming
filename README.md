# Embedded Programming Projects

Este repositório contém os projetos desenvolvido para sistemas embarcados 

## 🛠 Projetos

### 1. Controle de Estacionamento

Sistema distribuído para controle e monitoramento de estacionamentos comerciais. As principais funcionalidades incluem:

- Entrada e saída de veículos
- Monitoramento da ocupação das vagas
- Cobrança por tempo de permanência

**Execução:**

1. Servidor Central
2. Servidores Distribuídos (Térreo, Primeiro e Segundo andar)
3. Interface de controle manual

> [Link da Apresentação](https://youtu.be/C2OlpP-Yl9Q)

---

### 2. Controle de Elevadores com PID

Projeto de controle de elevadores usando um controlador **PID** e diversos sensores para:

- Controle da posição do elevador
- Monitoramento da temperatura ambiente com **BMP280**
- Comunicação UART com **ESP32**
- Atualização em **Display OLED**

**Principais Funcionalidades:**

- Mapeamento de andares
- Movimentação precisa do elevador com **PID**
- Exibição em OLED do estado do elevador e temperatura

> [Link da Apresentação](https://www.youtube.com/watch?v=lQIEO15wMr0)

**Execução:**

```bash
python3 src/main.py
```

### 3. Projeto Pomodoro com Monitoramento de Ambiente

Este projeto implementa o método Pomodoro, um sistema de gerenciamento de tempo que alterna períodos de foco e descanso. Além de atuar como um timer, o sistema também realiza monitoramento ambiental coletando informações de temperatura, umidade e nível de ruído no local. Quando ocorre a mudança entre o tempo de intervalo e o tempo de foco, ou vice-versa, uma campainha é acionada para notificar o usuário.

#### 1. Funcionalidades

##### 1.1 Método Pomodoro

O sistema realiza o gerenciamento do tempo com base no método Pomodoro, dividido em:

- **Tempo de Foco**: Período de trabalho intenso.
- **Tempo de Intervalo**: Período de descanso.

##### 1.2 Monitoramento de Temperatura e Umidadez

- Para monitorar a temperatura e umidade, foi utilizado um sensor DHT11 que recebe os valores e, através do protocolo MQTT, passa as informações para a Dashboard. Esse sensor tem a finalidade de monitorar a qualidade do ambiente de estudo.

##### 1.3 Monitoramento de Ruído

- O sensor KY-038 foi usado tanto na entrada digital quanto na analógica para medir os ruídos da sala de estudo. Há um gráfico para mostrar a variação e volume do ruído e um alerta caso ultrapasse o volume adequado.

##### 1.4 Notificações Sonoras

- Ao final de cada período de foco ou intervalo, o sistema aciona uma campainha, utilizando um buzzer, para notificar o usuário sobre a troca de modo. Isso ajuda a garantir que o usuário esteja ciente da mudança de atividades sem precisar monitorar ativamente o timer.

##### 1.5 Representação por RGB do Período

- Um LED RGB representa o período do Pomodoro, sendo vermelho para tempo de foco, verde para tempo de intervalo e azul para pausa.

##### 1.6 Ligar/Desligar o Pomodoro

- O botão de boot de uma das ESP32 funciona como botão para ligar/desligar o Pomodoro.

##### 1.7 Display

- Um display OLED exibe o tempo restante e o período atual.

##### 1.8 Botão Externo

- Um botão para pausar e despausar.

#### 2. Componentes Utilizados

- **ESP32**: Microcontrolador principal, responsável por realizar o timer do método Pomodoro e gerenciar os sensores.
- **Buzzer**: Dispositivo sonoro que notifica o usuário quando ocorre a mudança entre os períodos de foco e intervalo.
- **SSD1306 OLED**: Módulo display responsável pelo timer.
- **Botão**: Botão externo.
- **LED RGB**: LED para indicação visual do período.
- **Sensor DHT11**: Sensor para monitoramento de temperatura e umidade.
- **Sensor KY-038**: Sensor para monitoramento de ruído.

#### 3. Comunicação MQTT

A comunicação entre o ESP32 e o servidor ThingsBoard é feita via protocolo MQTT. A comunicação entre as ESP32 é feita via protocolo MQTT com um broker público (`mqtt://test.mosquitto.org`).

Os dados são enviados em formato JSON, e o ESP32 é capaz de receber comandos RPC.

#### 4. Modo Bateria (Deep Sleep)

O modo de bateria foi implementado na ESP32 com DHT11 e KY-038 e documentado no README da placa. [Clique aqui](https://github.com/FGA-FSE/trabalho-final-kishmotor-team/tree/main/esp32-dht-ky038) para ver a documentação completa e seu funcionamento.

##### Imagem das Boards

As imagens de cada configuração das protoboards estão em suas respectivas pastas.


| Nome    | Matricula |
|---------|-------|
| Guilherme Kishimoto   | 190088257    |
| Iago Cabral     | 190088745    |
- **Data..............** 04/08/2023
# Trabalho 2 (2024-1)

Este é o [Trabalho 2](https://gitlab.com/fse_fga/trabalhos-2024_1/trabalho-2-2024-1) da disciplina de Fundamentos de Sistemas Embarcados (FSE) da [UnB Gama - FGA](https://fga.unb.br/). 

<a name="top0"></a>
## Sumário
1. [Instruções](#top1)
2. [Implementação do controlador PID](#top2)
3. [Leitura da Temperatura Ambiente](#top3)
4. [Comunicação UART](#top4)
5. [Mostrador no OLED](#top5)



<br/>

## Apresentação em Vídeo

**Para assistir ao vídeo, clique no link a baixo:**<br>
[Vídeo no YouTube](https://youtu.be/lQIEO15wMr0)
<br/>

<img align="center" alt="Raspverry Pi" height="40" width="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/raspberrypi/raspberrypi-original.svg"><img align="center" alt="Python" height="40" width="40" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">


<a name="top1"></a>
## 1. Instruções
### Dependências
```bash
Python3
Pip 
Bmp280
i2cdevice
RPi.GPIO 
Smbus
Adafruit
```
Para instalar:
```bash
$ pip install RPi.GPIO
$ pip install smbus
$ pip3 install adafruit-blinka
$ pip3 install adafruit-circuitpython-ssd1306
$ pip3 install bmp280
  ```

### Executando
Para executar, clone o repositório e transfira a pasta `src` para uma das Raspberry.
 
Na raiz do projeto execute o seguinte comando:

```bash
$ python3 src/main.py
```
<br/>

```
1. Inicialmente, o programa realizará a subida do elevador até alcançar o valor maximo no encoder e mapear o endereço do Terreo, 1, 2 e 3 andar;
2. Em seguida, ele iniciará a descida;
3. Após essa verificação, o programa executará a lógica necessária para direcionar o elevador aos andares desejados, de acordo com os botões selecionados na board;
4. Durante todo o processo, a atualização no visor OLED será realizada, exibindo informações como o estado do elevador e a temperatura ambiente.
```

<br/>

[(Sumário - voltar ao topo)](#top0)
<br/>




<a name="top2"></a>
## 2. Implementação do controlador PID
- A implementação do controlador PID visa proporcionar um controle preciso e eficiente do elevador, permitindo que ele se mova de forma suave e precisa entre diferentes andares. 

### 2.1. Entendendo a Implementação do Codigo:

#### main.py:
```
- Inicia configurando o logger e importando os módulos necessários, incluindo `pid`, `gpio`, `uart`, `cmds`, e `global_config`.
- Cria instâncias dos controladores PID (`pid_control1` e `pid_control2`) e configura suas constantes de ganho (Kp, Ki, Kd).
- Inicializa os controladores GPIO (`gc.controle1` e `gc.controle2`) e configura o PWM global.
- Define o tratamento de sinais para finalizar o programa de forma segura ao receber sinais de interrupção (`SIGINT` e `SIGTERM`).
- Abre a comunicação UART e inicia o processo de leitura dos botões em threads.
- Calibra os elevadores e inicia os controladores.
- Inicia os threads de leitura dos botões e configura o tratamento de sinais.
- No bloco `finally`, garante que o PWM e os controladores sejam parados corretamente e encerra a comunicação UART e os threads de leitura dos botões.
```

#### gpio.py:
```
- Importa os módulos necessários, incluindo `RPi.GPIO`, `logging`, `pid`, `cmds`, `global_config`, `uart`, e `oled`.
- Define a classe `GPIOController` para gerenciar o controle dos pinos GPIO e a lógica do elevador.
- No método `__init__`, configura os pinos GPIO para o elevador com base no `elevador_id`, define o PWM, e inicializa os eventos e variáveis.
- O método `start` inicia uma thread para processar os pedidos do elevador.
- O método `stop` encerra a thread de processamento de pedidos e limpa os eventos.
- O método `add_request` adiciona um pedido de andar à lista de solicitações, se não estiver já presente.
- O método `process_requests` processa os pedidos de andar e move o elevador até o andar solicitado.
- O método `monitorar_sensores` monitora os sensores até que o evento seja ativado.
- O método `calibrar_elevador` calibra o elevador, ajustando os valores dos sensores e do encoder.
- O método `start_pwm` inicia o PWM e o método `stop_pwm` o para.
- O método `definir_potencia_motor` ajusta a potência do motor com base na porcentagem fornecida.
- O método `aciona_motor` controla a direção e a potência do motor, e atualiza o status do elevador no display OLED.
- O método `ir_para_andar` usa o controlador PID para mover o elevador até o andar solicitado e ajusta a potência do motor conforme necessário.
- O método `verificar_sensores` retorna o estado dos sensores do elevador.
```

#### pid.py:
```
- O módulo `pid` contém a classe `PID`, responsável por implementar o controlador PID.
- O método `controle` é fundamental, calculando o sinal de controle com base nos erros proporcional, integral e derivativo.
- Os ganhos (Kp, Ki, Kd) e a referência são ajustados dinamicamente durante a execução.
```

### 2.2. Exemplo de Funcionamento:
```
- No main.py, o elevador sobre até o terceiro andar e, em seguida, reconhecendo os andares e desce para o terreo
- Em seguida, move-se para o andar desejado, utilizando o PID para controlar a movimentação.
```


[(Sumário - voltar ao topo)](#top0)
<br/>
<a name="top3"></a>
## 3. Leitura da Temperatura Ambiente
A obtenção da temperatura ambiente é crucial para monitorar as condições internas do elevador. Utilizando a i2c_bmp280.py. Abaixo esta a implementação correspondente:

Arquivo **`i2c_bmp280.py`**:
```bash
- Importa os módulos necessários, incluindo `smbus2`, `BMP280` do módulo `bmp280`, e `sleep` do módulo `time`.
- Inicializa o barramento I2C usando `smbus2.SMBus(1)`.
- Tenta inicializar dois sensores BMP280 com endereços I2C 0x76 e 0x77. Se não conseguir encontrar um sensor em um endereço, captura a exceção e define o sensor como `None`.
- Define a função `temp_ambiente` que retorna a temperatura medida pelo sensor BMP280 correspondente ao `elevador` especificado (0 ou 1). Se o sensor não estiver disponível ou o ID do elevador for inválido, lança uma exceção apropriada.
- Realiza um teste básico, imprimindo a temperatura dos dois elevadores e lidando com exceções se os sensores não estiverem disponíveis.
```


Arquivo **`cmds.py`**:
```bash
- Importa os módulos necessários, incluindo `logging`, `uart`, `gpio`, `i2c_bmp280`, `oled`, `struct`, `sleep` do módulo `time`, e `global_config`.

- **Variáveis Globais:**
  - `cod`: Endereço da ESP32.
  - `id`: Matrícula usada nas mensagens.

- **Funções:**
  - `le_encoder(id_motor)`: Cria uma mensagem para leitura do encoder.
  - `envia_pwm(id_motor, pwm_value)`: Cria uma mensagem para enviar o valor PWM ao motor.
  - `envia_temp(id_motor, temperatura)`: Cria uma mensagem para enviar a temperatura ao motor.
  - `le_btn(addr)`: Cria uma mensagem para ler o estado do botão no endereço especificado.
  - `escr_btn(addr, value)`: Cria uma mensagem para escrever o estado do botão no endereço especificado.

- **Funções de Controle do Elevador:**
  - `menu_elevador(controle, exit_event)`: Controle do elevador com leitura do encoder, reconhecimento de andares, e movimentação entre andares com logs para depuração.
  - `apurar_lcd(controle0, controle1, exit_event)`: Mede e envia a temperatura para os elevadores e atualiza o display OLED com a temperatura medida.
  - `apurar_encoder(id_motor)`: Envia uma mensagem para ler o valor do encoder e retorna o valor lido.
  - `apurar_pwm(id_motor, pwm_global)`: Envia uma mensagem para apurar o valor do PWM do motor.
  - `apurar_temp(id_motor)`: Mede a temperatura e envia a temperatura para o motor.
  - `apagar_botao(endereco)`: Apaga o botão no endereço especificado.
  - `le_regs()`: Lê o estado dos botões nos endereços de 0x00 a 0x0A e imprime o estado.
  - `escr_regs_off()`: Desativa todos os botões nos endereços de 0x00 a 0x0A.
  - `escr_regs_on()`: Ativa todos os botões nos endereços de 0x00 a 0x0A.

- **Tratamento de Erros:**
  - Exceções são capturadas e registradas para fornecer informações detalhadas em caso de falhas durante as operações.
```

[(Sumário - voltar ao topo)](#top0)
<br/>
<a name="top4"></a>
## 4. Comunicação UART
O módulo UART é fundamental para a comunicação no projeto, utilizando a validação do CRC. Abaixo estão os trechos de código mais relevantes:

Arquivo **`uart.py`**:
```bash
- **Importações e Configuração:**
  - Importa módulos como `os`, `termios`, `time`, `struct`, `logging`, `crc`, e `global_config`.
  - Configura o logging para exibir mensagens de depuração e erro.

- **Constantes:**
  - `ADDRESS`, `SEND`, `REQUEST`, `S_TEMP_AMB`, `R_TEMP_I`, `R_BOTOES`: Códigos e endereços usados na comunicação UART.

- **Eventos:**
  - `button_states_internal`, `button_states_external`: Armazenam o estado dos botões internos e externos.
  - `priority_event`, `stop_event`, `encoder_event`, `uart_in_use_event`, `registradores_event`: Eventos para controle e sincronização de threads.

- **Funções:**
  - `validacao(codes, crc)`: Valida o CRC dos códigos.
  - `open_uart()`: Abre e configura a conexão UART.
  - `read_uart(size)`: Lê dados da UART com um tamanho específico e retorna os dados lidos.
  - `send_request(payload, response_size)`: Envia uma requisição UART com CRC e lê a resposta.
  - `solicitar_valor_encoder(id_motor)`: Solicita o valor do encoder para um motor específico.
  - `read_encoder_value(response)`: Lê e interpreta o valor do encoder da resposta.
  - `enviar_temp_ambiente(id_elevator, temperatura)`: Envia a temperatura ambiente para um elevador específico.
  - `ler_registradores(endereco_inicial, quantidade)`: Lê os registradores dos botões a partir de um endereço inicial.
  - `read_registradores_botoes(response, quantidade)`: Lê e interpreta os valores dos botões a partir da resposta.
  - `read_buttons_continuously(...)`: Lê continuamente o estado dos botões e adiciona solicitações baseadas no estado dos botões.
  - `start_button_reading_threads()`: Inicia threads para leitura contínua dos botões.
  - `stop_button_reading_threads(button_threads)`: Para as threads de leitura de botões e aguarda sua conclusão.
  - `close_uart()`: Fecha a conexão UART.

- **Tratamento de Erros:**
  - Exceções são capturadas e registradas para ajudar na depuração e identificar problemas na comunicação UART.

```

[(Sumário - voltar ao topo)](#top0)
<br/>
<a name="top5"></a>
## 5. Mostrador no OLED
No arquivo **`cmds.py`**, a função apurar_lcd() utiliza as funções do arquivo **`oled.py`** para exibir informações relevantes no oled, como o estatos do elevador e a temperatura ambiente.<br>
Arquivo **`oled.py`**:
```bash
- **Importações:**
  - Importa módulos do `board`, `busio`, `adafruit_ssd1306`, e `PIL` para controlar o display OLED.

- **Variáveis Globais:**
  - `stats1`, `stats2`: Status dos elevadores 1 e 2.
  - `temp1`, `temp2`: Temperaturas dos elevadores 1 e 2.

- **Funções:**
  - `up_temp(temperatura1, temperatura2)`: Atualiza as temperaturas exibidas no display OLED.
    - Atualiza as variáveis globais `temp1` e `temp2`.
    - Chama `show_display()` para atualizar o display.
  
  - `up_status(status1, elevador)`: Atualiza o status do elevador exibido no display OLED.
    - Atualiza a variável global `stats1` ou `stats2` dependendo do identificador do elevador (`elevador`).
    - Chama `show_display()` para atualizar o display.

  - `show_display()`: Exibe as informações no display OLED.
    - Inicializa a comunicação I2C e o display SSD1306.
    - Cria uma nova imagem em preto e branco para desenhar no display.
    - Desenha o texto no display com informações sobre os elevadores e suas temperaturas.
    - Atualiza o display para mostrar a imagem desenhada.

- **Uso de Recursos:**
  - Utiliza o módulo `busio` para comunicação I2C.
  - Utiliza o módulo `adafruit_ssd1306` para controlar o display OLED.
  - Usa `PIL` para criar e desenhar na imagem exibida.
```

[(Sumário - voltar ao topo)](#top0)
<br/>
<a name="top6"></a>

# Display
### Introdução
Essa partição do projeto é responsavel pelo controle do periodo do pomodoro, o tempo restante e a exibição no display.

### Recebe 

Recebe via MQTT o estado do botão de Power, disponibilizado pela [esp32-display](https://github.com/FGA-FSE/trabalho-final-kishmotor-team/tree/main/esp32-display), responsavel por ligar o display. 

### Envia

Envia via MQTT o periodo do metodo pomodoro, sendo 0 para pausa, 1 para foco e 2 para intervalo, alem de enviar o tempo restante de cada momento. 
### Dispositivos

* **ESP32** - Microcontrolador principal, responsável por realizar o timer do método Pomodoro e gerenciar os sensores.
* **Ssd1306 Lcd Arduino Pic** - Tela oled responsavel pela exibição do tempo restante e do periodo atual. 
* **Botão** - Botão externo, responsavel pelo controle de pausa e continuação do metodo.

### Conjunto 

![Foto da Board](https://media.discordapp.net/attachments/1278505631413829737/1281064838264655944/esp.png?ex=66da5c1a&is=66d90a9a&hm=ff2e32aa101c55339e320ca56a2ac5e77c2bda0e91239adc3d1a5f34fac9ec36&=&format=webp&quality=lossless)

import logging
import uart
import gpio
import i2c_bmp280
import oled
import struct
from time import sleep
import global_config

cod = [0x01]  # Endereço da ESP32
id = [8, 2, 5, 7]  # Matrícula

# Mensagens
def le_encoder(id_motor):
    # Mensagem para leitura do encoder
    return [0x01, 0x23, 0xC1, id_motor, 8, 2, 5, 7]

def envia_pwm(id_motor, pwm_value):
    # Mensagem para enviar PWM
    return [cod[0], 0x16, 0xC2, id_motor, *struct.pack("<i", pwm_value), *id]

def envia_temp(id_motor, temperatura):
    # Mensagem para enviar temperatura
    return [cod[0], 0x16, 0xD1, id_motor, temperatura, *id]

def le_btn(addr):
    # Mensagem para ler botão
    return [cod[0], 0x03, addr, 1, *id]

def escr_btn(addr, value):
    # Mensagem para escrever botão
    return [cod[0], 0x06, addr, 1, value, *id]

def menu_elevador(controle, exit_event):
    try:
        while not exit_event.is_set():
            logging.info('Descendo o elevador...')
            controle.desce_tudo()
            
            valor_encoder = apurar_encoder(controle.id)
            if valor_encoder is None:
                logging.error(f'Falha ao ler o valor do encoder para o motor {controle.id}')
                return 

            logging.info(f'Valor do encoder para motor {controle.id}: {valor_encoder}')

            logging.debug(f"Estado do objeto controle: {controle.__dict__}")

            logging.info('Reconhecendo andares...')
            controle.reconhece_andares()

            logging.info('Andares reconhecidos')

            logging.info('Indo para 1o Andar')
            controle.ir_para_andar(1)
            logging.info('Parou 1o Andar')
            sleep(5)

            logging.info('Indo para Terreo')
            controle.ir_para_andar(0)
            logging.info('Parou Terreo')
            sleep(5)
    except TypeError as e:
        logging.error(f"Exceção do tipo TypeError na função menu_elevador: {e}")
    except Exception as e:
        logging.error(f"Exceção na função menu_elevador: {e}")

def apurar_lcd(controle0, controle1, exit_event):
    try:
        global_config.temperature = i2c_bmp280.temp_ambiente(controle0)
        lcd_temp = round(global_config.temperature, 1)
        logging.debug(f"Temperatura medida para elevador {controle0}: {lcd_temp}°C")
        global_config.temperature1 = i2c_bmp280.temp_ambiente(controle1)
        lcd_temp = round(global_config.temperature1, 1)
        logging.debug(f"Temperatura medida para elevador {controle1}: {lcd_temp}°C")

        # uart.priority_event.set()
        uart.enviar_temp_ambiente(0x00, global_config.temperature)
        logging.debug(f"Enviou temperatura: {global_config.temperature} para elevador {controle0}")
        uart.enviar_temp_ambiente(0x01, global_config.temperature1)
        logging.debug(f"Enviou temperatura: {global_config.temperature1} para elevador {controle1}")
        # uart.priority_event.clear()
        oled.up_temp("{:05.2f}C".format(global_config.temperature), "{:05.2f}C".format(global_config.temperature1))
    except Exception as e:
        logging.error(f"Exceção na função apurar_lcd: {e}")


def apurar_encoder(id_motor):
    try:
        mensagem = le_encoder(id_motor)
        uart.encoder_event.set()
        response = uart.send_request(bytearray(mensagem), 9)
        if response:
            valor = struct.unpack("<i", response[3:7])[0]
            logging.debug(f"Valor do encoder recebido: {valor}")
            return valor
        else:
            logging.error("Erro ao apurar encoder.")
            return None
    except Exception as e:
        logging.error(f"Exceção na função apurar_encoder: {e}")
        return None

def apurar_pwm(id_motor, pwm_global):
    try:
        mensagem = envia_pwm(id_motor, pwm_global[id_motor])
        response = uart.send_request(bytearray(mensagem), len(mensagem) + 2) 
        return response
    except Exception as e:
        logging.error(f"Erro ao apurar PWM: {e}")
        return None

def apurar_temp(id_motor):
    temperatura = i2c_bmp280.temp_ambiente(id_motor)
    mensagem = envia_temp(id_motor, temperatura)
    valor_temp = uart.envia_recebe(global_config.uart_file, mensagem)
    if valor_temp:
        return valor_temp
    else:
        logging.error("Erro ao apurar temperatura.")
        return None

def apagar_botao(endereco):
    mensagem = escr_btn(endereco, 0)
    try:
        response = uart.send_request(bytearray(mensagem), len(mensagem) + 2)  # Adiciona 2 bytes para CRC
        return response
    except Exception as e:
        logging.error(f"Erro ao apagar botão: {e}")
        return None

def le_regs():
    while True:
        for addr in range(0x00, 0x0B):
            btn_state = uart.envia_recebe(global_config.uart_file, le_btn(addr))
        sleep(0.1)

def escr_regs_off():
    for addr in range(0x00, 0x0B):
        uart.envia_recebe(global_config.uart_file, escr_btn(addr, 0))

def escr_regs_on():
    for addr in range(0x00, 0x0B):
        uart.envia_recebe(global_config.uart_file, escr_btn(addr, 1))

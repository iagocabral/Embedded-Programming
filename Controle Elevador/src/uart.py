import os
import termios
import time
import struct
import logging
from crc import calculate_CRC
import global_config
from threading import Thread, Event

# Configuração de logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

ADDRESS = 0x01
SEND = 0x16
REQUEST = 0x23
S_TEMP_AMB = 0xD1
R_TEMP_I = 0xC1
R_BOTOES = 0x03

button_states_internal = [None, None]
button_states_external = [None, None]
priority_event = Event()
stop_event = Event()
encoder_event = Event()
uart_in_use_event = Event()
registradores_event = Event()


def validacao(codes, crc):
    res_crc = calculate_CRC(codes)
    if res_crc == crc:
        logging.debug("CRC válido")
        return True
    else:
        logging.debug("CRC inválido")
        logging.warning("Erro de comunicação")
        return False

def open_uart():
    try:
        global_config.uart_file = os.open("/dev/serial0", os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
        
        attrs = termios.tcgetattr(global_config.uart_file)
        
        attrs[0] = termios.IGNPAR
        attrs[1] = 0
        attrs[2] = termios.B115200 | termios.CS8 | termios.CLOCAL | termios.CREAD
        attrs[3] = 0
        
        termios.tcflush(global_config.uart_file, termios.TCIFLUSH)
        termios.tcsetattr(global_config.uart_file, termios.TCSANOW, attrs)
        logging.info("Conexão UART estabelecida")
        time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao abrir a conexão UART: {e}")
        exit(1)

def read_uart(size):
    buffer = b''
    attempts = 20
    total_bytes_read = 0
    while total_bytes_read < size and attempts > 0:
        try:
            chunk = os.read(global_config.uart_file, size - total_bytes_read)
            if chunk:
                buffer += chunk
                total_bytes_read += len(chunk)
                logging.debug(f"Chunk received: {chunk.hex()} ({chunk}), Total bytes read: {total_bytes_read}")
            else:
                logging.debug("No data received, sleeping for 0.5 seconds...")
                time.sleep(0.5)
        except BlockingIOError:
            logging.debug("BlockingIOError encountered, sleeping for 0.5 seconds...")
            time.sleep(0.5)
        attempts -= 1
    if total_bytes_read < size:
        logging.warning(f"Timeout reading from UART after {20 - attempts} attempts")
    return buffer

def send_request(payload, response_size):
    if not uart_in_use_event.wait(timeout=5):
            logging.error("Timeout ao tentar adquirir uart_in_use_event no método send_request")
            return None
    uart_in_use_event.clear()
    try:
        logging.debug(f"Payload before CRC: {payload.hex()}")
        crc = calculate_CRC(payload)
        crc_bytes = struct.pack('<H', crc)
        logging.debug(f"Calculated CRC: {crc} (bytes: {crc_bytes.hex()})")
        payload += crc_bytes
        logging.debug(f"Payload with CRC: {payload.hex()}")

        try:
            written = os.write(global_config.uart_file, payload)
            logging.debug(f"Bytes enviados: {written}")
        except OSError as e:
            logging.error(f"OSError ao escrever na UART: {e}")
            uart_in_use_event.set()
            return None

        time.sleep(1)

        response = read_uart(response_size)
        logging.debug(f"Resposta recebida: {response.hex()}")

        #Verifica CRC
        if len(response) >= 2:
            received_crc = struct.unpack('<H', response[-2:])[0]
            calculated_crc = calculate_CRC(response[:-2])
            logging.debug(f"Received CRC: {received_crc:04x}, Calculated CRC: {calculated_crc:04x}")
            if received_crc == calculated_crc:
                logging.info("CRC verificado com sucesso!")
            else:
                logging.error(f"CRC incorreto: recebido {received_crc:04x}, esperado {calculated_crc:04x}")
        else:
            logging.error("Resposta recebida é muito curta para conter CRC válido.")

        uart_in_use_event.set()
        return response
    except Exception as e:
        logging.error(f"Erro ao adquirir uart_lock no método send_request: {e}")
        return None

def solicitar_valor_encoder(id_motor):
    termios.tcflush(global_config.uart_file, termios.TCIFLUSH)
    buffer = bytearray()
    buffer.append(ADDRESS)
    buffer.append(REQUEST)
    buffer.append(R_TEMP_I)
    buffer.append(id_motor)
    for digito in "8257":
        buffer.append(int(digito))
    
    logging.debug(f"Encoder Request payload: {buffer.hex()}")
    return send_request(buffer, 9)

def read_encoder_value(response):
    if len(response) < 9:
        logging.error("Resposta muito curta para conter valor válido do encoder.")
        return None
    try:
        valor_encoder = struct.unpack("<i", response[3:7])[0]
        logging.debug(f"Valor do encoder recebido: {valor_encoder}")
        return valor_encoder
    except struct.error as e:
        logging.error(f"Erro ao descompactar a resposta do encoder: {e}")
        return None

def enviar_temp_ambiente(id_elevator, temperatura):
    termios.tcflush(global_config.uart_file, termios.TCIFLUSH)
    buffer = bytearray()
    
    buffer.append(ADDRESS)
    buffer.append(SEND)
    buffer.append(S_TEMP_AMB)
    buffer.append(id_elevator)
    buffer.extend(struct.pack('<f', temperatura))
    # buffer.append(temperatura)
    logging.debug(f"ELEVADOR ID {id_elevator}")
    
    for digito in "8257":
        buffer.append(int(digito))
    
    logging.debug(f"TEMPERATURA payload: {buffer.hex()}")
    return send_request(buffer, 5)

def ler_registradores(endereco_inicial, quantidade):
    termios.tcflush(global_config.uart_file, termios.TCIFLUSH)
    buffer = bytearray()
    buffer.append(ADDRESS)
    buffer.append(R_BOTOES)
    buffer.append(endereco_inicial)
    buffer.append(quantidade)
    for digito in "8257":
        buffer.append(int(digito))

    logging.debug(f"Leitura dos botões payload: {buffer.hex()}")
    return send_request(buffer, 5 + 2 * quantidade)

def read_registradores_botoes(response, quantidade):
    if len(response) <  quantidade + 2:
        logging.error("Resposta muito curta para conter os valores dos registradores.")
        return None
    try:
        botoes = struct.unpack(f'>{quantidade}B', response[2:2 + quantidade])
        logging.debug(f"Valores dos registradores dos botões recebidos: {botoes}")
        return botoes
    except struct.error as e:
        logging.error(f"Erro ao descompactar a resposta dos registradores dos botões: {e}")
        return None
    
def read_buttons_continuously(elevator_id, endereco_inicial, quantidade, button_type, elevator_id1, endereco_inicial1, quantidade1, button_type1):
    global button_states_internal, button_states_external
    endereco_mapping_elevador0 = [
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A
    ]
    endereco_mapping_elevador1 = [
        0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA
    ]

    while True:
        if priority_event.is_set() or encoder_event.is_set():
            time.sleep(0.1)
            continue

        response = ler_registradores(endereco_inicial, quantidade)
        if response:
            botoes = read_registradores_botoes(response, quantidade)
            if button_type == 'internal':
                endereco_mapping = endereco_mapping_elevador0 
                button_states_internal[elevator_id] = botoes
                for i, estado in enumerate(botoes):
                    if estado == 1:
                        endereco = endereco_mapping[i]
                        global_config.controle1.add_request(endereco) if elevator_id == 0 else global_config.controle2.add_request(endereco)
            else:
                endereco_mapping = endereco_mapping_elevador0 
                button_states_external[elevator_id] = botoes
                for i, estado in enumerate(botoes):
                    if estado == 1:
                        endereco = endereco_mapping[i]
                        global_config.controle1.add_request(endereco) if elevator_id == 0 else global_config.controle2.add_request(endereco)
        time.sleep(0.5)

        if priority_event.is_set() or encoder_event.is_set():
            time.sleep(0.1)
            continue
        
        response1 = ler_registradores(endereco_inicial1, quantidade1)
        if response1:
            botoes = read_registradores_botoes(response1, quantidade1)
            if button_type == 'internal':
                endereco_mapping = endereco_mapping_elevador1
                button_states_internal[elevator_id1] = botoes
                for i, estado in enumerate(botoes):
                    if estado == 1:
                        endereco = endereco_mapping[i]
                        global_config.controle1.add_request(endereco) if elevator_id1 == 0 else global_config.controle2.add_request(endereco)
            else:
                endereco_mapping = endereco_mapping_elevador1
                button_states_external[elevator_id1] = botoes
                for i, estado in enumerate(botoes):
                    if estado == 1:
                        endereco = endereco_mapping[i]
                        global_config.controle1.add_request(endereco) if elevator_id1 == 0 else global_config.controle2.add_request(endereco)
        time.sleep(0.5)

def start_button_reading_threads():
    global stop_event
    stop_event.clear()
    
    button_threads = []
    enderecos_iniciais = {
        'internal': [0x06, 0xA6],
        'external': [0x00, 0xA0]
    }
    
    read_buttons_continuously(0, enderecos_iniciais['external'][0], 11, 'external', 1, enderecos_iniciais['external'][1], 11, 'external')
    
    return button_threads

def stop_button_reading_threads(button_threads):
    global stop_event
    stop_event.set()
    for thread in button_threads:
        thread.join()

def close_uart():
    if global_config.uart_file:
        os.close(global_config.uart_file)
        logging.info("Conexão UART fechada")

# if __name__ == "__main__":
#     open_uart()

#     response = enviar_temp_ambiente(0x00, 23.543698115854568)
#     logging.debug(f"Final response: {response}")

#     close_uart()

# if __name__ == "__main__":
#     open_uart()

#     # Testar solicitação de valor do encoder
#     id_motor = 0x01  # Substitua pelo ID do motor correto
#     valor_encoder = solicitar_valor_encoder(id_motor)
#     if valor_encoder is not None:
#         logging.info(f"Valor do encoder para motor {id_motor}: {valor_encoder}")
#     else:
#         logging.error(f"Falha ao ler o valor do encoder para motor {id_motor}")

#     os.close(global_config.uart_file)

# if __name__ == "__main__":
#     open_uart()

#     id_motor = 0x01
#     response = solicitar_valor_encoder(id_motor)
#     if response:
#         valor_encoder = read_encoder_value(response)
#         if valor_encoder is not None:
#             logging.info(f"Valor do encoder para motor {id_motor}: {valor_encoder}")

#     close_uart()


# if __name__ == "__main__":
#     open_uart()
    
#     # Testar leitura dos registradores dos botões com endereço inicial em hexadecimal
#     endereco_inicial = 0xA1  # Substitua pelo endereço inicial desejado
#     quantidade = 2          # Substitua pela quantidade de bytes desejada
#     response = ler_registradores(endereco_inicial, quantidade)
#     if response:
#         botoes = read_registradores_botoes(response, quantidade)
#         if botoes is not None:
#             for i, estado in enumerate(botoes):
#                 print(f"Botão {i + 1}: {'Pressionado' if estado else 'Liberado'}")
#         else:
#             logging.error("Falha ao ler os estados dos botões.")
#     else:
#         logging.error("Falha ao solicitar leitura dos registradores dos botões.")
    
    
#     close_uart()
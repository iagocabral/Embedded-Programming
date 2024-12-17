from gpiozero import LED, Button
import sys
from time import sleep
from datetime import datetime
import threading
from server_distribuidos.models.car import Car
import json
from server_distribuidos.server_client_terreo import send_data, enviar_carro_para_servidor, request_car_info, update_car_info, request_remove_car, listen_for_updates, request_status_lotacao_A, request_status_lotacao_B, request_status_lotacao_A_v, request_status_lotacao_B_v


endereco_01 = LED(22)
endereco_02 = LED(26)
endereco_03 = LED(19)
sensor_de_vaga = Button(18)
sinal_de_lotado_fechado = LED(27)
sensor_abertura_cancela_entrada = Button(23)
sensor_fechamento_cancela_entrada = Button(24)
motor_cancela_entrada = LED(10)
sensor_abertura_cancela_saida = Button(25)
sensor_fechamento_cancela_saida = Button(12)
motor_cancela_saida = LED(17)

estados_vagas = [True] * 8
tem_vaga = [True] * 8
estacionamento_lotado = False
cancela_precionada = 0
comeco = 0
comeca_verificar = 0
car_creation_lock = threading.Lock()

def monitorar_vagas():
    global estados_vagas
    global comeco

    while True:
        for vaga_id in range(8):
            estado_binario = format(vaga_id, '03b')
            endereco_01.value = int(estado_binario[2])
            endereco_02.value = int(estado_binario[1])
            endereco_03.value = int(estado_binario[0])
            sleep(0.1)

            comeco += 1
            
            estado_atual = sensor_de_vaga.is_pressed
            if estado_atual != estados_vagas[vaga_id]:
                estados_vagas[vaga_id] = estado_atual
                processar_mudanca_vaga(vaga_id, estado_atual)
        sleep(0.5)

def processar_mudanca_vaga(vaga_id, estado):
    global estados_vagas
    global tem_vaga
    global estacionamento_lotado
    global message
    global cancela_precionada
    global comeco

    tipo = 'disabled' if vaga_id == 0 else 'elderly' if vaga_id in [1, 2] else 'regular'
    vaga_num = vaga_id + 1
    estado_str = "ocupada" if not estado else "livre"
    if estado_str == "livre" and comeco > 8:
        tem_vaga[vaga_id] = True
        estacionamento_lotado = False
        controlar_saida(vaga_num)
        sleep(1)
        controlar_entrada()
        
    elif estado_str == "ocupada":
        vaga_info = {'tipo': tipo, 'D': 0}
        car = request_car_info('localhost', 10400, vaga_info)
        vaga_info = {'tipo': tipo, 'T': vaga_num}
        car['dados']['vaga'] = vaga_info
        car['dados']['vaga_num'] = vaga_num
        update_car_info('localhost', 10400, car)
        tem_vaga[vaga_id] = False

    request_status_lotacao_A('localhost', 10400)
    # request_status_lotacao_B('localhost', 10400)
    print(f"Vaga {tipo} T{vaga_num} {estado_str}.")

def monitorar_lotacao():
    global estacionamento_lotado
    global tem_vaga
    global comeca_verificar

    while True:
        lotado_A = request_status_lotacao_A_v('localhost', 10400)
        lotado_B = request_status_lotacao_B_v('localhost', 10400)
        
        if sinal_de_lotado_fechado.is_lit or (all(not vaga for vaga in tem_vaga) and lotado_A and lotado_B):
            sinal_de_lotado_fechado.on()
            print("Estacionamento lotado ou fechado.")
            estacionamento_lotado = True
            comeca_verificar = 0
            while comeca_verificar == 0:
                lotado_A = request_status_lotacao_A_v('localhost', 10400)
                lotado_B = request_status_lotacao_B_v('localhost', 10400)
                if not sensor_abertura_cancela_saida.is_pressed or not lotado_A or not lotado_B:
                    sinal_de_lotado_fechado.off()
                    estacionamento_lotado = False
                    comeca_verificar = 1
                sleep(0.1)
        sleep(1)

def terreo_fechar_estacionamento():
    sinal_de_lotado_fechado.on()

def terreo_abrir_estacionamento():
    global comeca_verificar
    comeca_verificar = 1
    sinal_de_lotado_fechado.off()

def criar_carro():
    with car_creation_lock:
        vaga_info = {'tipo': 'default', 'D': 0}
        car = Car(vaga_info, 0)
        enviar_carro_para_servidor(car, 'localhost', 10400)

        return car

def controlar_entrada():
    global estacionamento_lotado
    global cancela_precionada
    global tem_vaga

    if not sensor_abertura_cancela_entrada.is_pressed and estacionamento_lotado == False:
        motor_cancela_entrada.on()
        cancela_precionada = 1
        car = criar_carro()
        sleep(1.5)
        motor_cancela_entrada.off()
        return car
    
    elif not sensor_abertura_cancela_entrada.is_pressed and estacionamento_lotado == True:
        print("Estacionamento lotado ou fechado!")
        message_fila_entrada = 'Estacionamento lotado ou fechado!'
        send_data('localhost', 10400, to_json_fila_entrada(message_fila_entrada))
        while estacionamento_lotado:
            if not sensor_abertura_cancela_saida.is_pressed:
                for index, vaga in enumerate(tem_vaga):
                    if vaga:
                        numero_vaga = index + 1
                        controlar_saida(numero_vaga)

                estacionamento_lotado = False
            sleep(0.1)

def controlar_saida(vaga_num):
    global cancela_precionada
    if isinstance(vaga_num, int):
        tipo = 'disabled' if vaga_num == 1 else 'elderly' if vaga_num in [2, 3] else 'regular'
        vaga_info = {'tipo': tipo, 'T': vaga_num}
        motor_cancela_saida.on()
        remover_carro_por_vaga(vaga_info, vaga_num)
        sleep(1.5)
        motor_cancela_saida.off()
    else:
        while True:
            if not sensor_abertura_cancela_saida.is_pressed:
                motor_cancela_saida.on()
                sleep(1.5)
                motor_cancela_saida.off()
            break

def remover_carro_por_vaga(vaga_info, vaga_num):
    car = request_car_info('localhost', 10400, vaga_info)
    if (('T' in vaga_info) and (car['dados']['vaga_num'] == vaga_num)):
        atualizar_current_charge(car)
        send = car['dados']['id']
        car['dados']['current_charge']
        request_remove_car('localhost', 10400, send)
        sleep(0.5)

def atualizar_current_charge(car_data):
    entry_time = datetime.fromisoformat(car_data['dados']['entry_time'])
    duration = datetime.now() - entry_time
    minutes_parked = duration.total_seconds() / 60
    rate_per_minute = 0.10
    car_data['dados']['current_charge'] = round(minutes_parked * rate_per_minute, 3)

def to_json_entrada(car):
        return {
            'tipo': 'message',
            'dados': {
                'carro id': car['dados']['id'],
                'entry_time': car['dados']['entry_time']
            }
        }

def to_json_saida(car):
        return json.dumps({
            'carro id': car.id,
            'vaga': car.vaga,
            'current_charge': car.calculate_current_charge()
        }, indent=4)

def to_json_fila_entrada(message):
    return json.dumps({
        'tipo': 'message',
        'dados': message
    }, indent=4)

def to_json_message(message):
    return {
        'tipo': 'message',
        'dados': message
    }

sensor_abertura_cancela_entrada.when_released = controlar_entrada
sensor_abertura_cancela_saida.when_released = controlar_saida

if __name__ == "__main__":
    thread_monitoramento = threading.Thread(target=monitorar_vagas, daemon=True)
    thread_lotacao = threading.Thread(target=monitorar_lotacao, daemon=True)

    thread_monitoramento.start()
    thread_lotacao.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Programa encerrado.")
        sys.exit(0)

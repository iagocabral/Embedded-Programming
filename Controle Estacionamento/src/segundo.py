from gpiozero import LED, Button
import sys
from time import sleep, time
from datetime import datetime
import threading
from threading import Event
from server_distribuidos.models.car import Car
import json
from server_distribuidos.server_client_2 import send_data, enviar_carro_para_servidor, request_car_info, update_car_info, request_remove_car, listen_for_updates, request_status_lotacao_B, request_status_lotacao_B_v
from terreo import controlar_saida

endereco_01 = LED(9)
endereco_02 = LED(11)
endereco_03 = LED(15)
sensor_de_vaga = Button(1)
sinal_de_lotado_fechado = LED(14)
sensor_de_passagem_1 = Button(0)
sensor_de_passagem_2 = Button(7)

estados_vagas = [True] * 8
tem_vaga = [True] * 8
estacionamento_lotado = False
cancela_precionada = 0
comeco = 0
comeca_verificar = 0
estacionamento_lotado_v = None
waiting_for_sensor_2 = False
fechar_event = Event()
fechar_event_1 = Event()
t = False
event_descendo = Event()

def sensor_1_activated_callback():
    global waiting_for_sensor_2
    waiting_for_sensor_2 = True

def sensor_2_activated_callback():
    global waiting_for_sensor_2
    if not waiting_for_sensor_2:
        mensagem_subindo = ("Carro descendo.")
        waiting_for_sensor_2 = False
    elif waiting_for_sensor_2:
        mensagem_subindo = ("Carro subindo para o segundo andar.")
        waiting_for_sensor_2 = False
    send_data('localhost', 10398, to_json_message(mensagem_subindo))
    waiting_for_sensor_2 = False
        

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
        sleep(1.5)

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
        carro_descendo(vaga_num)
        sleep(1)
        
    elif estado_str == "ocupada":      
        vaga_info = {'tipo': tipo, 'D': 0}
        car = request_car_info('localhost', 10398, vaga_info)
        vaga_info = {'tipo': tipo, 'B': vaga_num}
        car['dados']['vaga'] = vaga_info
        car['dados']['vaga_num'] = vaga_num
        update_car_info('localhost', 10398, car)
        tem_vaga[vaga_id] = False

    estacionamento_lotado = all(not vaga for vaga in tem_vaga)
    
    verifica_led = request_status_lotacao_B_v('localhost', 10398)
    if estacionamento_lotado or verifica_led:
        sinal_de_lotado_fechado.on()
    else:
        sinal_de_lotado_fechado.off()

    request_status_lotacao_B('localhost', 10398)
    
    print(f"Vaga {tipo} B{vaga_num} {estado_str}.")

def monitorar_lotacao():
    global tem_vaga
    global estacionamento_lotado
    global estacionamento_lotado_v
    
    while True:
        
        if sinal_de_lotado_fechado.is_lit or all(not vaga for vaga in tem_vaga):
            sinal_de_lotado_fechado.on()
            segundo_fechar_estacionamento()
            fechar_event.wait()
            print("Estacionamento lotado ou fechado.")
            comeca_verificar = 0
            while comeca_verificar == 0:
                verifica_led = request_status_lotacao_B_v('localhost', 10398)
                if (estacionamento_lotado == False or not sinal_de_lotado_fechado.is_lit) and not verifica_led:
                    comeca_verificar = 1
                    sinal_de_lotado_fechado.off()
                sleep(0.1)
        sleep(1)

def segundo_fechar_estacionamento():
    global estacionamento_lotado
    global estacionamento_lotado_v
    estacionamento_lotado = True
    estacionamento_lotado_v = True
    sinal_de_lotado_fechado.on()
    sleep(0.3)
    fechar_event.set()

def segundo_abrir_estacionamento():
    global comeca_verificar
    global estacionamento_lotado 
    global tem_vaga
    if sinal_de_lotado_fechado.is_lit and not any(tem_vaga):
            estacionamento_lotado = True
    else:
        estacionamento_lotado = False
        sinal_de_lotado_fechado.off()
        comeca_verificar = 1
    sleep(0.3)

def carro_descendo(vaga_num):
    # message_descendo = 'Carro descendo'
    remover_carro_por_vaga_primeiro(vaga_num)
    controlar_saida('oi')
    # send_data('localhost', 10398, to_json_message(message_descendo))
            

def remover_carro_por_vaga_primeiro(vaga_num):
    tipo = 'disabled' if vaga_num == 1 else 'elderly' if vaga_num in [2, 3] else 'regular'
    vaga_info = {'tipo': tipo, 'B': vaga_num}
    car = request_car_info('localhost', 10398, vaga_info)
 
    if (('B' in vaga_info) and (car['dados']['vaga_num'] == vaga_num)):
        atualizar_current_charge(car)
        send = car['dados']['id']
        sleep(1.5)
        request_remove_car('localhost', 10398, send)
        sleep(0.5)

def atualizar_current_charge(car_data):
    entry_time = datetime.fromisoformat(car_data['dados']['entry_time'])
    duration = datetime.now() - entry_time
    minutes_parked = duration.total_seconds() / 60
    rate_per_minute = 0.10
    car_data['dados']['current_charge'] = round(minutes_parked * rate_per_minute, 3)



def to_json_entrada(car):
        return json.dumps({
            'carro id': car.id,
            'entry_time': car.entry_time.isoformat(),
            'vaga': car.vaga
        }, indent=4)

def to_json_saida(car):
        return json.dumps({
            'carro id': car.id,
            'vaga': car.vaga,
            'current_charge': car.calculate_current_charge()
        }, indent=4)



def to_json_message(message):
    return {
        'tipo': 'message',
        'dados': message
    }

sensor_de_passagem_1.when_released = sensor_1_activated_callback
sensor_de_passagem_2.when_released = sensor_2_activated_callback

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
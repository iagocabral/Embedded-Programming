import socket
import json
import threading
from collections import defaultdict
from datetime import datetime
from terreo import terreo_fechar_estacionamento, terreo_abrir_estacionamento
from primeiro import primeiro_fechar_estacionamento, primeiro_abrir_estacionamento
from segundo import segundo_fechar_estacionamento, segundo_abrir_estacionamento
import os

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        client_handler.start()

cars = {}
clients = []

sinal1 = False
sinal2 = False
car_counter = 0
message_counter = 0

def handle_client(client_socket, addr):
    global sinal1, sinal2
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print("No data received")
                break
            received_data = json.loads(data.decode('utf-8'))
            tipo = received_data['tipo']
            response = {}

            tipos_de_vaga_A, tipos_de_vaga_T, tipos_de_vaga_B = contar_tipos_de_vaga(cars)
                
            if tipo == "carro":
                process_car_data(received_data['dados'])
                send_updates_to_clients(received_data['dados'])
                response = {"status": "OK"}    
            elif tipo == "message":
                process_message(received_data['dados'])
                response = {"status": "OK"}
            elif tipo == 'get_car':
                vaga_info = received_data['vaga']
                car = get_car_by_vaga_num(vaga_info)
                response = car if car else {}
            elif tipo == 'remove_car':
                car_id = received_data['car_id']
                success = remove_car(car_id)
                response = {"success": success}
            elif tipo == 'update_car':
                car_data = received_data['car_data']
                success = update_car(car_data)
                response = {"success": success}
            elif tipo == 'status_lotacao_A' or tipo == 'status_lotacao_B':
                lotar_A = verificar_vagas_totais(tipos_de_vaga_A)
                lotar_B = verificar_vagas_totais(tipos_de_vaga_B)
                print("_________________________________________")
                print("Quantidade de cada tipo de vaga para 'T':")
                for tipo_vaga, contagens in tipos_de_vaga_T.items():
                    for tipo, quantidade in contagens.items():
                        if tipo == 'regular':
                            print(f" - {tipo}: {quantidade} ocupadas de 5 vagas disponiveis")
                        if tipo == 'disabled':
                            print(f" - {tipo}: {quantidade} ocupadas de 1 vagas disponiveis")
                        if tipo == 'elderly':
                            print(f" - {tipo}: {quantidade} ocupadas de 2 vagas disponiveis")
                        #x = 5 if tipo == 'regular' else (1 if tipo == 'disabled' else (2 if tipo == 'elderly' else None))
                        #print(f" - {tipo}: {quantidade} ocupadas de {x} vagas disponiveis")

                print("_________________________________________")
                print("Quantidade de cada tipo de vaga para 'A':")
                for tipo_vaga, contagens in tipos_de_vaga_A.items():
                    for tipo, quantidade in contagens.items():
                        x = 5 if tipo == 'regular' else (1 if tipo == 'disabled' else (2 if tipo == 'elderly' else None))
                        print(f" - {tipo}: {quantidade} ocupadas de {x} vagas disponiveis")
                
                print("_________________________________________")
                print("Quantidade de cada tipo de vaga para 'B':")
                for tipo_vaga, contagens in tipos_de_vaga_B.items():
                    for tipo, quantidade in contagens.items():
                        x = 5 if tipo == 'regular' else (1 if tipo == 'disabled' else (2 if tipo == 'elderly' else None))
                        print(f" - {tipo}: {quantidade} ocupadas de {x} vagas disponiveis")
                
                total_vagas_ocupadas_B = sum([sum(contagens.values()) for contagens in tipos_de_vaga_B.values()])
                total_vagas_ocupadas_A = sum([sum(contagens.values()) for contagens in tipos_de_vaga_A.values()])
                total_vagas_ocupadas_T = sum([sum(contagens.values()) for contagens in tipos_de_vaga_T.values()])
                total_vagas = total_vagas_ocupadas_B + total_vagas_ocupadas_A + total_vagas_ocupadas_T
                print("")
                print("______________________________________________")
                print("Número total de carros no Estacionamento: ", total_vagas)
                print("Número total de carros no Terreo: ", total_vagas_ocupadas_T)
                print("Número total de carros no Primeiro Andar: ", total_vagas_ocupadas_A)
                print("Número total de carros no Segundo Andar: ", total_vagas_ocupadas_B)
                print("______________________________________________")

        
            elif tipo == 'status_lotacao_A_v' or tipo == 'status_lotacao_B_v':
                lotar_A = verificar_vagas_totais(tipos_de_vaga_A)
                if sinal1 == True:
                    lotar_A = True
                elif sinal1 == False and lotar_A == True:
                    lotar_A = True
                lotar_B = verificar_vagas_totais(tipos_de_vaga_B)
                if sinal2 == True:
                    lotar_B = True
                elif sinal2 == False and lotar_B == True:
                    lotar_B = True
                if tipo == 'status_lotacao_A_v':
                    response = {"lotar_A": lotar_A}
                elif tipo == 'status_lotacao_B_v':
                    response = {"lotar_B": lotar_B}
            elif tipo == "fechar_estacionamento":
                fechar_estacionamento()
                response = {"status": "Estacionamento fechado"}
            elif tipo == "abrir_estacionamento":
                abrir_estacionamento()
                response = {"status": "Estacionamento aberto"}
            elif tipo == "bloquear_primeiro_andar":
                sinal1 = True
                bloquear_primeiro_andar()
                response = {"status": "Primeiro andar bloqueado"}
            elif tipo == "desbloquear_primeiro_andar":
                sinal1 = False
                desbloquear_primeiro_andar()
                response = {"status": "Primeiro andar desbloqueado"}
            elif tipo == "bloquear_segundo_andar":
                sinal2 = True
                bloquear_segundo_andar()
                response = {"status": "Segundo andar bloqueado"}
            elif tipo == "desbloquear_segundo_andar":
                sinal2 = False
                desbloquear_segundo_andar()
                response = {"status": "Segundo andar desbloqueado"}
            else:
                response = {"status": "OK"}
            response_json = json.dumps(response)
            client_socket.sendall(response_json.encode('utf-8'))
            break  
    except Exception as e:
        print(f"Erro no handle_client: {e}")
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()

def process_car_data(car_data):
    global car_counter
    if isinstance(car_data, str):
        car_data = json.loads(car_data)

    if 'dados' in car_data and isinstance(car_data['dados'], str):
        car_data['dados'] = json.loads(car_data['dados'])

    car_id = car_data['dados']['id']
    cars[car_id] = car_data
    car_counter += 1

    if car_counter % 4 == 0:
        os.system('clear')
        print("Carro", car_id, "entrou no estacionamento.")
        print("Horario: ", car_data['dados']['entry_time'])


def process_message(message):
    global message_counter
    if message['dados'] == "Carro subindo para o primeiro andar." or message['dados'] == "Carro subindo para o segundo andar." or message['dados'] == "Carro descendo.":
        message_counter += 1
        if message_counter % 2 == 0:
            print(message['dados'])
    else:
        print(message['dados'])

def get_car_by_vaga_num(vaga_info): 
    for car in cars.values():
        if 'dados' in car and 'vaga' in car['dados']:
            if 'D' in car['dados']['vaga'] and 'D' in vaga_info:
                if car['dados']['vaga']['D'] == vaga_info['D']:
                    return car
            elif 'T' in car['dados']['vaga'] and 'T' in vaga_info:
                if car['dados']['vaga']['T'] == vaga_info['T']:
                    return car
            elif 'A' in car['dados']['vaga'] and 'A' in vaga_info:
                if car['dados']['vaga']['A'] == vaga_info['A']:
                    return car
            elif 'B' in car['dados']['vaga'] and 'B' in vaga_info:
                if car['dados']['vaga']['B'] == vaga_info['B']:
                    return car
    return None

def send_updates_to_clients(update):
    for client in clients:
        try:
            client.sendall(json.dumps(update).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send update to a client: {e}")
            clients.remove(client)

def remove_car(car_id):
    if car_id in cars:
        car_data = cars[car_id]
        atualizar_current_charge(car_data)
        print("______________VOLTE SEMPRE!________________")
        print("Carro", car_id, "saindo da vaga.")
        print("valor pago:", car_data['dados']['current_charge'])
        print("___________________________________________")
        del cars[car_id]
        return True
    return False

def atualizar_current_charge(car_data):
    entry_time = datetime.fromisoformat(car_data['dados']['entry_time'])
    duration = datetime.now() - entry_time
    minutes_parked = duration.total_seconds() / 60
    rate_per_minute = 0.10
    car_data['dados']['current_charge'] = round(minutes_parked * rate_per_minute, 3)
    
def update_car(car_data):
    if isinstance(car_data, str):
        car_data = json.loads(car_data)

    if 'dados' in car_data and isinstance(car_data['dados'], str):
        car_data['dados'] = json.loads(car_data['dados'])

    car_id = car_data['dados']['id']
    if car_id in cars:
        cars[car_id]['dados'].update(car_data['dados'])
        if 'vaga' in car_data:
            cars[car_id]['dados']['vaga'] = car_data['vaga']
        if 'vaga_num' in car_data:
            cars[car_id]['dados']['vaga_num'] = car_data['vaga_num']
        return True
    return False

def verificar_vagas_totais(tipos_de_vaga):
    if sinal1 == True and sinal2 == True:
        return True
    for tipo, contagens in tipos_de_vaga.items():
        total_vagas_ocupadas = sum(contagens.values())
        if total_vagas_ocupadas == 8:
            return True
    return False

def contar_tipos_de_vaga(cars):
    global sinal2
    tipos_de_vaga_T = defaultdict(lambda: defaultdict(int))
    tipos_de_vaga_A = defaultdict(lambda: defaultdict(int))
    tipos_de_vaga_B = defaultdict(lambda: defaultdict(int))
    
    for car_id, car_info in cars.items():
        vaga = car_info['dados']['vaga']
        
        if 'T' in vaga:
            tipo_de_vaga = vaga['tipo']
            tipos_de_vaga_T['T'][tipo_de_vaga] += 1
        elif 'A' in vaga:
            tipo_de_vaga = vaga['tipo']
            tipos_de_vaga_A['A'][tipo_de_vaga] += 1
        elif 'B' in vaga:
            tipo_de_vaga = vaga['tipo']
            tipos_de_vaga_B['B'][tipo_de_vaga] += 1
    
    return tipos_de_vaga_A, tipos_de_vaga_T, tipos_de_vaga_B


def fechar_estacionamento():
    print("Fechando o estacionamento...")
    terreo_fechar_estacionamento()

def abrir_estacionamento():
    print("Abrindo o estacionamento...")
    terreo_abrir_estacionamento()

def bloquear_primeiro_andar():
    global sinal1
    sinal1 = True
    print("Bloqueando o primeiro andar...")
    primeiro_fechar_estacionamento()

def desbloquear_primeiro_andar():
    global sinal1
    sinal1 = False
    print("Desbloqueando o primeiro andar...")
    primeiro_abrir_estacionamento()

def bloquear_segundo_andar():
    global sinal2
    sinal2 = True
    print("Bloqueando o segundo andar...")
    segundo_fechar_estacionamento()

def desbloquear_segundo_andar():
    global sinal2
    sinal2 = False
    print("Desbloqueando o segundo andar...")
    segundo_abrir_estacionamento()

if __name__ == "__main__":
    servers = [
        threading.Thread(target=start_server, args=('localhost', 10400), daemon=True),
        threading.Thread(target=start_server, args=('localhost', 10399), daemon=True),
        threading.Thread(target=start_server, args=('localhost', 10398), daemon=True),
        threading.Thread(target=start_server, args=('localhost', 10397), daemon=True)
    ]

    for server in servers:
        server.start()

    for server in servers:
        server.join()
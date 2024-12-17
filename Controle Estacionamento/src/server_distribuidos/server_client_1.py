import socket
import json
import time
from datetime import datetime
import threading

def send_data(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        json_data = json.dumps({"tipo": 'message', "dados": data})
        sock.sendall(json_data.encode('utf-8'))
        response = sock.recv(1024)
        time.sleep(1)

def enviar_carro_para_servidor(car, server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        data = car.to_json()
        json_data = json.dumps({"tipo": "carro", "dados": data})
        sock.sendall(json_data.encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')

def listen_for_updates(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        while True:
            data = sock.recv(1024)
            if not data:
                break
            update = json.loads(data.decode('utf-8'))
            process_update(update)
            process_received_json(data.decode('utf-8'))

def process_update(update):
    print("Received update:", update)

def process_received_json(json_data):
    data = json.loads(json_data)

    car_id = data['id']
    entry_time = datetime.fromisoformat(data['entry_time'])
    vaga_info = data['vaga']
    vaga_num = data['vaga_num']
    current_charge = data['current_charge']

    vaga_tipo = vaga_info.get('tipo', 'Tipo desconhecido') if isinstance(vaga_info, dict) else "Informação de vaga não disponível"

    print(f"Car ID: {car_id}")
    print(f"Entry Time: {entry_time}")
    print(f"Tipo de Vaga: {vaga_tipo}")
    print(f"Número da Vaga: {vaga_num}")
    print(f"Current Charge: {current_charge:.2f} (calculated)")

    if vaga_num != 0:
        print(f"Carro {car_id} agora está na vaga {vaga_num}.")
    else:
        print(f"Carro {car_id} ainda não foi alocado a uma vaga.")

    return vaga_num

def request_car_info(server_host, server_port, vaga_info):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        request = json.dumps({"tipo": 'get_car', 'vaga': vaga_info})
        sock.sendall(request.encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')

        if not response:
            raise ValueError("Resposta vazia recebida do servidor.")
     
        try:
            responses = response.split('}{')
            if len(responses) > 1:
                responses = [responses[0] + '}', '{' + responses[1]]
                return json.loads(responses[0]), json.loads(responses[1])
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            print("Erro ao decodificar JSON:", e)
            print("Resposta completa recebida:", response)
            raise ValueError("Resposta do servidor não é um JSON válido.") from e
    
def update_car_info(server_host, server_port, car):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        request = json.dumps({"tipo": 'update_car', 'car_data': car})
        sock.sendall(request.encode('utf-8'))
        response = sock.recv(1024)
        return json.loads(response.decode('utf-8'))
    
def request_remove_car(server_host, server_port, car_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        request = json.dumps({"tipo": 'remove_car', 'car_id': car_id})
        sock.sendall(request.encode('utf-8'))
        response = sock.recv(1024)
        return json.loads(response.decode('utf-8'))

def request_status_lotacao_A(server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        request = json.dumps({'tipo': 'status_lotacao_A'})
        sock.sendall(request.encode('utf-8'))
        response = sock.recv(1024)
        status = json.loads(response.decode('utf-8'))
        return status.get('lotar_A', False)
    
def request_status_lotacao_A_v(server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_host, server_port))
        request = json.dumps({'tipo': 'status_lotacao_B_v'})
        sock.sendall(request.encode('utf-8'))
        response = sock.recv(1024)
        status = json.loads(response.decode('utf-8'))
        return status.get('lotar_B', False)

if __name__ == "__main__":
    listener_thread = threading.Thread(target=listen_for_updates, args=('localhost', 10399), daemon=True)
    listener_thread.start()

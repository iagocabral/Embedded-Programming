from server_client_terreo import request_car_info, update_car_info, enviar_carro_para_servidor
from server_client_1 import request_car_info1, update_car_info1, request_remove_car1
from models.car import Car
from time import sleep

def criar_carro():
    vaga_info = {'tipo': 'default', 'D': 0}
    car = Car(vaga_info, 0)
    enviar_carro_para_servidor(car, 'localhost', 10400)
    print('NOVO CARRO CRIADOS:', car)

    return car

def main():
    criar_carro()
    tipo = 'idoso'
    vaga_info = {'tipo': tipo, 'D': 0}
    car = request_car_info('localhost', 10400, vaga_info)
    print(f'Carro teste: {car}')
    vaga_info = {'tipo': tipo, 'T': 1}
    car['dados']['vaga'] = vaga_info
    car['dados']['vaga_num'] = 1
    update_car_info('localhost', 10400, car)
    print('CARRO DEPOIS DA ATUALIZACAO: ', car)
    sleep(2)
    print("==============================")
    criar_carro()
    tipo = 'idoso'
    vaga_info = {'tipo': tipo, 'D': 0}
    car = request_car_info('localhost', 10400, vaga_info)
    print(f'Carro teste: {car}')
    vaga_info = {'tipo': tipo, 'T': 2}
    car['dados']['vaga'] = vaga_info
    car['dados']['vaga_num'] = 2
    update_car_info('localhost', 10400, car)
    print('CARRO DEPOIS DA ATUALIZACAO: ', car)
    sleep(2)
    print("==============================")
    criar_carro()
    tipo = 'idoso'
    vaga_info1 = {'tipo': tipo, 'D': 0}
    car = request_car_info1('localhost', 10400, vaga_info1)
    print(f'Carro teste: {car}')
    vaga_info1 = {'tipo': tipo, 'A': 2}
    car['dados']['vaga'] = vaga_info1
    car['dados']['vaga_num'] = 2
    update_car_info1('localhost', 10400, car)
    print('CARRO DEPOIS DA ATUALIZACAO: ', car)
    sleep(10)
    print("==============================")
    request_car_info1('localhost', 10400, vaga_info1)
    if (('A' in vaga_info) and (car['dados']['vaga_num'] == 2)):
        # enviar_carro_para_servidor(car, 'localhost', 10400)
        send = car['dados']['id']
        request_remove_car1('localhost', 10400, send)



if __name__ == "__main__":
    main()
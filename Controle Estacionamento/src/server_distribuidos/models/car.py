from datetime import datetime

class Car:
    next_id = 1
    lista_de_carros = []

    def __init__(self, vaga, vaga_num):
        self.id = Car.next_id
        Car.next_id += 1
        self.entry_time = datetime.now()
        self.vaga = vaga
        self.vaga_num = vaga_num
        Car.lista_de_carros.append(self)
   
    def get_car(vaga_num):
        for car in Car.lista_de_carros:
            if car.vaga_num == vaga_num:
                return car
            
    def libera_car(self):
        Car.lista_de_carros.remove(self)

    def calculate_current_charge(self):
        duration = datetime.now() - self.entry_time
        minutes_parked = duration.total_seconds() / 60
        charge = (minutes_parked * 0.10)
        return charge
    
    def convert_json(self):
        return {
            'id': self.id,
            'entry_time': self.entry_time.isoformat()
        }

    def to_json(self):
        return {
            'tipo': 'carro',
            'dados': {
                'id': self.id,
                'entry_time': self.entry_time.isoformat(),
                'vaga': self.vaga,
                'vaga_num': self.vaga_num,
                'current_charge': self.calculate_current_charge()
            }
        }
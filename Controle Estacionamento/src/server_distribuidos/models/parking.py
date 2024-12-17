from datetime import datetime
import json
from .car import Car

class Parking:
    def __init__(self):
        self.cars = []
        self.floors = {
            'Terreo': {'vagas': {'regular': [False]*5, 'disabled': [False]*1, 'elderly': [False]*2}, 'cars': []},
            'First': {'vagas': {'regular': [False]*5, 'disabled': [False]*1, 'elderly': [False]*2}, 'cars': []},
            'Second': {'vagas': {'regular': [False]*5, 'disabled': [False]*1, 'elderly': [False]*2}, 'cars': []}
        }
        self.rate_per_minute = 0.10
        self.total_money_collected = 0

    def add_car(self, car_id, floor):
        car = Car(car_id)
        self.cars.append(car)
        self.floors[floor]['cars'].append(car)

    def park_car(self, floor, spot_type, car_id):
        car = next((car for car in self.floors[floor]['cars'] if car.id == car_id), None)
        if car and self.floors[floor]['vagas'][spot_type] > 0:
            self.floors[floor]['vagas'][spot_type] -= 1
            return True
        return False

    def remove_car(self, car_id):
        for floor_data in self.floors.items():
            car = next((car for car in floor_data['cars'] if car.id == car_id), None)
            if car:
                self.calculate_charge(car)
                floor_data['cars'].remove(car)
                return True
        return False

    def calculate_charge(self, car):
        duration = datetime.now() - car.entry_time
        minutes_parked = duration.total_seconds() / 60
        charge = minutes_parked * self.rate_per_minute
        self.total_money_collected += charge

    def get_car_count_floor(self, floor):
        return len(self.floors[floor]['cars'])

    def get_total_cars(self):
        return len(self.cars)

    def get_vagas_available(self, floor):
        return self.floors[floor]['vagas']
    
    def get_last_car(self):
        if self.cars:
            last_car = self.cars[-1]
            return last_car.convert_json()
        return None

    def to_json(self):
        return json.dumps({
            "last_car": self.get_last_car(),
            'floors': {floor: {'cars_count': self.get_car_count_floor(floor), 'vagas_available': self.get_vagas_available(floor)} for floor in self.floors},
            'total_cars': self.get_total_cars(),
            'total_money_collected': self.total_money_collected
        }, indent=4)
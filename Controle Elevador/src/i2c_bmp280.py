import smbus2
from bmp280 import BMP280  # Importa a classe BMP280 do módulo bmp280
from time import sleep

# Inicializa o barramento I2C
bus = smbus2.SMBus(1)

# Tenta inicializar os sensores BMP280 nos endereços 0x76 e 0x77
try:
    bmp280_1 = BMP280(i2c_dev=bus, i2c_addr=0x76)
except IOError as e:
    print("Could not find BMP280 sensor at address 0x76:", e)
    bmp280_1 = None

try:
    bmp280_2 = BMP280(i2c_dev=bus, i2c_addr=0x77)
except IOError as e:
    print("Could not find BMP280 sensor at address 0x77:", e)
    bmp280_2 = None

def temp_ambiente(elevador):
    if elevador == 0:
        if bmp280_1:
            return bmp280_1.get_temperature()
        else:
            raise RuntimeError("BMP280 sensor at address 0x76 is not available.")
    elif elevador == 1:
        if bmp280_2:
            return bmp280_2.get_temperature()
        else:
            raise RuntimeError("BMP280 sensor at address 0x77 is not available.")
    else:
        raise ValueError("ID do elevador inválido. Use 0 ou 1.")

# Teste básico para verificar se a função está funcionando
try:
    print(f"Elevador 1: {temp_ambiente(0)} C")
    print(f"Elevador 2: {temp_ambiente(1)} C")
except RuntimeError as e:
    print(e)
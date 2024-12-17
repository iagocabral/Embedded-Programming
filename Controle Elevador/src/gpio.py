import RPi.GPIO as GPIO
import logging
from time import sleep
from pid import PID
import cmds
from global_config import pwm_global  
from threading import Thread, Event
import uart
import global_config
import oled

class GPIOController:
    def __init__(self, elevador_id):
        self.id = elevador_id
        self.pwm_global = pwm_global  
        self.andar_solicitado = []
        self.exit_event = Event()
        self.uart_lock = global_config.uart_lock

        # Configuração dos pinos GPIO
        GPIO.setmode(GPIO.BCM)
        if self.id == 0:
            self.DIR1_PIN = 20
            self.DIR2_PIN = 21
            self.PWM_PIN = 12
            self.SENSOR_TERREO_PIN = 18
            self.SENSOR_1_ANDAR_PIN = 23
            self.SENSOR_2_ANDAR_PIN = 24
            self.SENSOR_3_ANDAR_PIN = 25
        else:
            self.DIR1_PIN = 19
            self.DIR2_PIN = 26
            self.PWM_PIN = 13
            self.SENSOR_TERREO_PIN = 17
            self.SENSOR_1_ANDAR_PIN = 27
            self.SENSOR_2_ANDAR_PIN = 22
            self.SENSOR_3_ANDAR_PIN = 6

        GPIO.setup(self.DIR1_PIN, GPIO.OUT)
        GPIO.setup(self.DIR2_PIN, GPIO.OUT)
        GPIO.setup(self.PWM_PIN, GPIO.OUT)
        GPIO.setup(self.SENSOR_TERREO_PIN, GPIO.IN)
        GPIO.setup(self.SENSOR_1_ANDAR_PIN, GPIO.IN)
        GPIO.setup(self.SENSOR_2_ANDAR_PIN, GPIO.IN)
        GPIO.setup(self.SENSOR_3_ANDAR_PIN, GPIO.IN)

        self.pwm = GPIO.PWM(self.PWM_PIN, 1000)  
        self.pwm.start(0)

        self.status = None
        self.terreo = None
        self.andar1 = None
        self.andar2 = None
        self.andar3 = None
        self.andar_atual = None
        self.nome_andar = None
        self.vel = None

        self.sensor_event = Event()

        self.zonas = {
            "terreo": [None, None],
            "andar1": [None, None],
            "andar2": [None, None],
            "andar3": [None, None]
        }

        self.endereco_para_andar_elevador0 = {
            0x00: 0,
            0x01: 1,
            0x02: 1,
            0x03: 2,
            0x04: 2,
            0x05: 3,
            0x06: 4,
            0x07: 0,
            0x08: 1,
            0x09: 2,
            0x0A: 3
        }

        self.endereco_para_andar_elevador1 = {
            0xA0: 0,
            0xA1: 1,
            0xA2: 1,
            0xA3: 2,
            0xA4: 2,
            0xA5: 3,
            0xA6: 4,
            0xA7: 0,
            0xA8: 1,
            0xA9: 2,
            0xAA: 3
        }

        self.endereco_para_andar = self.endereco_para_andar_elevador0 if self.id == 0 else self.endereco_para_andar_elevador1

    def start(self):
        thread = Thread(target=self.process_requests, name=f"Elevator{self.id}-Thread")
        thread.start()

    def stop(self):
        self.exit_event.set()
        for thread in self.threads:
            thread.join()

    def add_request(self, endereco):
        andar = self.endereco_para_andar.get(endereco, None)
        if andar is not None and not any(req['andar'] == andar for req in self.andar_solicitado):
            self.andar_solicitado.append({'andar': andar, 'endereco': endereco})
            logging.info(f"Adicionado pedido para o elevador {self.id} para o {andar}º andar com endereço {endereco}")

    def process_requests(self):
        while True:
            if self.andar_solicitado:
                request = self.andar_solicitado.pop(0)
                andar_destino = request['andar']
                endereco_botao = request['endereco']
                uart.encoder_event.set()
                self.ir_para_andar(andar_destino, endereco_botao)
            sleep(0.1)

    def monitorar_sensores(self, sensor_esperado):
        while not self.sensor_event.is_set():
            if GPIO.input(sensor_esperado):
                logging.info(f"Sensor {sensor_esperado} ativado para elevador {self.id}")
                self.sensor_event.set()
            sleep(0.1)

    def calibrar_elevador(self):
        self.start_pwm()
        self.definir_potencia_motor(1)
        self.andar_atual = cmds.apurar_encoder(self.id)
        if self.id == 0:
            elevador = 0
        else:
            elevador = 1 

        while True:
            logging.debug(f"Subindo o elevador para calibração elevador {self.id}")
            self.aciona_motor('sobe', elevador, 100)
            self.andar_atual = cmds.apurar_encoder(self.id)
            
            if GPIO.input(self.SENSOR_TERREO_PIN) == GPIO.HIGH:
                self.andar_atual = cmds.apurar_encoder(self.id)
                self.terreo = self.andar_atual
                logging.info(f"Valores calibrados para elevador {self.id}: Terreo={self.terreo}")
            if GPIO.input(self.SENSOR_1_ANDAR_PIN) == GPIO.HIGH:
                self.andar_atual = cmds.apurar_encoder(self.id)
                self.andar1 = self.andar_atual
                logging.info(f"Valores calibrados para elevador {self.id}: 1o Andar={self.andar1}")
            if GPIO.input(self.SENSOR_2_ANDAR_PIN) == GPIO.HIGH:
                self.andar_atual = cmds.apurar_encoder(self.id)
                self.andar2 = self.andar_atual
                logging.info(f"Valores calibrados para elevador {self.id}: 2o Andar={self.andar2}")
            if GPIO.input(self.SENSOR_3_ANDAR_PIN) == GPIO.HIGH:
                self.andar_atual = cmds.apurar_encoder(self.id)
                self.andar3 = self.andar_atual
                logging.info(f"Valores calibrados para elevador {self.id}: 3o Andar={self.andar3}")

            if self.andar_atual is None:
                logging.error("Falha ao obter o valor do Encoder.")
                return
            
            if self.andar_atual == self.andar3 or self.andar_atual >= 23000:
                logging.debug(f"Andar mais alto alcançado: {self.andar_atual}")
                self.aciona_motor('freio', elevador, 0)
                self.pwm_global[self.id] = 0
                cmds.apurar_pwm(self.id, self.pwm_global)
                break
        

        while True:
            logging.debug(f"Descendo o elevador {self.id} para calibração")
            self.aciona_motor('desce', elevador, 100)  # Define uma potência adequada para descer
            self.andar_atual = cmds.apurar_encoder(self.id)

            if self.andar_atual is None:
                logging.error(f"Falha ao obter o valor do Encoder para elevador {self.id}.")
                return

            if GPIO.input(self.SENSOR_TERREO_PIN) == GPIO.HIGH or self.andar_atual <= 2000:
                logging.debug(f"Andar atual para elevador {self.id}: {self.andar_atual}")
                self.aciona_motor('freio', elevador, 0)
                self.pwm_global[self.id] = 0
                cmds.apurar_pwm(self.id, self.pwm_global) 
                self.stop_pwm()
                break

        self.stop_pwm()

        if self.terreo is None or self.andar1 is None or self.andar2 is None or self.andar3 is None:
            self.terreo = 1549
            self.andar1 = 5239
            self.andar2 = 10297
            self.andar3 = 19687
        logging.info(f"Valores calibrados para elevador {self.id}: Terreo={self.terreo}, 1o Andar={self.andar1}, 2o Andar={self.andar2}, 3o Andar={self.andar3}")
        uart.encoder_event.clear()

    def start_pwm(self):
        self.pwm.start(0)

    def stop_pwm(self):
        self.pwm.stop()

    def definir_potencia_motor(self, potencia_percentual):
        logging.debug(f"Definindo potência do motor: {potencia_percentual}%")
        self.pwm.ChangeDutyCycle(potencia_percentual)

    def aciona_motor(self, sentido, elevador, potencia_percentual=100):
        logging.debug(f"Acionando motor no sentido: {sentido} com potência: {potencia_percentual}%")
        if sentido == 'sobe':
            GPIO.output(self.DIR1_PIN, GPIO.HIGH)
            GPIO.output(self.DIR2_PIN, GPIO.LOW)
            self.definir_potencia_motor(potencia_percentual)
            self.status = 'Subindo'
            oled.up_status(self.status, elevador)
            
        elif sentido == 'desce':
            GPIO.output(self.DIR1_PIN, GPIO.LOW)
            GPIO.output(self.DIR2_PIN, GPIO.HIGH)
            self.definir_potencia_motor(potencia_percentual)
            self.status = 'Descendo'
            oled.up_status(self.status, elevador)
        elif sentido == 'freio':
            GPIO.output(self.DIR1_PIN, GPIO.HIGH)
            GPIO.output(self.DIR2_PIN, GPIO.HIGH)
            self.definir_potencia_motor(potencia_percentual)
            self.status = 'Parado'
            oled.up_status(self.status, elevador)
        elif sentido == 'livre':
            GPIO.output(self.DIR1_PIN, GPIO.LOW)
            GPIO.output(self.DIR2_PIN, GPIO.LOW)
            self.definir_potencia_motor(0)
            self.status = 'Parado'
            oled.up_status(self.status, elevador)

    def ir_para_andar(self, andar, endereco_botao):
        self.pid = PID()
        self.start_pwm()
        logging.debug(f"pwm_global inicial para elevador {self.id}: {self.pwm_global}")

        if andar == 0:
            referencia_andar = self.terreo
            sensor_andar = self.SENSOR_TERREO_PIN
        elif andar == 1:
            referencia_andar = self.andar1
            sensor_andar = self.SENSOR_1_ANDAR_PIN
        elif andar == 2:
            referencia_andar = self.andar2
            sensor_andar = self.SENSOR_2_ANDAR_PIN
        elif andar == 3:
            referencia_andar = self.andar3
            sensor_andar = self.SENSOR_3_ANDAR_PIN
        else:
            logging.error(f"Andar {andar} inválido ou não calibrado para elevador {self.id}")
            return

        logging.info(f"Indo para o {andar}º andar do elevador {self.id}")

        while True:
            uart.encoder_event.set()

            self.andar_atual = cmds.apurar_encoder(self.id)
            erro = referencia_andar - self.andar_atual
            pid_output = self.pid.controle(erro)

            if abs(erro) < 300:  # Define uma margem de erro aceitável

                logging.info(f"Elevador {self.id} chegou ao {andar}º andar")
                self.aciona_motor('freio', self.id, 0)
                self.pwm_global[self.id] = 0
                cmds.apurar_pwm(self.id, self.pwm_global)

                cmds.apagar_botao(endereco_botao)
                break

            if erro > 0:
                logging.debug(f"Subindo o elevador {self.id}")
                self.aciona_motor('sobe', self.id, min(abs(pid_output), 10)) 
            elif erro < 0:
                logging.debug(f"Descendo o elevador {self.id}")
                self.aciona_motor('desce', self.id, min(abs(pid_output), 10)) 

            sleep(0.1)

        cmds.apurar_lcd(0, 1, self.exit_event)
        uart.encoder_event.clear()

        self.stop_pwm()
        logging.info(f"Elevador {self.id} chegou ao {andar}º andar")

  
    def verificar_sensores(self):
        return {
            "Terreo": GPIO.input(self.SENSOR_TERREO_PIN),
            "1o Andar": GPIO.input(self.SENSOR_1_ANDAR_PIN),
            "2o Andar": GPIO.input(self.SENSOR_2_ANDAR_PIN),
            "3o Andar": GPIO.input(self.SENSOR_3_ANDAR_PIN),
        }

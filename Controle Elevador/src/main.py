import logging
import log
from threading import Thread, Event
import signal
import sys
from time import sleep

logging.getLogger('').handlers.clear()
log.config_logging()

import cmds
import uart
import gpio
import pid
import struct

import global_config as gc

pid_control1 = pid.PID()
pid_control2 = pid.PID()
pid_control1.configura_constantes(Kp=0.5, Ki=0.05, Kd=40.0)
pid_control2.configura_constantes(Kp=0.5, Ki=0.05, Kd=40.0)
pid_control1.atualiza_referencia(0.0)
pid_control2.atualiza_referencia(0.0)

gc.controle1 = gpio.GPIOController(0)
gc.controle2 = gpio.GPIOController(1)

logging.debug(f"pwm_global inicial no main: {gc.pwm_global}")

exit_execution = Event()

def finaliza_programa(sig, frame):
    logging.info("Recebido sinal para finalizar o programa.")
    gc.controle1.stop_pwm()
    gc.controle2.stop_pwm()
    gpio.GPIO.cleanup()
    exit_execution.set()
    logging.info("Programa interrompido pelo usuário.")
    sys.exit(0)

def iniciar_threads():
    global button_thread
    button_thread = uart.start_button_reading_threads()

    # Configurando o tratamento de sinais para finalizar o programa
    signal.signal(signal.SIGINT, finaliza_programa)
    signal.signal(signal.SIGTERM, finaliza_programa)


if __name__ == "__main__":
    global button_thread
    try:
        uart.open_uart()
        uart.uart_in_use_event.set()
        gc.controle1.calibrar_elevador()
        gc.controle2.calibrar_elevador()
        cmds.apurar_lcd(0, 1, exit_execution)
        gc.controle1.start()
        gc.controle2.start()
        iniciar_threads()
    except KeyboardInterrupt:
        logging.info("Programa interrompido pelo usuário")
    finally:
        gc.controle1.stop_pwm()
        gc.controle2.stop_pwm()
        gc.controle1.stop()
        gc.controle2.stop()
        uart.stop_button_reading_threads(button_thread)
        uart.close_uart()
from threading import Lock

uart_lock = Lock()

pwm_global = [40, 40]

uart_file = None
encoder_value_elevator_1 = 0
encoder_value_elevator_2 = 0
pid_to_send_elevator_1 = 0
pid_to_send_elevator_2 = 0

controle1 = None
controle2 = None

terminei_leitura_botao = 0

temperature = 10.0
temperature1 = 11.0
# Trabalho 1 (2024-1) - Controle de Estacionamentos
Trabalho 1 da disciplina de Fundamentos de Sistemas Embarcados.

### Integrantes
| Nome    | Matricula |
|:-----------|------:|
| Guilherme Keyti Cabral Kishimoto | 190088257 |
| Iago de Paula Cabral | 190088745 |


## Sobre
Este trabalho tem por objetivo a criação de um sistema distribuído para o controle e monitoramento de estacionamentos comerciais. Dentre os itens controlados teremos a entrada e saída de veículos, a ocupação de cada vaga individualmente, a ocupação do estacionamento como um todo e a cobrança por tempo de permanência.

## Requisitos
- Python 3.9 ou superior
- gpiozero (https://gpiozero.readthedocs.io)


## Execução
1) Conectar nas placas de Fundamentos de sistemas embarcados.
2) executar o servidor central:
    ``` 
    python server_central.py # terminal 1
    ```

3) rodar os servidores distribuidos em diferentes terminais, nao importa a ordem de execução.
    ```
    python terreo.py # terminal 2
    ```
    ```
    python primeiro.py # terminal 3
    ```
    ```
    python segundo.py # terminal 4
    ```

4) Caso queira rodar a interface para comandos manuais do estacionamento:
    ```
    python interface.py # terminal 5
    ```

## Apresentação
Link da apresentação: https://youtu.be/C2OlpP-Yl9Q  


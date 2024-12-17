import socket
import json

CENTRAL_SERVER_HOST = 'localhost'
CENTRAL_SERVER_PORT = 10397

def enviar_comando(tipo, dados=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((CENTRAL_SERVER_HOST, CENTRAL_SERVER_PORT))
        comando = {"tipo": tipo}
        if dados:
            comando["dados"] = dados
        json_comando = json.dumps(comando)
        sock.sendall(json_comando.encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        print("Resposta do servidor:", response)

def fechar_abrir_estacionamento():
    print("\nEscolha uma ação para o estacionamento:")
    print("1. Fechar Estacionamento")
    print("2. Abrir Estacionamento")
    escolha = input("Digite o número da ação desejada: ")
    
    if escolha == '1':
        enviar_comando("fechar_estacionamento")
    elif escolha == '2':
        enviar_comando("abrir_estacionamento")
    else:
        print("Escolha inválida")

def bloquear_desbloquear_andar():
    print("\nEscolha uma ação para o andar:")
    print("1. Bloquear 1º Andar")
    print("2. Desbloquear 1º Andar")
    print("3. Bloquear 2º Andar")
    print("4. Desbloquear 2º Andar")
    escolha = input("Digite o número da ação desejada: ")
    
    if escolha == '1':
        enviar_comando("bloquear_primeiro_andar")
    elif escolha == '2':
        enviar_comando("desbloquear_primeiro_andar")
    elif escolha == '3':
        enviar_comando("bloquear_segundo_andar")
    elif escolha == '4':
        enviar_comando("desbloquear_segundo_andar")
    else:
        print("Escolha inválida")

def main():
    while True:
        print("\nMenu de Controle do Estacionamento")
        print("1. Fechar/Abrir Estacionamento")
        print("2. Bloquear/Desbloquear Andares")
        print("3. Sair")
        escolha = input("Digite o número da ação desejada: ")

        if escolha == '1':
            fechar_abrir_estacionamento()
        elif escolha == '2':
            bloquear_desbloquear_andar()
        elif escolha == '3':
            print("Saindo...")
            break
        else:
            print("Escolha inválida")

if __name__ == "__main__":
    main()
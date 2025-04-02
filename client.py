import socket

HOST = "localhost"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

modes = ["em_rajada", "individual"]

while True:
    try:
        mode_code = int(input(
            "Digite [1] para o modo Em Rajada (Go-Back-N)\n"
            "Digite [2] para o modo Individual (Repetição Seletiva)\n"
            "Digite: "
        ))
        if mode_code not in [1, 2]:
            print("\nDigite apenas [1] ou [2]\n")
        else:
            mode = modes[mode_code - 1]
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

while True:
    try:
        max_length = int(input("Digite o tamanho máximo da mensagem (Máx 3): "))
        if max_length > 3 or max_length < 1:
            print("\nO tamanho máximo precisa estar entre 1 e 3\n")
        else:
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

handshakeMessage = f"{mode};{max_length}"

client.send(handshakeMessage.encode())
print(f"[CLIENTE] Handshake enviado: modo={mode}, tamanho máximo={max_length}")

confirmation = client.recv(1024).decode()
print(f"[CLIENTE] Confirmação recebida do servidor: {confirmation}")

client.close()

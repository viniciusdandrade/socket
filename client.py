# cliente.py
import socket
import math

HOST = "localhost"
PORT = 5000

# configurações de handshake
modes = ["em_rajada", "individual"]
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# seleção de modo
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

# seleção de tamanho máximo
while True:
    try:
        max_length = int(input("Digite o tamanho máximo da mensagem (Máx 3): "))
        if max_length > 3 or max_length < 1:
            print("\nO tamanho máximo precisa estar entre 1 e 3\n")
        else:
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

# envio de handshake
handshakeMessage = f"{mode};{max_length}"
client.send(handshakeMessage.encode())
print(f"[CLIENTE] Handshake enviado: modo={mode}, tamanho máximo={max_length}")

# recepção de confirmação
confirmation = client.recv(1024).decode()
print(f"[CLIENTE] Confirmação recebida do servidor: {confirmation}")

# leitura da mensagem a enviar
texto = input("Digite a mensagem a ser enviada: ")

# fragmentação em pacotes com número de sequência
num_packets = math.ceil(len(texto) / max_length)
for seq in range(num_packets):
    start = seq * max_length
    payload = texto[start:start + max_length]
    packet = f"{seq}|{payload}"
    client.send(packet.encode())
    print(f"[CLIENTE] Pacote enviado: {packet}")

    # espera ACK
    ack = client.recv(1024).decode()
    print(f"[CLIENTE] ACK recebido: {ack}")

client.close()

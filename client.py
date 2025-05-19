import socket
import math
import time

HOST = "localhost"
PORT = 5065
TIMEOUT = 1

modes = ["em_rajada", "individual"]
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.settimeout(TIMEOUT)

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

# Escolha do modo
tipo = None
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
            tipo = modes[mode_code - 1]
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

# Tamanho máximo
while True:
    try:
        max_length = int(input("Digite o tamanho máximo da mensagem (Máx 3): "))
        if not 1 <= max_length <= 3:
            print("\nO tamanho máximo precisa estar entre 1 e 3\n")
        else:
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

window_size = 4
# Handshake inicial
data = f"{tipo};{max_length};{window_size}\n"
client.send(data.encode())
print(f"[CLIENTE] Handshake enviado: modo={tipo}, max_length={max_length}, janela={window_size}")
confirmation = client.recv(1024).decode().strip()
print(f"[CLIENTE] Confirmação recebida: {confirmation}\n")

# Loop de envio de mensagens
while True:
    texto = input("Digite a mensagem a ser enviada (ou 'sair' para encerrar): ")
    if texto.strip().lower() == "sair":
        client.send("FIM\n".encode())
        break

    num_packets = math.ceil(len(texto) / max_length)
    base = 0
    next_seq = 0
    acked = [False] * num_packets
    timer_start = None
    finished = False
    timeout_attempts = 0

    # Tenta enviar até 3 timeouts
    while not finished and timeout_attempts < 3:
        # Envio de pacotes na janela
        while next_seq < num_packets and next_seq < base + window_size:
            start = next_seq * max_length
            payload = texto[start:start + max_length]
            checksum = calcular_checksum(payload)
            packet = f"seq={next_seq}|data={payload}|sum={checksum}"
            if next_seq + 1 == num_packets:
                packet += "&"
            packet += "\n"

            client.send(packet.encode())
            print(f"[CLIENTE] Pacote enviado: {packet.strip()}")
            if base == next_seq:
                timer_start = time.time()
            next_seq += 1

        try:
            data = client.recv(1024).decode()
            for ack_msg in data.splitlines():
                if ack_msg.startswith("ACK"):
                    timeout_attempts = 0
                    fim = time.time()
                    print(f"[CLIENTE] ACK recebido: {ack_msg} ✅")
                    print(f"[CLIENTE] Tempo de Resposta: {(fim - timer_start):.4f}s ⏰\n")

                    parts = ack_msg.split("|")
                    ack_seq = int(parts[1]) if len(parts) > 1 else None
                    if ack_seq is not None:
                        if tipo == "em_rajada":
                            for i in range(base, ack_seq):
                                acked[i] = True
                            base = ack_seq
                        else:
                            acked[ack_seq] = True
                            while base < num_packets and acked[base]:
                                base += 1

                        if all(acked):
                            finished = True
                            break
                elif ack_msg.startswith("NACK"):
                    print(f"[CLIENTE] NACK recebido: {ack_msg.replace('@','')} ❌")

        except socket.timeout:
            timeout_attempts += 1
            if timeout_attempts >= 3:
                print(f"[CLIENTE] Número máximo de timeouts ({timeout_attempts}) atingido.")
                # Aborta mensagem para resetar no servidor
                client.send("ENDMSG\n".encode())
                break

            print(f"[CLIENTE] Timeout. Reenviando janela base={base} (tentativa {timeout_attempts}/3)")
            for seq in range(base, min(base + window_size, num_packets)):
                if tipo == "individual" and acked[seq]:
                    continue
                start = seq * max_length
                payload = texto[start:start + max_length]
                checksum = calcular_checksum(payload)
                packet = f"seq={seq}|data={payload}|sum={checksum}"
                if seq + 1 == num_packets:
                    packet += "&"
                packet += "\n"
                client.send(packet.encode())
                print(f"[CLIENTE] Reenviado: {packet.strip()}")
            timer_start = time.time()

# Ao sair do loop de envio, recomeça para nova mensagem

client.close()
print("[CLIENTE] Conexão encerrada.")
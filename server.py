import socket

HOST = "localhost"
PORT = 5065

# Escolha do modo de simulação
while True:
    try:
        mode_code = int(input(
            "Digite [1] para simular perda de pacote\n"
            "Digite [2] para continuar normalmente\n"
            "Digite: "
        ))
        if mode_code not in [1, 2]:
            print("\nDigite apenas [1] ou [2]\n")
        else:
            if mode_code == 1:
                perderPacote = True
                while True:
                    try:
                        pacotePerdido = int(input("Digite o número do pacote que será perdido: "))
                        break
                    except ValueError:
                        print("\nEntrada inválida! Digite um número\n")
            else:
                pacotePerdido = None
                perderPacote = False
            break
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

# Criação do servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")
conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

# Função para checksum
def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

# Receber o handshake
buffer = ""
while "\n" not in buffer:
    data = conn.recv(1024).decode()
    if not data:
        break
    buffer += data

header, buffer = buffer.split("\n", 1)
mode, max_len_str, window_str = header.split(";")
max_length = int(max_len_str)
window_size = int(window_str)
print(f"[SERVIDOR] Handshake: modo={mode}, max_payload={max_length}, janela={window_size}\n")
conn.send("HANDSHAKE_OK\n".encode())

# Loop principal para múltiplas mensagens
while True:
    expected_seq = 0
    received = {}
    buffer = ""
    mensagem_finalizada = False
    last_packet_seq = None

    while not mensagem_finalizada:
        data = conn.recv(1024).decode()
        if not data:
            break
        if "FIM" in data:
            print("\n[SERVIDOR] Conexão encerrada pelo cliente.")
            conn.close()
            server.close()
            exit(0)

        buffer += data

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            try:
                if "&" in line:
                    lastPacket = True
                    line = line.replace("&", "")
                else:
                    lastPacket = False

                parts = line.strip().split("|")
                data_dict = {}
                for part in parts:
                    key, value = part.split("=", 1)
                    data_dict[key] = value

                seq = int(data_dict["seq"])
                if seq == pacotePerdido and perderPacote:
                    perderPacote = False
                    continue
                payload = data_dict["data"]
                checksum_recv = int(data_dict["sum"])
            except ValueError:
                print(f"[SERVIDOR] Pacote mal formado: {line}")
                continue

            if checksum_recv != calcular_checksum(payload):
                print(f"[SERVIDOR] Checksum inválido seq={seq}")
                continue

            print(f"[SERVIDOR] Pacote recebido {line}")
            print(f"[SERVIDOR] Checksum válido {line} ✅")

            if seq in received:
                print(f"[SERVIDOR] Pacote repetido\n")
                continue

            if seq < expected_seq or seq >= expected_seq + window_size:
                ack = f"ACK|{expected_seq}\n" if mode == "em_rajada" else f"ACK|{seq}\n"
                conn.send(ack.encode())
                continue

            received[seq] = payload

            if mode == "individual":
                ack = f"ACK|{seq}|[{abs(4 - window_size)}-{window_size - 1}]\n"
                window_size += 1
                conn.send(ack.encode())
                print(f"[SERVIDOR] Enviado {ack.strip()}\n")

                if seq == expected_seq:
                    while expected_seq in received:
                        expected_seq += 1

                if lastPacket:
                    last_packet_seq = seq

                if last_packet_seq is not None:
                    if all(i in received for i in range(last_packet_seq + 1)):
                        mensagem_finalizada = True

            else:  # em_rajada
                if seq == expected_seq:
                    while expected_seq in received:
                        expected_seq += 1

                if lastPacket:
                    ack = f"ACK|{expected_seq}|[{abs(4 - window_size)}-{window_size - 1}]\n"
                    window_size += 1
                    conn.send(ack.encode())
                    print(f"[SERVIDOR] Enviado {ack.strip()}\n")
                    mensagem_finalizada = True
                else:
                    if window_size <= len(received):
                        ack = f"NACK|{expected_seq}|[{abs(4 - window_size)}-{window_size - 1}]\n"
                        conn.send(ack.encode())
                        print(f"[SERVIDOR] Enviado {ack.strip()} ❌\n")
                        expected_seq = 0
                        received.clear()
                        buffer = ""
                        mensagem_finalizada = False
                        break

    txt = ''.join(received[i] for i in sorted(received))
    print(f"[SERVIDOR] Mensagem completa: '{txt}'\n")

    # 🔄 Reset completo para próxima mensagem
    expected_seq = 0
    received.clear()
    buffer = ""
    mensagem_finalizada = False
    last_packet_seq = None
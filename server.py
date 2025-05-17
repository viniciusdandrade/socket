import socket

HOST = "localhost"
PORT = 5065

# Escolha do tipo de simulação
perderPacote = False
falharPacote = False
pacotePerdido = None
pacoteFalho = None
erros = []

while True:
    try:
        print("Simulação de falhas:")
        print("[1] Simular perda de pacote")
        print("[2] Simular falha de pacote (checksum inválido)")
        print("[3] Continuar normalmente")
        escolha = int(input("Digite: "))

        if escolha == 1:
            perderPacote = True
            pacotePerdido = int(input("Digite o número do pacote que será perdido: "))
            break
        elif escolha == 2:
            falharPacote = True
            pacoteFalho = int(input("Digite o número do pacote que terá falha no checksum: "))
            break
        elif escolha == 3:
            break
        else:
            print("\nDigite apenas [1], [2] ou [3]\n")
    except ValueError:
        print("\nEntrada inválida! Digite um número\n")

# Criação do servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")
conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

# Handshake
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

# Loop principal
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
                lastPacket = "&" in line
                line = line.replace("&", "")

                parts = line.strip().split("|")
                data_dict = {key: value for key, value in (p.split("=", 1) for p in parts)}
                seq = int(data_dict["seq"])
                if seq==pacotePerdido and seq not in erros:
                    perderPacote = True
                if seq==pacoteFalho and seq not in erros:
                    falharPacote = True
             
                payload = data_dict["data"]
                checksum_recv = int(data_dict["sum"])

                # Simular perda
                if seq == pacotePerdido and perderPacote:
                    erros.append(seq)
                    print(f"[SERVIDOR] Simulando perda do pacote {seq}")
                    perderPacote = False
                    continue

                # Simular falha
                if seq == pacoteFalho and falharPacote:
                    erros.append(seq)
                    print(f"[SERVIDOR] Simulando falha no pacote {seq}")
                    checksum_recv = -1
                    falharPacote = False

                # Checksum inválido
                if checksum_recv != calcular_checksum(payload):
                    print(f"[SERVIDOR] Pacote corrompido (checksum inválido) seq={seq}")
                    
                    if mode == "em_rajada":
                        if seq == expected_seq:
                            nack = f"NACK|{expected_seq}|[{abs(4 - window_size)}-{window_size - 1}]@\n"
                            conn.send(nack.encode())
                            print(f"[SERVIDOR] Enviado {nack.strip()} ❌ (pacote corrompido)\n")
                    
                    elif mode == "individual":
                        nack = f"NACK|{seq}|[{abs(4 - window_size)}-{window_size - 1}]@\n"
                        conn.send(nack.encode())
                        print(f"[SERVIDOR] Enviado {nack.strip()} ❌ (pacote corrompido)\n")
                    
                    continue

                # Pacote repetido
                if seq in received:
                    print(f"[SERVIDOR] Pacote repetido seq={seq}\n")
                    continue

                # Fora de ordem no Go-Back-N
                if mode == "em_rajada" and seq != expected_seq:
                    print(f"[SERVIDOR] Ignorando pacote fora de ordem: seq={seq}, esperado={expected_seq}")
                    continue

                # Fora de janela no modo individual
                if mode == "individual" and (seq < expected_seq or seq >= expected_seq + window_size):
                    ack = f"ACK|{seq}\n"
                    conn.send(ack.encode())
                    continue

                print(f"[SERVIDOR] Pacote recebido {line}")
                print(f"[SERVIDOR] Checksum válido {line} ✅")
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
                            nack = f"NACK|{expected_seq}|[{abs(4 - window_size)}-{window_size - 1}]\n"
                            conn.send(nack.encode())
                            print(f"[SERVIDOR] Enviado {nack.strip()} ❌ (janela cheia)\n")
                            expected_seq = 0
                            buffer = ""
                            mensagem_finalizada = False
                            break

            except Exception as e:
                print(f"[SERVIDOR] Erro ao processar pacote: {e}")
                continue

    txt = ''.join(received[i] for i in sorted(received))
    print(f"[SERVIDOR] Mensagem completa: '{txt}'\n")

    # Reset para próxima mensagem
    erros.clear()
    expected_seq = 0
    received.clear()
    buffer = ""
    mensagem_finalizada = False
    last_packet_seq = None

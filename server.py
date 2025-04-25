import socket

HOST = "localhost"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")
conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)


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
print(f"[SERVIDOR] Handshake: modo={mode}, max_payload={max_length}, janela={window_size}")
conn.send("HANDSHAKE_OK\n".encode())

expected_seq = 0
received = {}


while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    buffer += data
    
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        try:
            seq_str, payload, checksum_str = line.split("|", 2)
            seq = int(seq_str)
            checksum_recv = int(checksum_str)
        except ValueError:
            print(f"[SERVIDOR] Pacote mal formado: {line}")
            continue

        if checksum_recv != calcular_checksum(payload):
            print(f"[SERVIDOR] Checksum inválido seq={seq}")
            continue

        
        if seq < expected_seq or seq >= expected_seq + window_size:
            ack = f"ACK|{expected_seq}\n" if mode == "em_rajada" else f"ACK|{seq}\n"
            conn.send(ack.encode())
            continue

        received[seq] = payload
        if mode == "individual":
            ack = f"ACK|{seq}\n"
        else:
            if seq == expected_seq:
                while expected_seq in received:
                    expected_seq += 1
            ack = f"ACK|{expected_seq}\n"

        conn.send(ack.encode())
        print(f"[SERVIDOR] Enviado {ack.strip()}")


txt = ''.join(received[i] for i in sorted(received))
print(f"[SERVIDOR] Mensagem completa: '{txt}'")
conn.close()
server.close()
print("[SERVIDOR] Conexão encerrada.")
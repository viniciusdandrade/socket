# servidor.py
import socket

HOST = "localhost"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")
conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

data = conn.recv(1024).decode()
mode, max_length = data.split(";")
max_length = int(max_length)
print(f"[SERVIDOR] Handshake recebido:")
print(f"  ➤ Modo de operação: {mode}")
print(f"  ➤ Tamanho máximo da carga útil: {max_length} caracteres")

conn.send("HANDSHAKE_OK".encode())

print("\n")

expected_seq = 0
received = {}

while True:
    try:
        packet = conn.recv(1024).decode()
        if not packet:
            break
    except ConnectionResetError:
        break

    try:
        seq_str, payload, checksum_str = packet.split("|", 2)
    except ValueError:
        print(f"[SERVIDOR] Erro no formato do pacote. Ignorando.")
        continue

    seq = int(seq_str)
    checksum_recebido = int(checksum_str)
    checksum_calculado = calcular_checksum(payload)

    if checksum_recebido != checksum_calculado:
        print(f"[SERVIDOR] Erro de checksum no pacote seq={seq}. Ignorando pacote.")
        continue

    print(f"[SERVIDOR] Pacote válido: seq={seq}, payload='{payload}', checksum={checksum_recebido}")

    if mode == "individual":
        received[seq] = payload
        ack = f"ACK|{seq}"
    else:
        if seq == expected_seq:
            received[seq] = payload
            expected_seq += 1
        ack = f"ACK|{expected_seq}"

    conn.send(ack.encode())
    print(f"[SERVIDOR] Enviou { 'ACK individual' if mode=='individual' else 'ACK cumulativo' }: {ack}")

    print("\n")

mensagem = "".join(received[i] for i in sorted(received))
print(f"[SERVIDOR] Mensagem reconstruída: '{mensagem}'")

conn.close()

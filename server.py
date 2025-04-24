# servidor.py
import socket

HOST = "localhost"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")
conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

# recebe e processa handshake
data = conn.recv(1024).decode()
mode, max_length = data.split(";")
max_length = int(max_length)
print(f"[SERVIDOR] Handshake recebido:")
print(f"  ➤ Modo de operação: {mode}")
print(f"  ➤ Tamanho máximo da carga útil: {max_length} caracteres")

conn.send("HANDSHAKE_OK".encode())

# parâmetros para recepção de dados
expected_seq = 0
received = {}

# loop de recebimento até o cliente fechar
while True:
    try:
        packet = conn.recv(1024).decode()
        if not packet:
            break
    except ConnectionResetError:
        break

    seq_str, payload = packet.split("|", 1)
    seq = int(seq_str)
    print(f"[SERVIDOR] Pacote recebido: seq={seq}, payload='{payload}'")

    if mode == "individual":
        # ACK individual
        received[seq] = payload
        ack = f"ACK|{seq}"
    else:
        # Go-Back-N: só aceita em ordem
        if seq == expected_seq:
            received[seq] = payload
            expected_seq += 1
        # ACK cumulativo: último seq recebido em ordem
        ack = f"ACK|{expected_seq - 1}"

    conn.send(ack.encode())
    print(f"[SERVIDOR] Enviou { 'ACK individual' if mode=='individual' else 'ACK cumulativo' }: {ack}")

# reagrupa mensagem final
mensagem = "".join(received[i] for i in sorted(received))
print(f"[SERVIDOR] Mensagem reconstruída: '{mensagem}'")

conn.close()

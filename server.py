import socket

HOST = "localhost"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print(f"[SERVIDOR] Aguardando conexão na porta {PORT}...")

conn, addr = server.accept()
print(f"[SERVIDOR] Conectado a {addr}")

data = conn.recv(1024).decode()
mode, max_length = data.split(";")

print(f"[SERVIDOR] Handshake recebido:")
print(f"  ➤ Modo de operação: {mode}")
print(f"  ➤ Tamanho máximo da carga útil: {max_length} caracteres")

conn.send("HANDSHAKE_OK".encode())

conn.close()

import socket

HOST = 'localhost'
PORTA = 5000

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORTA))
servidor.listen(1)

print(f"[SERVIDOR] Aguardando conexão na porta {PORTA}...")

conn, addr = servidor.accept()
print(f"[SERVIDOR] Conectado a {addr}")

dados = conn.recv(1024).decode()
modo, tamanho_max = dados.split(";")

print(f"[SERVIDOR] Handshake recebido:")
print(f"  ➤ Modo de operação: {modo}")
print(f"  ➤ Tamanho máximo da carga útil: {tamanho_max} caracteres")

conn.send("HANDSHAKE_OK".encode())

conn.close()
import socket

HOST = 'localhost'  
PORTA = 5000

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

cliente.connect((HOST, PORTA))

tipo_modo =int(input("Digite [1] para o modo Em Lote\nDigite [2] para o modo Individual\nDigite: "))

if (tipo_modo==1):
    modo="em_lote"
elif (tipo_modo==2):
    modo="individualmente"

tamanho_max= int(input("Digite o tamanho máximo da mensagem: "))
mensagem_handshake = f"{modo};{tamanho_max}"

cliente.send(mensagem_handshake.encode())
print(f"[CLIENTE] Handshake enviado: modo={modo}, tamanho máximo={tamanho_max}")

confirmacao = cliente.recv(1024).decode()
print(f"[CLIENTE] Confirmação recebida do servidor: {confirmacao}")

cliente.close()
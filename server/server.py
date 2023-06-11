import socket
import threading
import os
import select

# Constants
HOST = '127.0.0.1'  # Host address
PORT = 2022  # Port number
BUFFER_SIZE = 1024  # Buffer size for receiving data
DIRECTORY = './ftp_server_files'  # Directory for storing files

# Dictionary to store client connections
clients = {}

# Function to handle client connections
def handle_client(client_socket):
    client_address = client_socket.getpeername()
    print(f'Accepted connection from {client_address}')
    
    client_socket.send('220 Welcome to the FTP server\r\n'.encode())
    
    authenticated = False
    current_directory = DIRECTORY
    
    while True:
        # Use select to handle both incoming data and user input
        ready_to_read, _, _ = select.select([client_socket], [], [], 0.1)
        
        if client_socket in ready_to_read:
            data = client_socket.recv(BUFFER_SIZE).decode().strip()
            
            if not data:
                print(f'Connection closed by {client_address}')
                break
            
            print(f'Received: {data}')
            
            command = data.split(' ')[0].upper()
            
            if command == 'USER':
                client_socket.send('331 User name okay, need password.\r\n'.encode())
            elif command == 'PASS':
                authenticated = True
                client_socket.send('230 User logged in, proceed.\r\n'.encode())
            elif not authenticated:
                client_socket.send('530 Not logged in.\r\n'.encode())
            elif command == 'CWD':
                directory = data.split(' ')[1]
                if os.path.exists(os.path.join(current_directory, directory)):
                    current_directory = os.path.join(current_directory, directory)
                    client_socket.send('250 Directory changed.\r\n'.encode())
                else:
                    client_socket.send('550 Directory not found.\r\n'.encode())
            elif command == 'QUIT':
                client_socket.send('221 Service closing control connection.\r\n'.encode())
                break
            elif command == 'RETR':
                filename = data.split(' ')[1]
                filepath = os.path.join(current_directory, filename)
                if os.path.isfile(filepath):
                    client_socket.send('200 Ready to send file.\r\n'.encode())
                    with open(filepath, 'rb') as file:
                        data = file.read(BUFFER_SIZE)
                        while data:
                            client_socket.send(data)
                            data = file.read(BUFFER_SIZE)
                    client_socket.send('202 File transfer complete.\r\n'.encode())
                else:
                    client_socket.send('550 File not found.\r\n'.encode())
            elif command == 'STOR':
                filename = data.split(' ')[1]
                filepath = os.path.join(current_directory, filename)
                client_socket.send('200 Ready to receive file.\r\n'.encode())
                with open(filepath, 'wb') as file:
                    while True:
                        data = client_socket.recv(BUFFER_SIZE)
                        if not data:
                            break
                        file.write(data)
                client_socket.send('202 File transfer complete.\r\n'.encode())
            elif command == 'RNTO':
                old_filename = data.split(' ')[1]
                new_filename = data.split(' ')[2]
                old_filepath = os.path.join(current_directory, old_filename)
                new_filepath = os.path.join(current_directory, new_filename)
                if os.path.isfile(old_filepath):
                    os.rename(old_filepath, new_filepath)
                    client_socket.send('202 Rename successful.\r\n'.encode())
                else:
                    client_socket.send('550 File not found.\r\n'.encode())
            elif command == 'DELE':
                filename = data.split(' ')[1]
                filepath = os.path.join(current_directory, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    client_socket.send('202 File deleted.\r\n'.encode())
                else:
                    client_socket.send('550 File not found.\r\n'.encode())
            elif command == 'RMD':
                directory = data.split(' ')[1]
                dirpath = os.path.join(current_directory, directory)
                if os.path.exists(dirpath):
                    os.rmdir(dirpath)
                    client_socket.send('202 Directory deleted.\r\n'.encode())
                else:
                    client_socket.send('550 Directory not found.\r\n'.encode())
            elif command == 'MKD':
                directory = data.split(' ')[1]
                dirpath = os.path.join(current_directory, directory)
                os.makedirs(dirpath, exist_ok=True)
                client_socket.send('202 Directory created.\r\n'.encode())
            elif command == 'PWD':
                client_socket.send(f'257 "{current_directory}" is the current directory.\r\n'.encode())
            elif command == 'LIST':
                client_socket.send('200 Here is the directory listing.\r\n'.encode())
                file_list = os.listdir(current_directory)
                for file in file_list:
                    file_info = os.stat(os.path.join(current_directory, file))
                    permissions = 'rwxrwxrwx'
                    file_permissions = ''
                    for i in range(9):
                        if not file_info.st_mode & (1 << (8 - i)):
                            file_permissions += '-'
                        else:
                            file_permissions += permissions[i]
                    file_size = file_info.st_size
                    client_socket.send(f'{file_permissions} {file_size} {file}\r\n'.encode())
                client_socket.send('.\r\n'.encode())
            elif command == 'HELP':
                client_socket.send('214 Help message.\r\n'.encode())
            else:
                client_socket.send('500 Syntax error, command unrecognized.\r\n'.encode())

# Create FTP server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f'FTP server listening on {HOST}:{PORT}')

# Handle client connections using threads
while True:
    client_socket, client_address = server_socket.accept()
    clients[client_socket] = client_address
    threading.Thread(target=handle_client, args=(client_socket,)).start()

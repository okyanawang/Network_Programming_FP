import socket

# Constants
HOST = '127.0.0.1'  # Host address
PORT = 2022  # Port number
BUFFER_SIZE = 1024  # Buffer size for receiving data

# Function to receive and print server response
def receive_response(sock):
    response = sock.recv(BUFFER_SIZE).decode()
    print(response)

# Create FTP client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Receive and print welcome message
receive_response(client_socket)

while True:
    # Get user input
    command = input('Enter command: ')

    # Send command to server
    client_socket.send(command.encode())

    # Receive and print server response
    receive_response(client_socket)

    # Check if QUIT command was entered
    if command.upper() == 'QUIT':
        break

# Close the client socket
client_socket.close()

import socket

# Define server address and port
SERVER_ADDRESS = '127.0.0.1' # Probably will need to use something different for sure
SERVER_PORT = 8000

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

# Keep listening for user inputs until 'quit' command is entered
while True:
    # Get user input
    command = input('Enter command: ')

    # Send command to the server
    client_socket.send(command.encode())

    # Receive response from the server
    response = client_socket.recv(1024).decode()

    # Print the response from the server
    print(response)

    # Check if the user wants to quit
    if command == 'exit':
        break

# Close the socket
client_socket.close()

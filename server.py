import socket
import threading
import pickle
import sys

# Global variables
database = {}  # Dictionary to store customer information
cohorts = {}  # Dictionary to store cohort information
port_bank = 8000  # Port number for bank communication
port_cohort = 8001  # Port number for cohort communication


# Function to handle incoming messages from customers
def handle_customer_message(message, address, sock):
    global database, cohorts

    tokens = message.split()
    command = tokens[0]
    customer_name = tokens[1]

    if command == "open":
        if customer_name in database:
            response = "FAILURE"
        else:
            balance = tokens[2]
            ip_address = tokens[3]
            port_bank = int(tokens[4])
            port_cohort = int(tokens[5])
            database[customer_name] = (balance, ip_address, port_bank, port_cohort)
            response = "SUCCESS"
        sock.sendto(response.encode(), address)

    elif command == "new-cohort":
        if customer_name not in database:
            response = "FAILURE"
        else:
            n = int(tokens[2])
            if n > len(database):
                response = "FAILURE"
            else:
                cohort = [customer_name]
                available_customers = set(database.keys()) - set(cohort)
                for i in range(n - 1):
                    new_member = available_customers.pop()
                    cohort.append(new_member)
                cohorts[customer_name] = cohort
                response = "SUCCESS\n" + "\n".join([f"{name} {ip} {pb} {pc}" for (name, (b, ip, pb, pc)) in
                                                    [(customer_name, database[customer_name])] + [(name, database[name])
                                                                                                  for name in
                                                                                                  cohort[1:]]])
        sock.sendto(response.encode(), address)

    elif command == "delete-cohort":
        if customer_name not in database or customer_name not in cohorts:
            response = "FAILURE"
        else:
            cohort = cohorts[customer_name]
            for member in cohort:
                if member != customer_name:
                    ip = database[member][1]
                    port = database[member][3]
                    sock.sendto("DELETE".encode(), (ip, port))
                    del database[member]
                    del cohorts[member]
            del cohorts[customer_name]
            response = "SUCCESS"
        sock.sendto(response.encode(), address)

    elif command == "exit":
        if customer_name not in database:
            response = "FAILURE"
        else:
            del database[customer_name]
            if customer_name in cohorts:
                del cohorts[customer_name]
            response = "SUCCESS"
        sock.sendto(response.encode(), address)


# Function to listen for incoming messages from customers
def listen_for_customers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("localhost", port_bank))
        while True:
            data, address = sock.recvfrom(1024)
            message = data.decode()
            threading.Thread(target=handle_customer_message, args=(message, address, sock)).start()


# Function to handle incoming messages from cohorts
def handle_cohort_message(message, address, sock):
    global cohorts

    tokens = message.split()
    command = tokens[0]
    customer_name = tokens[1]

    if command == "DELETE":
        del cohorts[customer_name]

    sock.sendto("ACK".encode(), address)


class Bank:
    def __init__(self):
        self.accounts = {}
        self.transactions = []

    def add_account(self, account_id, balance):
        self.accounts[account_id] = balance

    def process_transaction(self, transaction):
        if transaction.type == "deposit":
            self.accounts[transaction.account_id] += transaction.amount
        elif transaction.type == "withdraw":
            if self.accounts[transaction.account_id] < transaction.amount:
                return "Insufficient funds"
            self.accounts[transaction.account_id] -= transaction.amount
        self.transactions.append(transaction)
        return "Transaction successful"

    def process_message(self, message):
        transaction = message.transaction
        result = self.process_transaction(transaction)
        response = {
            "type": "response",
            "transaction_id": message.transaction_id,
            "result": result
        }
        return response

    def listen(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f"Listening on {host}:{port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    data = conn.recv(1024)
                    if not data:
                        continue
                    message = pickle.loads(data)
                    response = self.process_message(message)
                    conn.sendall(pickle.dumps(response))


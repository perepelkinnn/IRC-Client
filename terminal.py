import main
import time
import threading


class Terminal():
    def __init__(self):
        pass

    def read(self, handler):
        while True:
            handler.input.append(input())
            time.sleep(0.1)

    def write(self, handler):
        while True:
            if handler.output:
                print(handler.output.pop(0))
            time.sleep(0.1)

    def update_users(self, handler):
        while True:
            if handler.names:
                print(handler.names)
                handler.names = []
            time.sleep(1)


server = input('Enter server: ')
nick = input('Enter your nickname: ')

client = main.Client(server, nick)
client.handler.run()
client.login()
terminal = Terminal()

threading.Thread(target=terminal.read, args=[client.handler]).start()
threading.Thread(target=terminal.write, args=[client.handler]).start()
threading.Thread(target=terminal.update_users, args=[client.handler]).start()

while True:
    time.sleep(1)

import socket
import threading
import time

is_running = False
__channel__ = None


class Config:
    def __init__(self, server, nick):
        self.server = server
        self.port = 6667
        self.nickname = nick
        self.hostname = socket.gethostname()
        self.target = None


class Commands:
    def privmsg(target, msg):
        return 'PRIVMSG {} : {}\r\n'.format(target, msg)

    def user(nickname, hostname, server):
        return 'USER {} {} {} {}\r\n'.format(nickname, hostname,
                                             server,   nickname)

    def join(channel):
        global __channel__
        __channel__ = channel
        return 'JOIN {}\r\n'.format(channel)

    def part(channel):
        global __channel__
        __channel__ = None
        return 'PART {}\r\n'.format(channel)

    def pong(socket):
        return'PONG {}\r\n'.format(socket)

    def nick(nickname):
        global __channel__
        if __channel__:
            return 'NICK {}\r\n'.format(nickname) + Commands.names()
        return 'NICK {}\r\n'.format(nickname)

    def quit(msg=''):
        return 'QUIT {}\r\n'.format(msg)

    def names():
        global __channel__
        if __channel__:
            return 'NAMES {}\r\n'.format(__channel__)


class Socket:
    def __init__(self, server, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(server, port)

    def connect(self, socket, port):
        try:
            self.socket.connect((socket, port))
        except Exception:
            raise ConnectionAbortedError

    def get(self):
        return self.socket.recv(1024).decode('utf-8')

    def send(self, cmd):
        if cmd:
            self.socket.sendall(cmd.encode('utf-8'))


class Handler:
    def __init__(self, socket):
        self.socket = socket
        self.input = []
        self.output = []
        self.names = []
        self.__temp_names__ = []

    def handle_input(self):
        while is_running:
            if len(self.input):
                cmd, *arg = self.input.pop(0).split()
                try:
                    func = getattr(Commands, cmd)
                    self.socket.send(func(*arg))
                except AttributeError:
                    print('Unknown command')
            time.sleep(0.1)

    def handle_output(self):
        other = ''
        msg = ''
        while is_running:
            if '\r\n' in msg:
                msg, other = msg.split('\r\n', 1)
                out = self.parse_msg(*self.pre_parse_msg(msg))
                if out:
                    self.output.append(out)
            else:
                other = msg + self.socket.get()
            msg = other
            time.sleep(0.01)

    def pre_parse_msg(self, raw):
        prefix = ''
        if raw[0] == ':':
            prefix, raw = raw[1:].split(' ', 1)
        if raw.find(' :') != -1:
            raw, trailing = raw.split(' :', 1)
            args = raw.split()
            args.append(trailing)
        else:
            args = raw.split()
        command = args.pop(0)

        return prefix, command, args

    def parse_msg(self, prefix, command, args):
        nick = prefix.split('!', 1)[0] if '!' in prefix else prefix
        if command == 'JOIN':
            self.socket.send(Commands.names())
            return '<{}> join to channel'.format(nick)
        if command == 'PART' or command == 'QUIT':
            self.socket.send(Commands.names())
            return '<{}> left from channel'.format(nick)
        if command == 'PRIVMSG' or command == 'NOTICE':
            return '<{}> {}'.format(nick, args[1])
        if command == 'PING':
            self.socket.send(Commands.pong(args[0]))
        if command == '353':
            self.__temp_names__.extend(args[3].split(' '))
        if command == '366':
            self.names = self.sort_nicks(self.__temp_names__)
            self.__temp_names__ = []

    def sort_nicks(self, names):
        sorted_names = []
        non_op = []
        for name in names:
            if name[0] == '@':
                sorted_names.append(name)
            else:
                non_op.append(name)
        sorted_names.extend(non_op)
        return sorted_names

    def run(self):
        threading.Thread(target=self.handle_input).start()
        threading.Thread(target=self.handle_output).start()


class Client:
    def __init__(self, server, nick, socket=None):
        global is_running
        is_running = True
        self.config = Config(server, nick)
        if socket:
            self.socket = socket
        else:
            self.socket = Socket(self.config.server, self.config.port)
        self.handler = Handler(self.socket)

    def login(self):
        self.socket.send(Commands.user(self.config.nickname,
                                       self.config.hostname,
                                       self.config.server))
        self.socket.send(Commands.nick(self.config.nickname))

    def join(self, channel):
        self.config.target = channel
        self.socket.send(Commands.join(channel))

    def left(self, channel):
        self.config.target = None
        self.socket.send(Commands.part(channel))

    def change_nick(self, nick):
        self.config.nickname = nick
        self.socket.send(Commands.nick(self.config.nickname))

    def send_message(self, msg):
        if len(msg) > 255:
            self.send_message(msg[:255])
            self.send_message(msg[255:])
        else:
            self.socket.send(Commands.privmsg(self.config.target, msg))
        return '<{}> {}'.format(self.config.nickname, msg)

    def stop(self):
        global is_running
        self.socket.send(Commands.quit())
        self.socket.socket.shutdown(0)
        is_running = False
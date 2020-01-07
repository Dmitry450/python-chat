import socket
import sys
import threading

class InputThread(threading.Thread):

    def __init__(self, prompt=""):
        threading.Thread.__init__(self)
        self.input = ""
        self.prompt = prompt
    
    def run(self):
        while True:
            try:
                self.input = input(self.prompt)
            except KeyboardInterrupt:
                break
    
    def read(self):
        i = self.input
        self.input = ""
        return i
        

class Client:

    def __init__(self, addr: str):
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)
        ip, port = addr.split(':', 1)
        try:
            port = int(port)
        except ValueError:
            print("Invalid port: "+port)
            raise SystemExit(-1)
        try:
            self.socket.connect((ip, port))
        except ConnectionRefusedError:
            print("Unable to connect to server: connection refused")
            raise SystemExit(-2)
        except OSError:
            print("Unable to connect to server: no route to host")
            raise SystemExit(-2)
    
    def recv(self, bufferize=1024):
        try:
            return self.socket.recv(bufferize)
        except BlockingIOError:
            return b''

    def send(self, data: bytes):
        self.socket.send(data)

i = 0

readonly = False
name = ""

while i < len(sys.argv):
    if sys.argv[i] == '--read-only':
        readonly = True
    if sys.argv[i] in ('-n, --name'):
        i += 1
        name = sys.argv[i]
    if sys.argv[i] in ('-h', '--help'):
        print("Usage: client [OPTIONS]\n\n" \
              "-h, --help - print help\n" \
              "--read-only - connect to server and only read messages, no sendin\n" \
              "-n, --name <name> - set your name (if not given, using ip)")
        raise SystemExit(0)
    i += 1

c = Client(input("Address: "))

if name:
    c.send(bytes("command:setname "+name, 'utf-8'))

inp = InputThread(">>>")
inp.start()

while True:
    d = str(c.recv(), 'utf-8')
    print(("\r" if d else '')+d+('\n>>>' if d else ''), end = '')
    sys.stdin.buffer.flush()
    c.socket.setblocking(0)
    if not readonly:
        i = inp.read()
        if i == "quit": break
        if i:
            c.send(bytes("message:"+i, 'utf-8'))

import socket
import time
import threading

class ConnectionThread(threading.Thread):
    """
    When several users connect to us, it is too difficult to work 
    with them all in one thread, so we will creating new thread for each new connection. 
    It will wait for data from the client, work with it, 
    and when the client disconnects, the thread stops and the server will delete it.
    """
    
    def __init__(self, connection, addr, data_parser):
        threading.Thread.__init__(self)
        self.connection = connection
        self.addr = addr
        self.disconnected = False
        self.data_parser = data_parser
    
    def run(self):
        while True:
            data = None
            try:
                data = self.connection.recv(1024)
            except:
                data = b''
            if not data:
                break
            else:
                self.data_parser(self, data)
        print(time.strftime('[SERVER] [%D|%H:%M:%S] - disconnected: '+self.addr, time.localtime(time.time())))
        self.disconnected = True

class Server:
    """
    This class is essentially a simple set of methods for working with clients. 
    You just need to create an instance, passing the function of data processing as an argument, 
    then call the "initialize" method, telling which port to listen on and how 
    much maximum users can connect. After that, the server will be ready to work.
    """

    def __init__(self, parse_data_func):
        self.socket = socket.socket(socket.AF_INET,
                            socket.SOCK_STREAM,
                            proto=socket.IPPROTO_IP)
        self.socket.setblocking(0)
        self.connections = []
        self.max_connected = 0
        self.parse_data_func = parse_data_func
    
    def initialise(self, port = 43210, max_connected = 1):
        self.socket.bind(('0.0.0.0', port))
        self.socket.listen(max_connected)
        self.max_connected = max_connected
    
    def readyToConnection(self):
        """
        Checks, is anywho is trying to connect to server.
        raises BlockingIOError if no
        """
        if len(self.connections) == self.max_connected:
            return
        conn, addr = self.socket.accept()
        print(time.strftime('[SERVER] [%D|%H:%M:%S] - connection: ', time.localtime(time.time())), end='')
        print(addr[0])
        conn.send(b"Welcome to server")
        connthr = ConnectionThread(conn, addr[0], self.parse_data_func)
        connthr.start()
        self.connections.append(connthr)
    
    def sendDataToConnections(self, data: bytes, excludeConnections=[]):
        """
        Sends given data (bytes) to every connected client
        """
        for conn in self.connections:
            if conn in excludeConnections:
                continue
            try:
                conn.connection.send(data)
            except ConnectionResetError:
                print(time.strftime('[SERVER] [%D|%H:%M:%S] - disconnected: ', time.localtime(time.time())), end='')
                print(conn.addr)
                conn.disconnected = True
    
    def checkConnections(self):
        """
        Checks connections to find closed
        """
        for conn in self.connections:
            if conn.disconnected:
                conn.join()
                self.connections.remove(conn)
    
    def autoupdate(self):
        """
        Automatically calls readyToConnection() and checkConnections()
        All BlockingIOErrors will be catched
        """
        try:
            s.readyToConnection()
        except BlockingIOError:
            pass # If there aren't new connections
        s.checkConnections()

# Using test

###########################

PORT = 5050
MAX_CONNECTED = 8

###########################

data_to_send = []

def cmd(connthr, txt):
    args = txt.split()
    if args[0] == "setname":
        print("["+connthr.addr+"] setted name to \'"+args[1]+"\'")
        connthr.addr = args[1]

def parseData(connthr, data):
    d = str(data, 'utf-8')
    t, arg = d.split(':')
    if t == "message":
        print(time.strftime('['+connthr.addr+'] [%D|%H:%M:%S] - message: '+arg, time.localtime(time.time())))
        data_to_send.append({"data": bytes(f"[{connthr.addr}]: "+arg, 'utf-8'), "excludeConnections":[connthr]})
    elif t == "command":
        cmd(connthr, arg)

s = Server(parseData)
s.initialise(max_connected=MAX_CONNECTED, port=PORT)
print("Starting the server. Use ^C to stop it.")
try:
    while True:
        s.autoupdate()
        for d in data_to_send:
            s.sendDataToConnections(data=d["data"], excludeConnections=d["excludeConnections"])
            data_to_send.remove(d)
except KeyboardInterrupt:
    print("\rServer stopped")
    raise SystemExit(0)

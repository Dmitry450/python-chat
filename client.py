#!/usr/bin/python3 
# -*- coding: utf-8 -*-

import socket
import sys
import json
import threading
import curses
from curses import wrapper

import locale
locale.setlocale(locale.LC_ALL, ('RU', "UTF8"))

class Client:

    def __init__(self, addr: str):
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)
        ip, port = addr.split(':', 1) # addr format: 255.255.255.255:5050
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

class App:

    def __init__(self, client: Client, name = ""):
        self.line = 0
        self.col = 0
        self.msg_line = 0
        self.buffer = ""
        self.updated = False
        self.client = client
        self.client.socket.setblocking(0)
        if name:
            self.client.send(bytes("command:setname "+name, 'utf-8'))
    
    def init(self, screen):
        curses.curs_set(False)
        curses.cbreak()
        curses.noecho()
        screen.nodelay(1)
        screen.bkgd(' ')
        screen.keypad(True)
        self.msg_pad = curses.newpad(1000, 100) # Mmm, yeah, this is good solution
    
    def addMessage(self, msg):
        self.msg_pad.addstr(self.msg_line, 0, msg)
        self.msg_line += 1

    def checkMessages(self):
        msg = str(c.recv(), 'utf-8')
        if msg:
            self.addMessage(msg)

    def main(self, screen):
        self.init(screen)
        while True:
            self.msg_pad.refresh(self.line, self.col, 1, 1, int(curses.LINES/2), curses.COLS-2)
            self.checkMessages()
            k = None
            try:
                k = screen.get_wch()
            except curses.error:
                pass # No input
            if k == curses.KEY_UP:
                if self.line > 0: self.line -= 1
            elif k == curses.KEY_DOWN:
                if self.line < 999: self.line += 1
            elif k == curses.KEY_LEFT:
                if self.col > 0: self.col -= 1
            elif k == curses.KEY_RIGHT:
                if self.col < 999: self.col += 1
            elif k == curses.KEY_RESIZE:
                curses.update_lines_cols()
            elif k == "\n" or k == curses.KEY_ENTER:
                if self.buffer:
                    self.client.send(bytes("message:"+self.buffer, 'utf-8'))
                    self.addMessage("[you]: "+self.buffer)
                self.buffer = ""
                self.updated = True
            elif k == curses.KEY_BACKSPACE:
                self.buffer = self.buffer[0:len(self.buffer)-1] 
                self.updated = True
            elif k is not None:
                self.updated = True
                self.buffer += k
            
            screen.addstr(curses.LINES-2, 2, "Your message: "+self.buffer)
            screen.refresh()
            if self.updated:
                self.updated = False
                screen.clear()

i = 0

name = ""

while i < len(sys.argv):
    if sys.argv[i] in ('-n, --name'):
        i += 1
        name = sys.argv[i]
    if sys.argv[i] in ('-h', '--help'):
        print("Usage: client [OPTIONS]\n\n" \
              "-h, --help - print help\n" \
              "-n, --name <name> - set your name (if not given, using ip)")
        raise SystemExit(0)
    i += 1

if name:
    file = open("client_conf.json", 'w')
    json.dump({'name':name}, file)
else:
    try:
        file = open("client_conf.json")
        name = json.load(file)["name"]
    except:
        pass

c = Client(input("Address: "))

app = App(c, name)

wrapper(app.main)
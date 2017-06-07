import zmq
import signal
import sys

port = 5556
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://172.18.0.1:%s" % port)
socket.send_string("hello")

def handler(signal, frame):
    print('exiting...')
    socket.disconnect("tcp://172.18.0.1:%s" % port)
    exit()

signal.signal(signal.SIGINT, handler)

reward = socket.recv()
next_input = socket.recv()

while True:
    socket.send_string("a") # your attempt to solve the current task
    reward = socket.recv()
    next_input = socket.recv()
    print(reward)

signal.pause()
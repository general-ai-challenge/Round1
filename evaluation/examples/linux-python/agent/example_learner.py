import zmq
import signal
import sys
import getopt


host = '172.18.0.1'
port = 5556

try:
    opts, args = getopt.getopt(sys.argv[1:], 'a:p:', ['address=', 'port='])
except getopt.GetoptError:
    print("Error reading options. Usage:")
    print("  example_learner.py [-a <address> -p <port>]")
    sys.exit(2)

for opt, arg in opts:
    if opt in ('-a', '--address'):
        host = arg
    elif opt in ('-p', '--port'):
        try:
            port = int(arg)
            if port < 1 or port > 65535:
                raise ValueError("Out of range")
        except ValueError:
            print("Invalid port number: %s" % arg)
            sys.exit(2)

context = zmq.Context()
socket = context.socket(zmq.PAIR)

address = "tcp://%s:%s" % (host, port)
print("Connecting to %s" % address)
sys.stdout.flush()

socket.connect(address)
socket.send_string("hello")


def handler(signal, frame):
    print('exiting...')
    socket.disconnect(address)
    exit()


signal.signal(signal.SIGINT, handler)

reward = socket.recv()
next_input = socket.recv()

while True:
    socket.send_string("a")  # your attempt to solve the current task
    reward = socket.recv()
    next_input = socket.recv()
    print(reward)

signal.pause()

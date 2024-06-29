import json
import zmq

class MQueue:
    MODE_PUBLISHER  = 0
    MODE_SUBSCRIBER = 1
    socket = None
    mode = None

    def __init__(self, mode: int):
        self.mode = mode
        match self.mode:
            case self.MODE_PUBLISHER:
                self.socket = zmq.Context().socket(zmq.PUB)
                self.socket.bind("tcp://*:5555")
            case self.MODE_SUBSCRIBER:
                self.socket = zmq.Context().socket(zmq.SUB)
                self.socket.connect("tcp://localhost:5555")
                self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def send_message(self, message):
        self.socket.send_string(json.dumps(message))

    def listen(self, on_message):
        while True:
            msg = self.socket.recv_string()
            on_message(json.loads(msg))
import socket
import json
import threading
from PyQt6.QtCore import QThread, pyqtSignal

UDP_PORT = 5554
TCP_PORT = 5555

class DiscoveryListener(QThread):
    """Student portal uses this to find the Teacher automatically"""
    teacher_found = pyqtSignal(dict)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', UDP_PORT))
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                info = json.loads(data.decode('utf-8'))
                if info.get("type") == "PROCTORA_BROADCAST":
                    info["ip"] = addr[0]
                    self.teacher_found.emit(info)
            except: continue

class TeacherBroadcaster(threading.Thread):
    """Teacher app shouts 'I am here' and lists all available classes"""
    def __init__(self, class_list):
        super().__init__()
        self.class_list = class_list
        self.running = True
        self.daemon = True

    def stop(self):
        """Stop the broadcaster thread"""
        self.running = False

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = json.dumps({
            "type": "PROCTORA_BROADCAST",
            "available_classes": self.class_list 
        }).encode('utf-8')
        while self.running:
            sock.sendto(message, ('<broadcast>', UDP_PORT))
            threading.Event().wait(2)

def network_request(ip, request_dict):
    """Universal TCP requester for login and data fetching"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect((ip, TCP_PORT))
        client.send(json.dumps(request_dict).encode('utf-8'))
        response = client.recv(1024 * 100).decode('utf-8') 
        client.close()
        return json.loads(response)
    except:
        return {"status": "error", "message": "Teacher disconnected"}
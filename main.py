import socket, threading, queue, time
from pyllamacpp.model import Model

class HandleRequests(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.requests = queue.Queue()
        self.model = Model(ggml_model='ggml-alpaca-7b-q4.bin', n_ctx=512, n_threads=8)

    def run(self):
        while True:
            prompt, callback_fn = self.requests.get()
            self.model.generate(prompt, n_predict=500, new_text_callback=callback_fn, temp=0.7, top_p=0.75, top_k=100, repeat_penalty=2)
            callback_fn("\r\n")

class Client(threading.Thread):
    def __init__(self, clientsocket, addr, model):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr
        self.model = model

        self.main_prompt = "You are ChatBot, who responds to instructions with high accuracy and in-depth knowledge. You expand on topics where you can but always follow the user's instructions."
        self.room_history = []
    
    def build_prompt(self):
        prompt = self.main_prompt + "\n\n"

        for i in self.room_history:
            if i["side"] == "user":
                prompt += "### Instruction: \n" + i["text"] + "\n\n"
            else:
                prompt += "### Response: \n" + i["text"] + "\n\n"
        
        return prompt + "### Response:\n"

    def get_message(self):
        # Telnet sends char-by-char, but netcat sends line-by-line
        self.clientsocket.send("\r\n> ".encode('utf-8'))
        message = ""
        while True:
            char = self.clientsocket.recv(1024)
            char = char.decode('utf-8')
            if char == '\r':
                continue
            elif char == '\x08':
                message = message[:-1]
            else:
                message += char

                if message.endswith("\n"):
                    break

        return message
    
    def callback(self, text):
        # Send generated text to client
        text = text.replace("ÔÇÖ", "'")
        self.clientsocket.send(text.replace("\n", "\r\n").encode('utf-8'))
        self.current_response += text
        print(f"Sent {len(text)} chars to {self.addr}...")

    def run(self):
        while True:
            try:
                # Get message from client
                msg = self.get_message().replace("\r", "").replace("\n", "")
                
                # Build prompt for model
                self.room_history.append({"side": "user", "text": msg})
                prompt = self.build_prompt()
                self.current_response = ""

                # Alert user if busy
                if not self.model.requests.empty():
                    self.clientsocket.send(f"Queue not empty ({self.model.requests.qsize()}), you may need to wait a while...".encode('utf-8'))

                # Send prompt to model
                self.model.requests.put((prompt, self.callback))

                # Wait till finished
                while not "\r\n" in self.current_response:
                    time.sleep(0.1)
                
                # Add model response to history
                self.current_response = self.current_response.replace("\r\n", "")
                if self.current_response == "":
                    self.clientsocket.send("Model gave no response...".encode('utf-8'))
                    self.current_response = "..."

                self.room_history.append({"side": "bot", "text": self.current_response})

            except:
                print(self.addr, " disconnected")
                break

        self.clientsocket.close()

if __name__ == "__main__":
    # Load model
    model = HandleRequests()
    model.start()
    print("Model loaded")

    # Start server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ""
    port = 8080

    s.bind((host, port))
    s.listen(5)

    print(f"Server started on {host}:{port}...")

    while True:
        try:
            c, addr = s.accept()
            print('Got connection from', addr)
            Client(c, addr, model).start()
        except:
            print("Server closed")
            break

    s.close()
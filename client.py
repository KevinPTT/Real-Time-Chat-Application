import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser, QLineEdit, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext

# Common variables
HOST = '127.0.0.1'
PORT = 1234

# Define constants or variables used in the Tkinter part of the code
LIGHT_BACKGROUND = '#404040'
LIGHT_FOREGROUND = 'white'  # Changed text color to white

FONT = ("Helvetica", 17)
BUTTON_FONT = ("Helvetica", 15)
SMALL_FONT = ("Helvetica", 13)

# Define these variables
scrolledtext = scrolledtext
username_textbox = None
username_button = None
message_textbox = None
message_box = None

class ChatClient(QObject):
    message_received = pyqtSignal(str)

    def __init__(self, host, port, nickname):
        super().__init__()
        self.nickname = nickname
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.running = True

    def send_message(self, message):
        self.sock.send(message.encode('utf-8'))

    def receive_messages(self):
        while self.running:
            message = self.sock.recv(1024).decode('utf-8')
            if message == 'NICK':
                self.sock.send(self.nickname.encode('utf-8'))
            else:
                self.message_received.emit(message)

    def stop(self):
        self.running = False
        self.sock.close()

class ChatWindow(QMainWindow):
    closing = pyqtSignal()

    def __init__(self, client):
        QMainWindow.__init__(self)
        self.client = client
        self.client_thread = QThread()
        self.client.moveToThread(self.client_thread)
        self.client_thread.started.connect(self.client.receive_messages)
        self.client.message_received.connect(self.update_chat_history)

        self.setWindowTitle("Chat")
        self.setGeometry(100, 100, 400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.chat_history = QTextBrowser()
        self.chat_history.setStyleSheet(f'background-color: {LIGHT_BACKGROUND}; color: {LIGHT_FOREGROUND};')
        layout.addWidget(self.chat_history)

        self.message_input = QLineEdit()
        self.message_input.setStyleSheet(f'background-color: {LIGHT_BACKGROUND}; color: {LIGHT_FOREGROUND};')
        layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(f'background-color: {LIGHT_BACKGROUND}; color: {LIGHT_FOREGROUND};')
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.central_widget.setLayout(layout)

        self.client_thread.start()

    def send_message(self):
        message = self.message_input.text()
        if message:
            self.client.send_message(message)
            self.message_input.clear()

    @pyqtSlot(str)
    def update_chat_history(self, message):
        self.chat_history.append(message)

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()

def tkinter_window():
    root = tk.Tk()
    root.withdraw()

    root.destroy()

def tkinter_client():
    root = tk.Tk()
    root.geometry("600x600")
    root.title("Messenger Client")
    root.resizable(False, False)
    root.configure(bg=LIGHT_BACKGROUND)

    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=4)
    root.grid_rowconfigure(2, weight=1)

    top_frame = tk.Frame(root, width=600, height=100, bg=LIGHT_BACKGROUND)
    top_frame.grid(row=0, column=0, sticky=tk.NSEW)

    middle_frame = tk.Frame(root, width=600, height=400, bg=LIGHT_BACKGROUND)
    middle_frame.grid(row=1, column=0, sticky=tk.NSEW)

    bottom_frame = tk.Frame(root, width=600, height=100, bg=LIGHT_BACKGROUND)
    bottom_frame.grid(row=2, column=0, sticky=tk.NSEW)

    username_label = tk.Label(top_frame, text="Enter username:", font=FONT, bg=LIGHT_BACKGROUND, fg=LIGHT_FOREGROUND)
    username_label.pack(side=tk.LEFT, padx=10)

    username_textbox = tk.Entry(top_frame, font=FONT, bg=LIGHT_BACKGROUND, fg=LIGHT_FOREGROUND, width=23)
    username_textbox.pack(side=tk.LEFT)

    username_button = tk.Button(top_frame, text="Join", font=BUTTON_FONT, bg='#FFFF00', fg=LIGHT_FOREGROUND, command=tkinter_connect)
    username_button.pack(side=tk.LEFT, padx=15)

    message_textbox = tk.Entry(bottom_frame, font=FONT, bg=LIGHT_BACKGROUND, fg=LIGHT_FOREGROUND, width=38)
    message_textbox.pack(side=tk.LEFT, padx=10)

    message_button = tk.Button(bottom_frame, text="Send", font=BUTTON_FONT, bg='#FFFF00', fg=LIGHT_FOREGROUND, command=tkinter_send_message)
    message_button.pack(side=tk.LEFT, padx=10)

    message_box = scrolledtext.ScrolledText(middle_frame, font=SMALL_FONT, bg=LIGHT_BACKGROUND, fg=LIGHT_FOREGROUND, width=67, height=26.5)
    message_box.config(state=tk.DISABLED)
    message_box.pack(side=tk.TOP)

    root.mainloop()

def tkinter_connect():
    global tk_client
    tk_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    username = username_textbox.get()
    if username != '':
        try:
            tk_client.connect((HOST, PORT))
            print("Successfully connected to the server")
            add_tk_message("[SERVER] Successfully connected to the server")
            tk_client.sendall(username.encode())
            threading.Thread(target=tkinter_listen_for_messages).start()
            username_textbox.config(state=tk.DISABLED)
            username_button.config(state=tk.DISABLED)
        except ConnectionRefusedError:
            messagebox.showerror("Connection Error", "Server refused connection.")
    else:
        messagebox.showerror("Invalid username", "Username cannot be empty")

def tkinter_send_message():
    message = message_textbox.get()
    if message != '':
        tk_client.sendall(message.encode())
        message_textbox.delete(0, len(message))
    else:
        messagebox.showerror("Empty message", "Message cannot be empty")

def tkinter_add_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

def tkinter_listen_for_messages():
    while True:
        try:
            message = tk_client.recv(2048).decode('utf-8')
            if message:
                username = message.split("~")[0]
                content = message.split('~')[1]
                tkinter_add_message(f"[{username}] {content}")
            else:
                messagebox.showerror("Error", "Message received from the client is empty")
        except ConnectionResetError:
            print("Connection to the server lost.")
            tkinter_add_message("[SERVER] Connection to the server lost.")
            break

def add_tk_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

def main():
    app = QApplication(sys.argv)
    client = ChatClient(HOST, PORT, 'YourNickname')
    chat_window = ChatWindow(client)
    chat_window.show()

    threading.Thread(target=tkinter_window).start()

    def on_close():
        client.stop()
        app.quit()

    chat_window.closing.connect(on_close)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

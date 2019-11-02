import sys
import main
import threading
import time
from PyQt5.QtWidgets import (QApplication, QAction, QWidget, QTextEdit,
                             QPushButton,  QGridLayout, QMenuBar, QLineEdit,
                             QMenu, QInputDialog, QMessageBox, QListWidget,
                             QFileDialog)
from PyQt5.QtGui import QIcon

TITLE = 'Pink Milk (IRC Client)'


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.client = None
        threading.Thread(target=self.run_writing).start()
        threading.Thread(target=self.update_users).start()

    def initUI(self):
        self.setWindowTitle(TITLE)
        self.setMinimumSize(700, 400)
        self.setWindowIcon(QIcon('Resources/icon.png'))

        self.init_messeges()
        self.init_users()
        self.init_botton_send()
        self.init_input()
        self.init_menu_bar()
        self.set_grid()

        self.show()

    def set_grid(self):
        grid = QGridLayout()
        grid.setMenuBar(self.menu_bar)
        grid.addWidget(self.users, 0, 2)
        grid.addWidget(self.messages, 0, 0, 1, 2)
        grid.addWidget(self.input_line, 1, 0, 1, 2)
        grid.addWidget(self.botton_send, 1, 2)
        self.setLayout(grid)

    def init_messeges(self):
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)

    def init_users(self):
        self.users = QListWidget()
        self.users.setFixedWidth(150)

    def init_botton_send(self):
        self.botton_send = QPushButton()
        self.botton_send.setFixedWidth(150)
        self.botton_send.setText('Send')
        self.botton_send.clicked.connect(self.on_click_send_button)

    def init_input(self):
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.on_click_send_button)

    def init_menu_bar(self):
        self.menu_bar = QMenuBar()

        menu_irc = QMenu('IRC', self.menu_bar)

        startAction = QAction('Start', self)
        startAction.triggered.connect(self.show_dialog_connect)
        stopAction = QAction('Stop', self)
        stopAction.triggered.connect(self.stop)

        menu_irc.addAction(startAction)
        menu_irc.addAction(stopAction)
        self.menu_bar.addMenu(menu_irc)

        menu_options = QMenu('Options', self.menu_bar)

        joinAction = QAction('Join', self)
        joinAction.triggered.connect(self.show_dialog_join)
        leftAction = QAction('Left', self)
        leftAction.triggered.connect(self.show_dialog_left)
        nickAction = QAction('Nick', self)
        nickAction.triggered.connect(self.show_dialog_nick)
        saveLogAction = QAction('Save log', self)
        saveLogAction.triggered.connect(self.show_dialog_unload)

        menu_options.addAction(joinAction)
        menu_options.addAction(leftAction)
        menu_options.addAction(nickAction)
        menu_options.addAction(saveLogAction)
        self.menu_bar.addMenu(menu_options)

    def on_click_send_button(self):
        if not self.client:
            QMessageBox.warning(
                self, ' ', 'You need to connect to the server!')
            return
        if not self.client.config.target:
            QMessageBox.warning(self, ' ', 'You need to join to the channel!')
            return
        if not self.input_line.text():
            return
        line = self.client.send_message(self.input_line.text())
        self.messages.append(line)
        self.input_line.clear()
        self.input_line.setFocus()

    def show_dialog_connect(self):
        if self.client:
            QMessageBox.warning(self, ' ', 'You are already connected!')
            return
        server, res_1 = QInputDialog.getText(self, ' ', 'Enter server')
        nick, res_2 = QInputDialog.getText(self, ' ', 'Enter nickname')
        if res_1 and res_2:
            self.client = main.Client(server, nick)
            self.client.handler.run()
            self.client.login()

    def show_dialog_join(self):
        if self.client:
            channel, res = QInputDialog.getText(self, ' ', 'Enter channel')
            if res:
                self.client.join(channel)
        else:
            QMessageBox.warning(
                self, ' ', 'You need to connect to the server!')

    def show_dialog_unload(self):
        path, mask = QFileDialog.getSaveFileName(
            self, "Open Dialog", "", "*.txt")
        if path:
            with open(path, 'w', encoding='UTF-8') as file:
                file.write(self.messages.toPlainText())
        else:
            QMessageBox.warning(
                self, ' ', 'You need to change file!')

    def show_dialog_left(self):
        if self.client and self.client.config.target:
            channel, res = QInputDialog.getText(self, ' ', 'Enter channel')
            if res:
                self.client.left(channel)
        else:
            QMessageBox.warning(
                self, ' ', 'You need to join to the channel!')

    def show_dialog_nick(self):
        if self.client:
            nick, res = QInputDialog.getText(self, ' ', 'Enter new nick')
            if res:
                self.client.change_nick(nick)
        else:
            QMessageBox.warning(
                self, ' ', 'You need to connect to the server!')

    def run_writing(self):
        while True:
            if self.client:
                if len(self.client.handler.output):
                    self.messages.append(self.client.handler.output.pop(0))
            time.sleep(0.1)

    def update_users(self):
        while True:
            if self.client:
                if self.client.handler.names:
                    self.users.clear()
                    for nick in self.client.handler.names:
                        self.users.addItem(nick)
                    self.client.handler.names = []
            time.sleep(1)

    def stop(self):
        if not self.client:
            QMessageBox.warning(self, ' ', 'You are already stopped!')
            return
        self.client.stop()
        self.client = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game


def extract_command(msg: str):
    if msg.startswith("/"):
        return (msg.split()[0], " ".join(msg.split()[1::]))


@dataclass
class Client:
    ip: str = "localhost"
    port: int = 8888
    uid: str = None
    name: str = None
    room: str = None
    con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    commands: dict[str, Any] = field(default_factory=dict)
    is_game: bool = False
    game: Game = None

    # command system
    def command(self, cmd: str):
        def inner_command(f):
            self.commands[cmd] = f
            return f

        return inner_command

    # calls function based on command from client
    def dispath(self, cmd: str, *args, **kwargs):
        if cmd in self.commands:
            self.commands[cmd](self, *args, **kwargs)
        else:
            self.cprint(f"got command {cmd} with data {args[0]}")

    @property
    def tag(self):
        return self.name or self.uid

    def cprint(self, text: str) -> None:
        if self.is_game:
            print(text)
        else:
            print(f"\r{' '*40}\r{text}\n{self.tag} {self.room or ''} msg: ", end="")

    def connect(self) -> Client:
        self.con.connect((self.ip, self.port))
        Thread(target=self.listen, daemon=True).start()
        return self

    def listen(self):
        cprint = self.cprint
        while True:
            msg: str = self.con.recv(1024).decode("utf-8")
            if msg:
                if cmd := extract_command(msg):
                    self.dispath(cmd[0], cmd[1])
                else:
                    cprint(f"server: {msg}")
            else:
                continue

    def send(self, msg):
        if msg:
            self.con.send(msg.encode("utf-8"))

    def chat(self):
        while True:
            msg = input(f"{self.tag} {self.room or ''} msg: ").encode("utf-8")
            if msg:
                self.con.send(msg)

    def test(self):
        for i in range(1000000):
            self.con.send(str(i).encode("utf-8"))
            sleep(0.0001)


if __name__ == "__main__":
    client = Client()

    @client.command("/info")
    def info(client, data):
        client.cprint(data)

    @client.command("/relay")
    def info(client, data):
        client.cprint(data)

    @client.command("/uid")
    def set_uid(client, data):
        client.uid = data
        client.cprint(f"connected with uid {data}")

    @client.command("/name")
    def set_name(client, data):
        client.name = data
        client.cprint(f"changed name to {data}")

    @client.command("/room")
    def set_name(client, data):
        client.room = data
        client.cprint(f"connected to room {data}")

    client.connect().chat()

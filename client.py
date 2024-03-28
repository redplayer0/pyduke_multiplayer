from __future__ import annotations

import socket
from dataclasses import dataclass, field
from functools import partial
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game import Game


def make_decorator(game: Game, client: Client):
    def wrapper(func):
        part = partial(func, game, client)
        client.handlers[func.__name__] = part
        return part

    return wrapper


@dataclass
class Client:
    ip: str = "localhost"
    port: int = 8888
    con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    uid: str = None
    name: str = None
    room: str = None
    is_game: bool = False
    # msgs: deque[tuple[str, str]] = field(default_factory=deque)
    handlers: dict[str, Any] = field(default_factory=dict)

    def dispatch(self, msgs):
        for msg in msgs:
            if msg[0] in self.handlers:
                self.handlers[msg[0]](msg[1])
            else:
                self.cprint(f"error with msg: {msg}")

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
            data: str = self.con.recv(1024).decode("utf-8")
            if data:
                msgs = [
                    tuple(sub.strip().split(":")) for sub in data.strip().split("|")
                ][:-1]
                self.dispatch(msgs)
                cprint(f"[recieved] {data}")
            else:
                continue

    def send(self, msg):
        if msg:
            msg += "|"
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


# if __name__ == "__main__":
#     client = Client()

#     @client.command("/info")
#     def info(client, data):
#         client.cprint(data)

#     @client.command("/relay")
#     def info(client, data):
#         client.cprint(data)

#     @client.command("/uid")
#     def set_uid(client, data):
#         client.uid = data
#         client.cprint(f"connected with uid {data}")

#     @client.command("/name")
#     def set_name(client, data):
#         client.name = data
#         client.cprint(f"changed name to {data}")

#     @client.command("/room")
#     def set_name(client, data):
#         client.room = data
#         client.cprint(f"connected to room {data}")

#     client.connect().chat()

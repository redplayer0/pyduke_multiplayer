from __future__ import annotations

import socket
from dataclasses import dataclass, field
from functools import lru_cache, partial
from threading import Thread
from typing import Any
from uuid import uuid4


def remove_from_list(inlist: list[Any], x: Any) -> list[Any]:
    if x in inlist:
        inlist.remove(x)
    else:
        print(f"item: {x} not found in list: {inlist}")
    return inlist


def sprint(text: str) -> None:
    print(f"\r{' '*40}\r{text}\nserver message: ", end="")


@dataclass(slots=True)
class Server:
    ip: str = "localhost"
    port: int = 8888
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clients: list[ServerClient] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    handlers: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.ip, self.port))

    @property
    def num_clients(self):
        return len(self.clients)

    @property
    def num_rooms(self):
        return len(self.rooms)

    @property
    def stats(self):
        return f"clients:{self.num_clients}|rooms:{self.num_rooms}"

    # creates the socket and start the listener in a thread
    def start(self) -> Server:
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(2)
        print("listening...")
        Thread(target=self.listener, daemon=True).start()
        return self

    # awaits new connections
    def listener(self):
        while True:
            conn, addr = self.sock.accept()
            client = self.new_client(conn, addr)
            Thread(target=self.handle_client, args=[client]).start()

    # awaits client msgs message_size=1024 chars
    def handle_client(self, client):
        while True:
            data: str = client.conn.recv(1024).decode("utf-8")
            if data:
                msgs = [
                    tuple(sub.strip().split(":")) for sub in data.strip().split("|")
                ][:-1]
                self.dispatch(msgs, client)
                sprint(f"[recieved] {data}")
            else:
                break

        self.remove_client(client)
        sprint(f"{client.tag} disconnected")

    # Commands section
    # command decorator

    def handle(self, func):
        part = partial(func, self)
        self.handlers[func.__name__] = part
        return part

    def dispatch(self, msgs, client: ServerClient):
        for msg in msgs:
            if msg[0] in self.handlers:
                self.handlers[msg[0]](msg[1], client)
            else:
                sprint(f"error with msg: {msg}")

    # client section
    def new_client(self, conn, addr) -> ServerClient:
        client = ServerClient(conn, addr)
        self.clients.append(client)
        sprint(f"new client connected with add:{client.addr} and uid:{client.uid}")
        return client

    def remove_client(self, client: ServerClient) -> Server:
        if client.room:
            remove_from_list(client.room.clients, client)
        remove_from_list(self.clients, client)
        for room in self.rooms:
            if room.is_empty:
                remove_from_list(self.rooms, client.room)

    def client_exit_room(self, client: ServerClient):
        if room := client.room:
            remove_from_list(room.clients, client)
            if room.is_empty:
                remove_from_list(self.rooms, room)
        client.room = None

    # room section
    @lru_cache(30)
    def get_room(self, name: str) -> Room:
        for room in self.rooms:
            if room.name == name:
                return room

        room = Room(name=name, max_clients=2)
        self.rooms.append(room)
        sprint(f"room {room.name} was created")
        return room

    def join_room(self, client: ServerClient, room_name: str):
        room = self.get_room(room_name)
        if room.is_full:
            client.send("info:room is full")
            return
        if client.room == room:
            client.send("info:you are already in this room")
            return
        elif client.room is not None:
            client.room.remove_client(client)
            if client.room.is_empty:
                remove_from_list(self.rooms, client.room)
                sprint(f"room {client.room.name} was deleted")

        room.clients.append(client)
        client.room = room
        client.send(f"room:{room_name}")
        if room.is_full:
            self.room_send(room, "room_ready:")

    # message section
    def send_to(self, client: ServerClient, msg):
        client.send(msg)

    def broadcast(self, msg, exclude=None):
        for c in self.clients:
            if c is not exclude:
                c.send(msg)

    def room_send(self, room: Room, msg: str):
        for c in room.clients:
            c.send(msg)

    def console(self):
        while True:
            msg = input(f"\r{' '*40}\rserver message: ")
            match msg:
                case "exit":
                    exit()
                case "stats":
                    sprint(self.stats)
                case "names":
                    sprint(self.names)
                case "rooms":
                    for room in self.rooms:
                        sprint(
                            f"[{room.name}] {room.num_clients}/{room.max_clients} host:{room.host.tag} members:{[c.tag for c in room.clients]}"
                        )
                case _:
                    self.broadcast(msg)


def extract_command(msg: str):
    if msg.startswith("/"):
        return (msg.split()[0], " ".join(msg.split()[1::]))


@dataclass
class ServerClient:
    conn: str
    addr: str
    uid: str = None
    name: str = None
    room: Room = None

    def __post_init__(self):
        self.uid = uuid4().hex[:7]

    @property
    def tag(self):
        return self.name or self.uid

    def send(self, msg):
        msg += "|"
        self.conn.send(msg.encode("utf-8"))

    def room_broadcast(self, msg):
        for c in self.room.clients:
            if c is not self:
                c.send(msg)


@dataclass
class Room:
    name: str = None
    clients: list[ServerClient] = field(default_factory=list)
    max_clients: int = 10
    _host: ServerClient = None

    @property
    def host(self):
        return self._host or self.clients[0]

    @property
    def num_clients(self):
        return len(self.clients)

    @property
    def is_full(self):
        return len(self.clients) >= self.max_clients

    @property
    def is_empty(self):
        return len(self.clients) == 0

    @property
    def info(self):
        return f"{self.name} {self.num_clients}/{self.max_clients}"

    def remove_client(self, client: ServerClient) -> Room:
        remove_from_list(self.clients, client)
        return self


if __name__ == "__main__":
    server = Server()

    # commands
    @server.handle
    def name(server: Server, data: str, client: ServerClient):
        client.name = data
        client.send(f"name:{data}")

    @server.handle
    def a(server: Server, data: str, client: ServerClient):
        # TODO
        server.broadcast(f"relay:{client.tag}: {data}", client)
        sprint(f"{client.tag} sent: {data}")

    @server.handle
    def uid(server: Server, data: str, client: ServerClient):
        client.send(f"uid:{client.uid}")

    @server.handle
    def room(server: Server, room: str, client: ServerClient):
        server.join_room(client, room)

    @server.handle
    def w(server: Server, data: str, client: ServerClient):
        target = data.split()[0]
        msg = data.replace(target, "").strip()
        for c in server.clients:
            if c.uid == target or c.name == target:
                # TODO
                c.send(f"info:{client.tag} says: {msg}")

    @server.handle
    def get_rooms(server: Server, data: str, client: ServerClient):
        rooms = ",".join([room.info for room in server.rooms])
        client.send(f"rooms:{rooms}")

    @server.handle
    def positions(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"positions:{data}")

    @server.handle
    def move(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"move:{data}")

    @server.handle
    def spawn_opponent(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"spawn_opponent:{data}")

    @server.handle
    def ready(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            if client == client.room.host:
                client.send("move:")

    @server.handle
    def lost(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            for c in client.room.clients:
                if c != client:
                    c.send("won:")
                else:
                    c.send("lost:")

    @server.handle
    def exit_room(server: Server, data: str, client: ServerClient):
        server.client_exit_room(client)

    server.start().console()

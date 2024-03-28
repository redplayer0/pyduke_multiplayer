from __future__ import annotations

import socket
from dataclasses import dataclass, field
from functools import lru_cache
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
    commands: dict[str, Any] = field(default_factory=dict)

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
            msg: str = client.conn.recv(1024).decode("utf-8")
            if msg:
                if cmd := extract_command(msg):
                    self.dispath(cmd[0], cmd[1], client)
                else:
                    sprint(f"{client.tag} sent: {msg}")
            else:
                break

        self.remove_client(client)
        sprint(f"{client.tag} disconnected")

    # Commands section
    # command decorator
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
            sprint(f"got command {cmd} with data {args[0]}")

    # client section
    def new_client(self, conn, addr) -> ServerClient:
        client = ServerClient(conn, addr)
        self.clients.append(client)
        # client.send(f"/info {client.uid}")
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
            client.send("/info room is full")
            return
        if client.room == room:
            client.send("/info you are already in this room")
            return
        elif client.room is not None:
            client.room.remove_client(client)
            if client.room.is_empty:
                remove_from_list(self.rooms, client.room)
                sprint(f"room {client.room.name} was deleted")

        room.clients.append(client)
        client.room = room
        client.send(f"/room {room_name}")
        if room.is_full:
            self.room_send(room, "/room_ready")

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
    server = Server().start()

    # commands
    @server.command("/name")
    def set_name(server: Server, data: str, client):
        client.name = data
        client.send(f"/name {data}")

    @server.command("/a")
    def broadcast(server: Server, data: str, client):
        server.broadcast(f"/relay {client.tag}: {data}", client)
        sprint(f"{client.tag} sent: {data}")

    @server.command("/uid")
    def send_uid(server: Server, data: str, client):
        client.send(f"/uid {client.uid}")

    @server.command("/room")
    def join_room(server: Server, room: str, client):
        server.join_room(client, room)

    @server.command("/w")
    def whisper(server: Server, data: str, client):
        target = data.split()[0]
        msg = data.replace(target, "").strip()
        for c in server.clients:
            if c.uid == target or c.name == target:
                c.send(f"/info {client.tag} says: {msg}")

    @server.command("/get_rooms")
    def get_rooms(server: Server, data: str, client):
        rooms = ",".join([room.info for room in server.rooms])
        client.send(f"/rooms {rooms}")

    @server.command("/positions")
    def send_positions(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"/positions {data}")

    @server.command("/move")
    def send_move(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"/move {data}")

    @server.command("/spawn_opponent")
    def send_spawn(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            client.room_broadcast(f"/spawn_opponent {data}")

    @server.command("/ready")
    def send_ready(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            if client == client.room.host:
                client.send("/move")

    @server.command("/lost")
    def send_win(server: Server, data: str, client: ServerClient):
        if client.room and client.room.is_full and client.room.max_clients == 2:
            for c in client.room.clients:
                if c != client:
                    c.send("/won")
                else:
                    c.send("/lost")

    @server.command("/exit_room")
    def exit_room(server: Server, data: str, client: ServerClient):
        server.client_exit_room(client)

    server.console()

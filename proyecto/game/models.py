from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import random


@dataclass
class Operation:
    a: int
    b: int
    operator: str
    answer: int

    @classmethod
    def generate(cls, difficulty: int = 1) -> "Operation":
        if difficulty <= 1:
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            operator = random.choice(["+", "-"])
        else:
            a = random.randint(5, 25)
            b = random.randint(2, 15)
            operator = random.choice(["+", "-", "*"])

        if operator == "+":
            answer = a + b
        elif operator == "-":
            answer = a - b
        else:
            answer = a * b

        return cls(a=a, b=b, operator=operator, answer=answer)

    def text(self) -> str:
        return f"{self.a} {self.operator} {self.b}"


@dataclass
class Enemy:
    name: str
    damage: int = 3


@dataclass
class Room:
    id: int
    kind: str
    description: str = ""
    gold: int = 0
    enemy: Optional[Enemy] = None
    explored: bool = False
    solved: bool = False

    def is_enemy(self) -> bool:
        return self.kind == "enemy"

    def is_treasure(self) -> bool:
        return self.kind == "treasure"

    def is_empty(self) -> bool:
        return self.kind == "empty"

    def is_wall(self) -> bool:
        return self.kind == "wall"


@dataclass
class Player:
    health: int = 9
    gold: int = 0
    enemies_defeated: int = 0
    rooms_cleared: int = 0
    current_room: int = 0

    def lose_health(self, amount: int) -> None:
        self.health = max(0, self.health - amount)

    def gain_gold(self, amount: int) -> None:
        self.gold += amount

    def defeat_enemy(self) -> None:
        self.enemies_defeated += 1

    def clear_room(self) -> None:
        self.rooms_cleared += 1

    def is_alive(self) -> bool:
        return self.health > 0


@dataclass
class Map:
    rooms: List[Room]

    @classmethod
    def generate(cls, stages: int = 6) -> "Map":
        room_types = ["empty", "treasure", "enemy", "wall"]
        rooms: List[Room] = []

        for idx in range(stages):
            kind = random.choice(room_types)
            gold = 0
            enemy = None

            if idx == 0 and kind == "wall":
                kind = "empty"

            if kind == "treasure":
                gold = random.randint(8, 16)
                description = "Has encontrado un cofre con oro antiguo."
            elif kind == "enemy":
                enemy = Enemy(name=f"Guardia {idx + 1}", damage=3)
                description = "Un enemigo te bloquea el paso. Debes responder bien para vencerlo."
            elif kind == "wall":
                description = "Un muro sólido bloquea el paso."
            else:
                description = "Una habitación vacía y silenciosa."

            rooms.append(Room(id=idx, kind=kind, description=description, gold=gold, enemy=enemy))

        walkable_rooms = [room for room in rooms if room.kind != "wall"]
        if stages > 1 and len(walkable_rooms) < 2:
            for room in rooms:
                if room.kind == "wall":
                    room.kind = "empty"
                    room.description = "Una habitación vacía y silenciosa."
                    walkable_rooms.append(room)
                    if len(walkable_rooms) == 2:
                        break

        if stages > 1 and not any(room.kind not in {"wall", "enemy"} for room in rooms):
            room = next(room for room in rooms if room.kind != "wall")
            room.kind = "empty"
            room.enemy = None
            room.description = "Una habitación vacía y silenciosa."

        if not any(room.kind == "enemy" for room in rooms):
            room = next(room for room in rooms if room.kind != "wall")
            room.kind = "enemy"
            room.description = "Un enemigo te bloquea el paso. Debes responder bien para vencerlo."
            room.enemy = Enemy(name="Guardia del castillo", damage=3)

        if stages > 1 and not any(room.kind == "treasure" for room in rooms):
            room = next(room for room in rooms if room.kind not in {"wall", "enemy"})
            room.kind = "treasure"
            room.description = "Has encontrado un cofre con oro antiguo."
            room.gold = random.randint(10, 18)

        return cls(rooms=rooms)

    def current_room(self, index: int) -> Room:
        return self.rooms[index]


@dataclass
class Game:
    config: dict
    player: Player
    map: Map
    status: str = "playing"
    current_operation: Optional[Operation] = None
    time_started: Optional[float] = None
    answer_input: str = ""
    last_event: str = ""

    @classmethod
    def create(cls, config: dict) -> "Game":
        player = Player(health=config["vida_inicial"])
        mapa = Map.generate(stages=config["etapas"])
        mapa.current_room(0).explored = True
        return cls(config=config, player=player, map=mapa)

    def current_room(self) -> Room:
        return self.map.current_room(self.player.current_room)

    def generate_enemy_operation(self) -> None:
        self.current_operation = Operation.generate(difficulty=1 if self.player.current_room < 3 else 2)
        self.time_started = __import__("time").time()

    def handle_enemy_answer(self, answer_value: str) -> None:
        if self.current_operation is None:
            return

        try:
            respuesta = int(answer_value)
        except ValueError:
            self.player.lose_health(self.config["penalizacion_error"])
            self.status = "lost" if not self.player.is_alive() else "playing"
            self.current_operation = None
            self.time_started = None
            return

        if respuesta == self.current_operation.answer:
            self.player.defeat_enemy()
            self.current_room().solved = True
            self.current_room().enemy = None
            self.current_room().kind = "empty"
            self.current_operation = None
            self.time_started = None
            self.status = "playing"
            return

        self.player.lose_health(self.config["penalizacion_error"])
        self.current_operation = None
        self.time_started = None
        self.status = "lost" if not self.player.is_alive() else "playing"

    def time_left(self) -> float:
        if self.time_started is None:
            return float(self.config["tiempo_limite"])
        elapsed = __import__("time").time() - self.time_started
        return max(0.0, float(self.config["tiempo_limite"]) - elapsed)

    def apply_time_expired(self) -> None:
        if self.current_operation is None:
            return
        self.player.lose_health(self.config["danio_enemigo"])
        self.current_operation = None
        self.time_started = None
        self.status = "lost" if not self.player.is_alive() else "playing"

    def collect_treasure(self) -> None:
        room = self.current_room()
        if room.kind == "treasure":
            self.player.gain_gold(room.gold)
            room.kind = "empty"
            room.gold = 0
            room.explored = True
            self.player.clear_room()

    def move_next_room(self) -> None:
        if self.player.current_room >= len(self.map.rooms) - 1:
            self.status = "won" if self.player.gold >= self.config["oro_objetivo"] else "playing"
            return

        next_index = self.player.current_room + 1
        next_room = self.map.current_room(next_index)
        if next_room.is_wall():
            next_room.explored = True
            self.last_event = "Un muro bloquea el paso. Has descubierto su ubicación, pero sigues en esta habitación."
            return

        self.player.current_room = next_index
        next_room.explored = True
        self.last_event = ""
        self.player.clear_room()
        self.current_operation = None
        self.time_started = None

    def check_end_state(self) -> None:
        if self.player.health <= 0:
            self.status = "lost"
            return

        if self.player.gold >= self.config["oro_objetivo"]:
            self.status = "won"

    def reset(self, config: dict | None = None) -> None:
        if config is not None:
            self.config = config
        self.player = Player(health=self.config["vida_inicial"])
        self.map = Map.generate(stages=self.config["etapas"])
        self.status = "playing"
        self.current_operation = None
        self.time_started = None
        self.answer_input = ""
        self.last_event = ""
        self.map.current_room(0).explored = True

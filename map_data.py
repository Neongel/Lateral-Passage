import json
import os


class MapData:
    def __init__(self, width=20, height=15, tile_size=40):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.start = {"x": 1, "y": height - 2}
        self.end = {"x": width - 2, "y": height - 2}
        self.traps = []
        self.ground = []
        self.doors = []
        self.info = {
            "name": "未命名关卡",
            "author": "未知",
            "version": "0.0.0",
            "description": ""
        }
        self.bg_color = "#87CEEB"
        self._generate_ground()

    def _generate_ground(self):
        self.ground = []
        for x in range(self.width):
            self.ground.append({"x": x, "y": self.height - 1})

    def to_dict(self):
        return {
            "info": self.info,
            "width": self.width,
            "height": self.height,
            "tile_size": self.tile_size,
            "bg_color": self.bg_color,
            "start": self.start,
            "end": self.end,
            "traps": self.traps,
            "ground": self.ground,
            "doors": self.doors
        }

    @classmethod
    def from_dict(cls, data):
        m = cls(data.get("width", 20), data.get("height", 15), data.get("tile_size", 40))
        m.start = data.get("start", m.start)
        m.end = data.get("end", m.end)
        m.traps = data.get("traps", [])
        m.ground = data.get("ground", m.ground)
        m.doors = data.get("doors", [])
        m.info = data.get("info", m.info)
        m.bg_color = data.get("bg_color", m.bg_color)
        return m

    def save(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_ground_tiles(self):
        return self.ground

    def is_ground(self, x, y):
        return any(g["x"] == x and g["y"] == y for g in self.ground)

    def add_ground(self, x, y):
        if not self.is_ground(x, y):
            self.ground.append({"x": x, "y": y})

    def remove_ground(self, x, y):
        self.ground = [g for g in self.ground if not (g["x"] == x and g["y"] == y)]

    def add_trap(self, x, y, trap_type="spike"):
        if not any(t["x"] == x and t["y"] == y for t in self.traps):
            self.traps.append({"x": x, "y": y, "type": trap_type})

    def remove_trap(self, x, y):
        self.traps = [t for t in self.traps if not (t["x"] == x and t["y"] == y)]

    def add_door(self, x, y):
        if not any(d["x"] == x and d["y"] == y for d in self.doors):
            self.doors.append({"x": x, "y": y, "type": "door", "open": False})

    def remove_door(self, x, y):
        self.doors = [d for d in self.doors if not (d["x"] == x and d["y"] == y)]

    def get_door(self, x, y):
        for d in self.doors:
            if d["x"] == x and d["y"] == y:
                return d
        return None

    def toggle_door(self, x, y):
        door = self.get_door(x, y)
        if door:
            door["open"] = not door["open"]

    def set_start(self, x, y):
        self.start = {"x": x, "y": y}

    def set_end(self, x, y):
        self.end = {"x": x, "y": y}

    def get_tile_rect(self, x, y):
        return (
            x * self.tile_size,
            y * self.tile_size,
            self.tile_size,
            self.tile_size
        )

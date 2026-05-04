import json
import os
import pygame
from lupa import LuaRuntime


class Item:
    def __init__(self, data, base_path="data/items"):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.category = data.get("category", "block")
        self.texture_path = data.get("texture", "")
        self.solid = data.get("solid", True)
        self.has_lua = data.get("has_lua", False)
        self.lua_script = data.get("lua_script", "")
        self.properties = data.get("properties", {})
        self.base_path = base_path
        self.texture = None
        self._load_texture()
        self.lua = None
        self._on_touch_func = None
        self._on_update_func = None
        if self.has_lua and self.lua_script:
            self._load_lua()

    def _load_texture(self):
        if self.texture_path:
            full_path = os.path.join(self.base_path, os.path.basename(self.texture_path))
            if os.path.exists(full_path):
                try:
                    self.texture = pygame.image.load(full_path)
                except Exception:
                    self.texture = None

    def _load_lua(self):
        if self.lua_script:
            lua_path = os.path.join(self.base_path, self.lua_script)
            if os.path.exists(lua_path):
                try:
                    self.lua = LuaRuntime(unpack_returned_tuples=True)
                    with open(lua_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    self.lua.execute(code)
                    self._on_touch_func = self.lua.globals().on_touch
                    self._on_update_func = self.lua.globals().on_update
                except Exception as e:
                    print(f"加载Lua脚本失败 {self.lua_script}: {e}")
                    self.lua = None

    def on_touch(self, player, map_data):
        if self._on_touch_func is not None:
            try:
                lua_player = self.lua.table(
                    alive=player.alive,
                    won=getattr(player, 'won', False)
                )
                lua_item = self.lua.table(
                    id=self.id,
                    name=self.name,
                    properties=self.properties
                )
                result = self._on_touch_func(lua_player, lua_item, map_data.to_dict())
                if lua_player.alive is not None:
                    player.alive = lua_player.alive
                if lua_player.won:
                    player.won = True
                return result
            except Exception as e:
                print(f"Lua on_touch 错误: {e}")
        return False

    def on_update(self, dt):
        if self._on_update_func is not None:
            try:
                self._on_update_func(self.properties, dt)
            except Exception as e:
                print(f"Lua on_update 错误: {e}")

    def draw(self, screen, rect):
        if self.texture:
            screen.blit(self.texture, rect)
            return True
        return False


class ItemManager:
    def __init__(self, items_dir="data/items"):
        self.items_dir = items_dir
        self.items = {}
        self._load_all_items()

    def _load_all_items(self):
        if not os.path.exists(self.items_dir):
            return
        for filename in os.listdir(self.items_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.items_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    item = Item(data, self.items_dir)
                    self.items[item.id] = item
                except Exception as e:
                    print(f"加载物品失败 {filename}: {e}")

    def get_item(self, item_id):
        return self.items.get(item_id)

    def get_all_items(self):
        return list(self.items.values())

    def get_item_ids(self):
        return list(self.items.keys())

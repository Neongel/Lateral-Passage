import pygame
import tkinter as tk
from tkinter import filedialog
from map_data import MapData
from utils import get_font, TextInput
from item_manager import ItemManager
from lang import _


class MapEditor:
    def __init__(self, screen):
        self.screen = screen
        self.map_data = MapData()
        self.item_manager = ItemManager()
        self.tool = "ground"
        self.tool_names = {}
        self.tool_textures = {}
        self._load_tool_data()
        self.font = get_font(24)
        self.small_font = get_font(18)
        self.title_font = get_font(22)
        self.grid_offset_x = 10
        self.grid_offset_y = 60
        self.buttons = []
        self._init_buttons()
        self.mouse_down = False
        self.mouse_button = None
        self.last_placed_pos = None
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom = 1.0
        self.zoom_min = 0.3
        self.zoom_max = 3.0
        self.popup = None
        self.popup_type = None
        self.text_inputs = {}
        self.text_input_focus = None
        self.close_btn_img = None
        self._load_close_btn()

    def _load_tool_data(self):
        for item_id, item in self.item_manager.items.items():
            self.tool_names[item_id] = item.name
            self.tool_textures[item_id] = item.texture

    def _load_close_btn(self):
        try:
            self.close_btn_img = pygame.image.load("assets/img/close_btn.png")
            self.close_btn_img = pygame.transform.scale(self.close_btn_img, (28, 28))
        except Exception:
            self.close_btn_img = None

    def _init_buttons(self):
        sw, sh = self.screen.get_size()
        self.buttons = []
        self.buttons.append({"rect": pygame.Rect(10, 10, 100, 35), "action": "map_props", "text": _("editor.map_props")})
        current_name = _(f"items.{self.tool}", self.tool_names.get(self.tool, self.tool))
        self.buttons.append({"rect": pygame.Rect(120, 10, 160, 35), "action": "item_select", "text": f"{_('editor.item_select')}[{current_name}]"})
        self.buttons.append({"rect": pygame.Rect(sw - 320, 10, 90, 35), "action": "export", "text": _("editor.export")})
        self.buttons.append({"rect": pygame.Rect(sw - 220, 10, 90, 35), "action": "import", "text": _("editor.import")})
        self.buttons.append({"rect": pygame.Rect(sw - 120, 10, 110, 35), "action": "test", "text": _("editor.test")})

    def _update_item_button(self):
        for btn in self.buttons:
            if btn.get("action") == "item_select":
                current_name = _(f"items.{self.tool}", self.tool_names.get(self.tool, self.tool))
                btn["text"] = f"{_('editor.item_select')}[{current_name}]"

    def _get_grid_pos(self, mx, my):
        grid_x = int((mx - self.grid_offset_x - self.pan_offset_x) / (self.map_data.tile_size * self.zoom))
        grid_y = int((my - self.grid_offset_y - self.pan_offset_y) / (self.map_data.tile_size * self.zoom))
        if 0 <= grid_x < self.map_data.width and 0 <= grid_y < self.map_data.height:
            return grid_x, grid_y
        return None

    def _place_tool(self, grid_x, grid_y):
        item = self.item_manager.get_item(self.tool)
        if not item:
            return

        # Check if position already has any item
        has_ground = self.map_data.is_ground(grid_x, grid_y)
        has_trap = any(t["x"] == grid_x and t["y"] == grid_y for t in self.map_data.traps)
        has_door = any(d["x"] == grid_x and d["y"] == grid_y for d in self.map_data.doors)
        is_start = self.map_data.start["x"] == grid_x and self.map_data.start["y"] == grid_y
        is_end = self.map_data.end["x"] == grid_x and self.map_data.end["y"] == grid_y

        if has_ground or has_trap or has_door or is_start or is_end:
            return

        if item.category == "block" and item.solid:
            self.map_data.add_ground(grid_x, grid_y)
        elif item.id == "start":
            self.map_data.set_start(grid_x, grid_y)
        elif item.id == "end":
            self.map_data.set_end(grid_x, grid_y)
        elif item.category == "trap":
            self.map_data.add_trap(grid_x, grid_y, item.id)
        elif item.id == "door":
            self.map_data.add_door(grid_x, grid_y)

    def _erase_at(self, grid_x, grid_y):
        self.map_data.remove_ground(grid_x, grid_y)
        self.map_data.remove_trap(grid_x, grid_y)
        self.map_data.remove_door(grid_x, grid_y)

    def handle_event(self, event):
        if self.popup:
            return self._handle_popup_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            for btn in self.buttons:
                if btn["rect"].collidepoint(mx, my):
                    action = btn.get("action")
                    if action == "map_props":
                        self._open_map_props()
                        return None
                    elif action == "item_select":
                        self._open_item_select()
                        return None
                    elif action == "export":
                        self._export_map()
                    elif action == "import":
                        result = self._import_map()
                        if result:
                            return result
                    elif action == "test":
                        return {"action": "test", "map_data": self.map_data}
                    return None

            pos = self._get_grid_pos(mx, my)
            if pos:
                self.mouse_down = True
                self.mouse_button = event.button
                self.last_placed_pos = pos
                if event.button == 1:
                    self._place_tool(pos[0], pos[1])
                elif event.button == 3:
                    self._erase_at(pos[0], pos[1])
                elif event.button == 2:
                    self.panning = True
                    self.pan_start_x = mx
                    self.pan_start_y = my

        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down = False
            self.mouse_button = None
            self.last_placed_pos = None
            if event.button == 2:
                self.panning = False

        elif event.type == pygame.MOUSEMOTION:
            if self.panning:
                dx = event.pos[0] - self.pan_start_x
                dy = event.pos[1] - self.pan_start_y
                self.pan_offset_x += dx
                self.pan_offset_y += dy
                self.pan_start_x = event.pos[0]
                self.pan_start_y = event.pos[1]
            elif self.mouse_down and self.mouse_button == 1:
                pos = self._get_grid_pos(event.pos[0], event.pos[1])
                if pos and pos != self.last_placed_pos:
                    self._place_tool(pos[0], pos[1])
                    self.last_placed_pos = pos
            elif self.mouse_down and self.mouse_button == 3:
                pos = self._get_grid_pos(event.pos[0], event.pos[1])
                if pos and pos != self.last_placed_pos:
                    self._erase_at(pos[0], pos[1])
                    self.last_placed_pos = pos

        if event.type == pygame.MOUSEWHEEL:
            old_zoom = self.zoom
            if event.y > 0:
                self.zoom = min(self.zoom * 1.1, self.zoom_max)
            elif event.y < 0:
                self.zoom = max(self.zoom / 1.1, self.zoom_min)
            if old_zoom != self.zoom:
                mx, my = pygame.mouse.get_pos()
                self.pan_offset_x = mx - (mx - self.pan_offset_x) * (self.zoom / old_zoom)
                self.pan_offset_y = my - (my - self.pan_offset_y) * (self.zoom / old_zoom)
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"

        return None

    def _open_map_props(self):
        self.popup_type = "map_props"
        self.popup = {
            "rect": pygame.Rect(150, 80, 600, 520),
            "close_rect": pygame.Rect(712, 88, 28, 28)
        }
        self.text_inputs = {
            "name": TextInput(self.map_data.info.get("name", "")),
            "author": TextInput(self.map_data.info.get("author", "")),
            "description": TextInput(self.map_data.info.get("description", "")),
            "width": TextInput(str(self.map_data.width)),
            "height": TextInput(str(self.map_data.height)),
            "bg_color": TextInput(self.map_data.bg_color),
        }
        self.text_input_focus = None
        pygame.key.start_text_input()

    def _open_item_select(self):
        self.popup_type = "item_select"
        item_count = len(self.item_manager.items)
        rows = (item_count + 2) // 3
        popup_h = 80 + rows * 90
        self.popup = {
            "rect": pygame.Rect(250, 120, 400, popup_h),
            "close_rect": pygame.Rect(612, 128, 28, 28)
        }

    def _handle_popup_event(self, event):
        popup = self.popup
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if popup["close_rect"].collidepoint(mx, my):
                self._close_popup()
                return None
            if not popup["rect"].collidepoint(mx, my):
                self._close_popup()
                return None

            if self.popup_type == "map_props":
                return self._handle_map_props_click(mx, my)
            elif self.popup_type == "item_select":
                return self._handle_item_select_click(mx, my)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close_popup()
                return None
            if self.popup_type == "map_props" and self.text_input_focus:
                handled = self.text_inputs[self.text_input_focus].handle_event(event)
                if handled:
                    return None

        elif event.type in (pygame.TEXTEDITING, pygame.TEXTINPUT):
            if self.popup_type == "map_props" and self.text_input_focus:
                handled = self.text_inputs[self.text_input_focus].handle_event(event)
                if handled:
                    return None

        return None

    def _handle_map_props_click(self, mx, my):
        popup_rect = self.popup["rect"]
        base_x = popup_rect.x
        base_y = popup_rect.y

        fields = [
            ("name", pygame.Rect(base_x + 100, base_y + 80, 420, 30)),
            ("author", pygame.Rect(base_x + 100, base_y + 125, 420, 30)),
            ("description", pygame.Rect(base_x + 100, base_y + 170, 420, 90)),
            ("width", pygame.Rect(base_x + 100, base_y + 330, 420, 30)),
            ("height", pygame.Rect(base_x + 100, base_y + 375, 420, 30)),
            ("bg_color", pygame.Rect(base_x + 100, base_y + 420, 420, 30)),
        ]
        clicked_field = None
        for field, rect in fields:
            if rect.collidepoint(mx, my):
                clicked_field = field
                self.text_input_focus = field
                if field == "description":
                    rel_y = my - rect.y
                    line_idx = max(0, min(rel_y // 24, 2))
                    lines = self.text_inputs[field].text.split("\n")
                    if line_idx < len(lines):
                        self.text_inputs[field].cursor = sum(len(l) + 1 for l in lines[:line_idx])
                    else:
                        self.text_inputs[field].cursor = len(self.text_inputs[field].text)
                else:
                    rel_x = mx - rect.x
                    text_len = len(self.text_inputs[field].text)
                    char_w = self.small_font.size("中")[0]
                    self.text_inputs[field].cursor = min(text_len, max(0, rel_x // char_w))
                return None

        if clicked_field is None:
            self.text_input_focus = None

        save_rect = pygame.Rect(popup_rect.centerx - 100, popup_rect.bottom - 55, 200, 40)
        if save_rect.collidepoint(mx, my):
            self._save_map_props()
            self._close_popup()
        return None

    def _save_map_props(self):
        self.map_data.info["name"] = self.text_inputs["name"].text
        self.map_data.info["author"] = self.text_inputs["author"].text
        self.map_data.info["description"] = self.text_inputs["description"].text
        try:
            new_w = int(self.text_inputs["width"].text)
            new_h = int(self.text_inputs["height"].text)
            if 5 <= new_w <= 100 and 5 <= new_h <= 100:
                old_w, old_h = self.map_data.width, self.map_data.height
                self.map_data.width = new_w
                self.map_data.height = new_h
                if new_w < old_w or new_h < old_h:
                    self.map_data.ground = [g for g in self.map_data.ground if g["x"] < new_w and g["y"] < new_h]
                    self.map_data.traps = [t for t in self.map_data.traps if t["x"] < new_w and t["y"] < new_h]
                    if self.map_data.start["x"] >= new_w:
                        self.map_data.start["x"] = new_w - 1
                    if self.map_data.start["y"] >= new_h:
                        self.map_data.start["y"] = new_h - 1
                    if self.map_data.end["x"] >= new_w:
                        self.map_data.end["x"] = new_w - 1
                    if self.map_data.end["y"] >= new_h:
                        self.map_data.end["y"] = new_h - 1
        except ValueError:
            pass
        self.map_data.bg_color = self.text_inputs["bg_color"].text or "#87CEEB"

    def _handle_item_select_click(self, mx, my):
        popup_rect = self.popup["rect"]
        start_x = popup_rect.x + 30
        start_y = popup_rect.y + 70
        gap = 90
        for i, (item_id, item) in enumerate(self.item_manager.items.items()):
            rect = pygame.Rect(start_x + (i % 3) * gap, start_y + (i // 3) * gap, 60, 60)
            if rect.collidepoint(mx, my):
                self.tool = item_id
                self._update_item_button()
                self._close_popup()
                return None
        return None

    def _close_popup(self):
        self.popup = None
        self.popup_type = None
        self.text_input_focus = None
        self.text_inputs = {}
        pygame.key.stop_text_input()

    def _export_map(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()
        if filepath:
            self.map_data.save(filepath)

    def _import_map(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()
        if filepath:
            try:
                self.map_data = MapData.load(filepath)
                return {"action": "import", "map_data": self.map_data}
            except Exception as e:
                print(f"{_('import.failed')}: {e}")
        return None

    def update(self):
        pass

    def draw(self):
        self.screen.fill((240, 240, 240))

        ox = self.grid_offset_x + self.pan_offset_x
        oy = self.grid_offset_y + self.pan_offset_y
        ts = int(self.map_data.tile_size * self.zoom)

        for x in range(self.map_data.width + 1):
            px = ox + x * ts
            pygame.draw.line(self.screen, (200, 200, 200), (px, oy), (px, oy + self.map_data.height * ts))

        for y in range(self.map_data.height + 1):
            py = oy + y * ts
            pygame.draw.line(self.screen, (200, 200, 200), (ox, py), (ox + self.map_data.width * ts, py))

        for tile in self.map_data.get_ground_tiles():
            draw_rect = pygame.Rect(tile["x"] * ts + ox, tile["y"] * ts + oy, ts, ts)
            item = self.item_manager.get_item("ground")
            if item and item.texture:
                tex = pygame.transform.scale(item.texture, (ts, ts))
                self.screen.blit(tex, draw_rect)
            else:
                pygame.draw.rect(self.screen, (34, 139, 34), draw_rect)
                pygame.draw.rect(self.screen, (0, 100, 0), draw_rect, 2)

        for trap in self.map_data.traps:
            draw_rect = pygame.Rect(trap["x"] * ts + ox, trap["y"] * ts + oy, ts, ts)
            item = self.item_manager.get_item(trap.get("type", "spike"))
            if item and item.texture:
                tex = pygame.transform.scale(item.texture, (ts, ts))
                self.screen.blit(tex, draw_rect)
            else:
                self._draw_spike(draw_rect)

        for door in self.map_data.doors:
            draw_rect = pygame.Rect(door["x"] * ts + ox, door["y"] * ts + oy, ts, ts)
            item = self.item_manager.get_item("door")
            if item and item.texture:
                if door.get("open", False):
                    tex = item.texture.copy()
                    tex.set_alpha(80)
                    tex = pygame.transform.scale(tex, (ts, ts))
                    self.screen.blit(tex, draw_rect)
                else:
                    tex = pygame.transform.scale(item.texture, (ts, ts))
                    self.screen.blit(tex, draw_rect)
            else:
                if door.get("open", False):
                    pygame.draw.rect(self.screen, (100, 200, 100), draw_rect)
                    pygame.draw.rect(self.screen, (0, 150, 0), draw_rect, 2)
                else:
                    pygame.draw.rect(self.screen, (139, 90, 43), draw_rect)
                    pygame.draw.rect(self.screen, (100, 60, 30), draw_rect, 2)

        start_draw_rect = pygame.Rect(self.map_data.start["x"] * ts + ox, self.map_data.start["y"] * ts + oy, ts, ts)
        item = self.item_manager.get_item("start")
        if item and item.texture:
            tex = pygame.transform.scale(item.texture, (ts, ts))
            self.screen.blit(tex, start_draw_rect)
        else:
            pygame.draw.rect(self.screen, (0, 255, 127), start_draw_rect)
            pygame.draw.rect(self.screen, (0, 128, 0), start_draw_rect, 2)

        end_draw_rect = pygame.Rect(self.map_data.end["x"] * ts + ox, self.map_data.end["y"] * ts + oy, ts, ts)
        item = self.item_manager.get_item("end")
        if item and item.texture:
            tex = pygame.transform.scale(item.texture, (ts, ts))
            self.screen.blit(tex, end_draw_rect)
        else:
            pygame.draw.rect(self.screen, (255, 215, 0), end_draw_rect)
            pygame.draw.rect(self.screen, (255, 140, 0), end_draw_rect, 2)

        for btn in self.buttons:
            color = (220, 220, 220)
            if btn.get("action") in ("export", "import"):
                color = (144, 238, 144)
            elif btn.get("action") == "test":
                color = (255, 182, 193)
            elif btn.get("action") == "map_props":
                color = (180, 200, 255)
            elif btn.get("action") == "item_select":
                color = (255, 220, 150)
            pygame.draw.rect(self.screen, color, btn["rect"])
            pygame.draw.rect(self.screen, (100, 100, 100), btn["rect"], 2)
            text = self.small_font.render(btn["text"], True, (0, 0, 0))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

        zoom_pct = int(self.zoom * 100)
        tip_text = _("editor.tip_place").format(zoom=zoom_pct)
        info_text = self.small_font.render(tip_text, True, (80, 80, 80))
        self.screen.blit(info_text, (10, self.screen.get_height() - 30))

        if self.popup:
            self._draw_popup()

    def _draw_popup(self):
        popup_rect = self.popup["rect"]
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(120)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (250, 250, 250), popup_rect, border_radius=10)
        pygame.draw.rect(self.screen, (150, 150, 150), popup_rect, 2, border_radius=10)

        if self.close_btn_img:
            self.screen.blit(self.close_btn_img, self.popup["close_rect"])
        else:
            pygame.draw.rect(self.screen, (220, 80, 80), self.popup["close_rect"])
            x_text = self.small_font.render("X", True, (255, 255, 255))
            self.screen.blit(x_text, x_text.get_rect(center=self.popup["close_rect"].center))

        if self.popup_type == "map_props":
            self._draw_map_props_popup()
        elif self.popup_type == "item_select":
            self._draw_item_select_popup()

    def _draw_map_props_popup(self):
        popup_rect = self.popup["rect"]
        base_x = popup_rect.x
        base_y = popup_rect.y

        title = self.title_font.render(_("map_props.title"), True, (50, 50, 50))
        self.screen.blit(title, (base_x + 20, base_y + 15))

        sec1_text = self.small_font.render(_("map_props.map_info"), True, (100, 100, 100))
        self.screen.blit(sec1_text, (base_x + 20, base_y + 50))
        pygame.draw.line(self.screen, (200, 200, 200), (base_x + 20, base_y + 72), (popup_rect.right - 20, base_y + 72))

        fields_info = [
            (_("map_props.name"), "name", 80),
            (_("map_props.author"), "author", 125),
            (_("map_props.description"), "description", 170),
        ]
        for label, key, y_offset in fields_info:
            label_text = self.small_font.render(label + ":", True, (60, 60, 60))
            self.screen.blit(label_text, (base_x + 30, base_y + y_offset))

            if key == "description":
                rect = pygame.Rect(base_x + 100, base_y + y_offset, 420, 90)
            else:
                rect = pygame.Rect(base_x + 100, base_y + y_offset, 420, 30)

            pygame.draw.rect(self.screen, (255, 255, 255), rect)
            border_color = (100, 149, 237) if self.text_input_focus == key else (180, 180, 180)
            pygame.draw.rect(self.screen, border_color, rect, 2)

            ti = self.text_inputs.get(key)
            if ti:
                display_text = ti.get_display_text()
                if key == "description":
                    lines = display_text.split("\n")
                    for i, line in enumerate(lines[:3]):
                        line_text = self.small_font.render(line, True, (50, 50, 50))
                        self.screen.blit(line_text, (rect.x + 5, rect.y + 5 + i * 24))
                else:
                    val_text = self.small_font.render(display_text, True, (50, 50, 50))
                    self.screen.blit(val_text, (rect.x + 5, rect.y + 5))

                if self.text_input_focus == key and (pygame.time.get_ticks() // 530) % 2 == 0:
                    cursor_x = ti.get_cursor_x(self.small_font, rect.x + 5)
                    if key == "description":
                        text_before_cursor = ti.get_display_text()[:ti.cursor]
                        lines = text_before_cursor.split("\n")
                        cur_line = len(lines) - 1
                        cur_col = len(lines[-1])
                        cx = rect.x + 5 + self.small_font.size(lines[-1])[0]
                        cy = rect.y + 5 + cur_line * 24
                        pygame.draw.line(self.screen, (0, 0, 0), (cx, cy), (cx, cy + 18), 2)
                    else:
                        cy = rect.y + 5
                        pygame.draw.line(self.screen, (0, 0, 0), (cursor_x, cy), (cursor_x, cy + 18), 2)

        sec2_text = self.small_font.render(_("map_props.map_settings"), True, (100, 100, 100))
        self.screen.blit(sec2_text, (base_x + 20, base_y + 280))
        pygame.draw.line(self.screen, (200, 200, 200), (base_x + 20, base_y + 302), (popup_rect.right - 20, base_y + 302))

        fields_props = [
            (_("map_props.width"), "width", 310),
            (_("map_props.height"), "height", 355),
            (_("map_props.bg_color"), "bg_color", 400),
        ]
        for label, key, y_offset in fields_props:
            label_text = self.small_font.render(label + ":", True, (60, 60, 60))
            self.screen.blit(label_text, (base_x + 30, base_y + y_offset))

            rect = pygame.Rect(base_x + 100, base_y + y_offset, 420, 30)
            pygame.draw.rect(self.screen, (255, 255, 255), rect)
            border_color = (100, 149, 237) if self.text_input_focus == key else (180, 180, 180)
            pygame.draw.rect(self.screen, border_color, rect, 2)

            ti = self.text_inputs.get(key)
            if ti:
                display_text = ti.get_display_text()
                val_text = self.small_font.render(display_text, True, (50, 50, 50))
                self.screen.blit(val_text, (rect.x + 5, rect.y + 5))

                if self.text_input_focus == key and (pygame.time.get_ticks() // 530) % 2 == 0:
                    cursor_x = ti.get_cursor_x(self.small_font, rect.x + 5)
                    cy = rect.y + 5
                    pygame.draw.line(self.screen, (0, 0, 0), (cursor_x, cy), (cursor_x, cy + 18), 2)

        save_rect = pygame.Rect(popup_rect.centerx - 100, popup_rect.bottom - 55, 200, 40)
        pygame.draw.rect(self.screen, (100, 149, 237), save_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 130, 180), save_rect, 2, border_radius=6)
        save_text = self.small_font.render(_("map_props.save"), True, (255, 255, 255))
        self.screen.blit(save_text, save_text.get_rect(center=save_rect.center))

    def _draw_item_select_popup(self):
        popup_rect = self.popup["rect"]
        title = self.title_font.render(_("item_select.title"), True, (50, 50, 50))
        self.screen.blit(title, (popup_rect.x + 20, popup_rect.y + 15))

        mx, my = pygame.mouse.get_pos()
        start_x = popup_rect.x + 30
        start_y = popup_rect.y + 70
        gap = 90

        for i, (item_id, item) in enumerate(self.item_manager.items.items()):
            rect = pygame.Rect(start_x + (i % 3) * gap, start_y + (i // 3) * gap, 60, 60)
            hover = rect.collidepoint(mx, my)
            color = (200, 220, 255) if hover else (240, 240, 240)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (100, 149, 237) if self.tool == item_id else (180, 180, 180), rect, 2, border_radius=6)

            if item.texture:
                tex = pygame.transform.scale(item.texture, (50, 50))
                self.screen.blit(tex, tex.get_rect(center=rect.center))
            else:
                fallback = pygame.Rect(rect.centerx - 15, rect.centery - 15, 30, 30)
                colors = {"ground": (34, 139, 34), "start": (0, 255, 127), "end": (255, 215, 0), "spike": (255, 0, 0)}
                pygame.draw.rect(self.screen, colors.get(item_id, (200, 200, 200)), fallback)

            if hover:
                tip = self.small_font.render(_(f"items.{item_id}", item.name), True, (50, 50, 50))
                tip_bg = pygame.Rect(mx + 10, my - 25, tip.get_width() + 10, 22)
                pygame.draw.rect(self.screen, (255, 255, 200), tip_bg)
                pygame.draw.rect(self.screen, (200, 200, 100), tip_bg, 1)
                self.screen.blit(tip, (tip_bg.x + 5, tip_bg.y + 2))

    def _draw_spike(self, rect):
        x, y, w, h = rect
        points = [
            (x + w // 2, y),
            (x + w, y + h),
            (x, y + h)
        ]
        pygame.draw.polygon(self.screen, (255, 0, 0), points)
        pygame.draw.polygon(self.screen, (139, 0, 0), points, 2)

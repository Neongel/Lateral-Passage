import pygame
from map_data import MapData
from player import Player
from utils import get_font
from item_manager import ItemManager
from lang import _


class Game:
    def __init__(self, screen, map_data):
        self.screen = screen
        self.map_data = map_data
        self.item_manager = ItemManager()
        self.player = Player(
            map_data.start["x"] * map_data.tile_size + 5,
            map_data.start["y"] * map_data.tile_size + 5
        )
        self.camera_x = 0
        self.camera_y = 0
        self.won = False
        self.dead = False
        self.reset_timer = 0
        self.font = get_font(36)
        self.small_font = get_font(24)
        self._parse_bg_color()
        self._reset_doors()

    def _reset_doors(self):
        for door in getattr(self.map_data, 'doors', []):
            door["open"] = False

    def _parse_bg_color(self):
        try:
            c = self.map_data.bg_color.lstrip("#")
            self.bg_color = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            self.bg_color = (135, 206, 235)

    def handle_event(self, event, from_editor=False):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                self.player.jump()
            if event.key == pygame.K_ESCAPE:
                if from_editor:
                    return "editor"
                return "menu"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._check_door_click(event.pos)
        return None

    def _check_door_click(self, mouse_pos):
        mx, my = mouse_pos
        player_center_x = self.player.rect.centerx
        player_center_y = self.player.rect.centery
        tile_size = self.map_data.tile_size

        for door in getattr(self.map_data, 'doors', []):
            door_rect = self.map_data.get_tile_rect(door["x"], door["y"])
            door_screen_rect = pygame.Rect(
                door_rect[0] - self.camera_x,
                door_rect[1] - self.camera_y,
                door_rect[2],
                door_rect[3]
            )
            if door_screen_rect.collidepoint(mx, my):
                door_center_x = door_rect[0] + door_rect[2] // 2
                door_center_y = door_rect[1] + door_rect[3] // 2
                distance = ((player_center_x - door_center_x) ** 2 + (player_center_y - door_center_y) ** 2) ** 0.5
                if distance <= tile_size * 1.5:
                    self.map_data.toggle_door(door["x"], door["y"])
                break

    def update(self):
        if self.won:
            return None

        if self.dead:
            self.reset_timer -= 1
            if self.reset_timer <= 0:
                self._reset_level()
            return None

        self.player.update(self.map_data)

        if not self.player.alive:
            self.dead = True
            self.reset_timer = 60
            return None

        if self._check_trap_collision():
            self.dead = True
            self.reset_timer = 60
            return None

        if self._check_end_collision():
            self.won = True
            return None

        self._update_camera()
        return None

    def _check_trap_collision(self):
        for trap in self.map_data.traps:
            trap_rect = self.map_data.get_tile_rect(trap["x"], trap["y"])
            if self.player.rect.colliderect(trap_rect):
                item = self.item_manager.get_item(trap.get("type", "spike"))
                if item and item.has_lua and item.lua:
                    try:
                        result = item.on_touch(self.player, self.map_data)
                        if result:
                            return True
                    except Exception as e:
                        print(f"Lua Trap Error: {e}")
                else:
                    self.player.alive = False
                    return True
        return False

    def _check_end_collision(self):
        end_rect = self.map_data.get_tile_rect(self.map_data.end["x"], self.map_data.end["y"])
        if self.player.rect.colliderect(end_rect):
            item = self.item_manager.get_item("end")
            if item and item.has_lua and item.lua:
                try:
                    result = item.on_touch(self.player, self.map_data)
                    if result:
                        return True
                except Exception as e:
                    print(f"Lua End Error: {e}")
            else:
                return True
        return False

    def _update_camera(self):
        screen_w, screen_h = self.screen.get_size()
        target_x = self.player.rect.centerx - screen_w // 2
        target_y = self.player.rect.centery - screen_h // 2

        map_pixel_w = self.map_data.width * self.map_data.tile_size
        map_pixel_h = self.map_data.height * self.map_data.tile_size

        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1

        self.camera_x = max(0, min(self.camera_x, map_pixel_w - screen_w))
        self.camera_y = max(0, min(self.camera_y, map_pixel_h - screen_h))

    def _reset_level(self):
        self.player.reset(
            self.map_data.start["x"] * self.map_data.tile_size + 5,
            self.map_data.start["y"] * self.map_data.tile_size + 5
        )
        self.dead = False
        self.won = False
        self.reset_timer = 0

    def draw(self):
        self.screen.fill(self.bg_color)

        for tile in self.map_data.get_ground_tiles():
            rect = self.map_data.get_tile_rect(tile["x"], tile["y"])
            draw_rect = pygame.Rect(rect[0] - self.camera_x, rect[1] - self.camera_y, rect[2], rect[3])
            item = self.item_manager.get_item("ground")
            if item and item.draw(self.screen, draw_rect):
                pass
            else:
                pygame.draw.rect(self.screen, (34, 139, 34), draw_rect)
                pygame.draw.rect(self.screen, (0, 100, 0), draw_rect, 2)

        for trap in self.map_data.traps:
            rect = self.map_data.get_tile_rect(trap["x"], trap["y"])
            draw_rect = pygame.Rect(rect[0] - self.camera_x, rect[1] - self.camera_y, rect[2], rect[3])
            item = self.item_manager.get_item(trap.get("type", "spike"))
            if item and item.draw(self.screen, draw_rect):
                pass
            else:
                self._draw_spike(draw_rect)

        end_rect = self.map_data.get_tile_rect(self.map_data.end["x"], self.map_data.end["y"])
        end_draw_rect = pygame.Rect(end_rect[0] - self.camera_x, end_rect[1] - self.camera_y, end_rect[2], end_rect[3])
        item = self.item_manager.get_item("end")
        if item and item.draw(self.screen, end_draw_rect):
            pass
        else:
            pygame.draw.rect(self.screen, (255, 215, 0), end_draw_rect)
            pygame.draw.rect(self.screen, (255, 140, 0), end_draw_rect, 2)

        start_rect = self.map_data.get_tile_rect(self.map_data.start["x"], self.map_data.start["y"])
        start_draw_rect = pygame.Rect(start_rect[0] - self.camera_x, start_rect[1] - self.camera_y, start_rect[2], start_rect[3])
        item = self.item_manager.get_item("start")
        if item and item.draw(self.screen, start_draw_rect):
            pass
        else:
            pygame.draw.rect(self.screen, (0, 255, 127), start_draw_rect)
            pygame.draw.rect(self.screen, (0, 128, 0), start_draw_rect, 2)

        for door in getattr(self.map_data, 'doors', []):
            rect = self.map_data.get_tile_rect(door["x"], door["y"])
            draw_rect = pygame.Rect(rect[0] - self.camera_x, rect[1] - self.camera_y, rect[2], rect[3])
            item = self.item_manager.get_item("door")
            if item and item.texture:
                if door.get("open", False):
                    tex = item.texture.copy()
                    tex.set_alpha(80)
                    self.screen.blit(tex, draw_rect)
                else:
                    self.screen.blit(item.texture, draw_rect)
            else:
                if door.get("open", False):
                    pygame.draw.rect(self.screen, (100, 200, 100, 80), draw_rect)
                    pygame.draw.rect(self.screen, (0, 150, 0), draw_rect, 2)
                else:
                    pygame.draw.rect(self.screen, (139, 90, 43), draw_rect)
                    pygame.draw.rect(self.screen, (100, 60, 30), draw_rect, 2)

        self.player.draw(self.screen, self.camera_x, self.camera_y)

        if self.won:
            self._draw_message(_("game.win_title"), _("game.win_subtitle"))
        elif self.dead:
            self._draw_message(_("game.death_title"), _("game.death_subtitle"))

    def _draw_spike(self, rect):
        x, y, w, h = rect
        points = [
            (x + w // 2, y),
            (x + w, y + h),
            (x, y + h)
        ]
        pygame.draw.polygon(self.screen, (255, 0, 0), points)
        pygame.draw.polygon(self.screen, (139, 0, 0), points, 2)

    def _draw_message(self, main_msg, sub_msg):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        text = self.font.render(main_msg, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 20))
        self.screen.blit(text, text_rect)

        sub_text = self.small_font.render(sub_msg, True, (200, 200, 200))
        sub_rect = sub_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20))
        self.screen.blit(sub_text, sub_rect)

import pygame
import os


class Player:
    def __init__(self, x, y, size=30):
        self.rect = pygame.Rect(x, y, size, size)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = 12
        self.gravity = 0.6
        self.on_ground = False
        self.alive = True
        self.image = None
        self._load_image(size)

    def update(self, map_data):
        if not self.alive:
            return

        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed

        self.vel_y += self.gravity
        self.rect.x += self.vel_x
        self._handle_collision_x(map_data)
        self.rect.y += self.vel_y
        self._handle_collision_y(map_data)

        if self.rect.top > map_data.height * map_data.tile_size:
            self.alive = False

    def _handle_collision_x(self, map_data):
        for tile in map_data.get_ground_tiles():
            tile_rect = map_data.get_tile_rect(tile["x"], tile["y"])
            if self.rect.colliderect(tile_rect):
                if self.vel_x > 0:
                    self.rect.right = tile_rect[0]
                elif self.vel_x < 0:
                    self.rect.left = tile_rect[0] + tile_rect[2]
        for door in getattr(map_data, 'doors', []):
            if not door.get("open", False):
                tile_rect = map_data.get_tile_rect(door["x"], door["y"])
                if self.rect.colliderect(tile_rect):
                    if self.vel_x > 0:
                        self.rect.right = tile_rect[0]
                    elif self.vel_x < 0:
                        self.rect.left = tile_rect[0] + tile_rect[2]

    def _handle_collision_y(self, map_data):
        self.on_ground = False
        for tile in map_data.get_ground_tiles():
            tile_rect = map_data.get_tile_rect(tile["x"], tile["y"])
            if self.rect.colliderect(tile_rect):
                if self.vel_y > 0:
                    self.rect.bottom = tile_rect[1]
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = tile_rect[1] + tile_rect[3]
                    self.vel_y = 0
        for door in getattr(map_data, 'doors', []):
            if not door.get("open", False):
                tile_rect = map_data.get_tile_rect(door["x"], door["y"])
                if self.rect.colliderect(tile_rect):
                    if self.vel_y > 0:
                        self.rect.bottom = tile_rect[1]
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = tile_rect[1] + tile_rect[3]
                        self.vel_y = 0

    def jump(self):
        if self.on_ground and self.alive:
            self.vel_y = -self.jump_power
            self.on_ground = False

    def check_trap_collision(self, map_data):
        if not self.alive:
            return False
        for trap in map_data.traps:
            trap_rect = map_data.get_tile_rect(trap["x"], trap["y"])
            if self.rect.colliderect(trap_rect):
                self.alive = False
                return True
        return False

    def check_end_collision(self, map_data):
        if not self.alive:
            return False
        end_rect = map_data.get_tile_rect(map_data.end["x"], map_data.end["y"])
        return self.rect.colliderect(end_rect)

    def reset(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.alive = True

    def _load_image(self, size):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "assets", "img", "character.png")
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (size, size))
        except Exception:
            self.image = None

    def draw(self, screen, camera_x=0, camera_y=0):
        if self.alive:
            draw_rect = self.rect.move(-camera_x, -camera_y)
            if self.image:
                screen.blit(self.image, draw_rect)
            else:
                pygame.draw.rect(screen, (0, 128, 255), draw_rect)
                pygame.draw.rect(screen, (0, 0, 0), draw_rect, 2)

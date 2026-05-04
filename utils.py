import pygame
import os

FONT_PATH = "assets/fonts/AlimamaFangYuanTiVF.ttf"


def get_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont("simhei", size)


def init_ime():
    os.environ["SDL_IME_SHOW_UI"] = "1"


class TextInput:
    def __init__(self, initial_text=""):
        self.text = initial_text
        self.cursor = len(initial_text)
        self.editing = False
        self.editing_text = ""
        self.editing_pos = 0

    def handle_event(self, event):
        if event.type == pygame.TEXTEDITING:
            self.editing = True
            self.editing_text = event.text
            self.editing_pos = event.start
            return True
        elif event.type == pygame.TEXTINPUT:
            self.editing = False
            self.editing_text = ""
            self.text = self.text[:self.cursor] + event.text + self.text[self.cursor:]
            self.cursor += len(event.text)
            return True
        elif event.type == pygame.KEYDOWN:
            if self.editing:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.editing = False
                    self.editing_text = ""
                return True
            if event.key == pygame.K_BACKSPACE:
                if self.cursor > 0:
                    self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                    self.cursor -= 1
                return True
            elif event.key == pygame.K_DELETE:
                if self.cursor < len(self.text):
                    self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
                return True
            elif event.key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.cursor = min(len(self.text), self.cursor + 1)
                return True
            elif event.key == pygame.K_HOME:
                self.cursor = 0
                return True
            elif event.key == pygame.K_END:
                self.cursor = len(self.text)
                return True
            elif event.key == pygame.K_RETURN:
                return True
        return False

    def get_display_text(self):
        if self.editing and self.editing_text:
            left = self.text[:self.cursor]
            right = self.text[self.cursor:]
            edit_left = self.editing_text[:self.editing_pos]
            edit_right = self.editing_text[self.editing_pos:]
            return left + edit_left + edit_right + right
        return self.text

    def get_cursor_x(self, font, x_offset):
        if self.editing and self.editing_text:
            left = self.text[:self.cursor]
            edit_left = self.editing_text[:self.editing_pos]
            measure_text = left + edit_left
            return x_offset + font.size(measure_text)[0]
        measure_text = self.text[:self.cursor]
        return x_offset + font.size(measure_text)[0]

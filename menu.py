import pygame
import tkinter as tk
from tkinter import filedialog
import os
import json
from map_data import MapData
from utils import get_font
from lang import _, I18n


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = get_font(48)
        self.button_font = get_font(28)
        self.small_font = get_font(18)
        self.title_font = get_font(36)
        self.buttons = []
        self.state = "main"
        self.level_buttons = []
        self.settings_buttons = []
        self.changelog_data = []
        self.changelog_scroll = 0
        self._init_main_buttons()
        self._scan_levels()
        self.version = "v1.0.1"
        self.dev_info_btn = pygame.Rect(screen.get_width() - 42, screen.get_height() - 42, 32, 32)
        self.dev_info_img = None
        self.show_dev_popup = False
        self._load_dev_info_img()
        self._init_settings_buttons()
        self._load_changelog()

    def _load_dev_info_img(self):
        try:
            self.dev_info_img = pygame.image.load("assets/img/dev_info.png")
        except Exception:
            self.dev_info_img = None

    def _load_changelog(self):
        try:
            with open("data/changelog.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self.changelog_data = data.get("changelog", [])
        except Exception:
            self.changelog_data = []

    def _scan_levels(self):
        self.levels = []
        levels_dir = "levels"
        if os.path.exists(levels_dir):
            for filename in sorted(os.listdir(levels_dir)):
                if filename.endswith(".json"):
                    filepath = os.path.join(levels_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        info = data.get("info", {})
                        self.levels.append({
                            "file": filepath,
                            "name": info.get("name", filename),
                            "author": info.get("author", _("author", "未知")),
                            "description": info.get("description", ""),
                            "filename": filename
                        })
                    except Exception:
                        self.levels.append({
                            "file": filepath,
                            "name": filename,
                            "author": _("author", "未知"),
                            "description": "",
                            "filename": filename
                        })

    def _init_main_buttons(self):
        sw, sh = self.screen.get_size()
        center_x = sw // 2
        start_y = sh // 2 - 100
        gap = 60

        self.buttons = [
            {"rect": pygame.Rect(center_x - 120, start_y, 240, 45), "action": "level_select", "text": _("menu.start_game")},
            {"rect": pygame.Rect(center_x - 120, start_y + gap, 240, 45), "action": "editor", "text": _("menu.editor")},
            {"rect": pygame.Rect(center_x - 120, start_y + gap * 2, 240, 45), "action": "import_play", "text": _("menu.import_map")},
            {"rect": pygame.Rect(center_x - 120, start_y + gap * 3, 240, 45), "action": "settings", "text": _("menu.settings")},
            {"rect": pygame.Rect(center_x - 120, start_y + gap * 4, 240, 45), "action": "changelog", "text": _("menu.changelog")},
            {"rect": pygame.Rect(center_x - 120, start_y + gap * 5, 240, 45), "action": "quit", "text": _("menu.quit")},
        ]

    def _init_level_buttons(self):
        self.level_buttons = []
        sw, sh = self.screen.get_size()
        center_x = sw // 2
        start_y = 160
        gap = 80
        btn_width = 500
        btn_height = 65

        for i, level in enumerate(self.levels):
            rect = pygame.Rect(center_x - btn_width // 2, start_y + i * gap, btn_width, btn_height)
            self.level_buttons.append({"rect": rect, "level": level, "index": i})

        back_y = start_y + len(self.levels) * gap + 20
        self.level_buttons.append({
            "rect": pygame.Rect(center_x - 100, back_y, 200, 45),
            "action": "back",
            "text": _("level_select.back")
        })

    def _init_settings_buttons(self):
        sw, sh = self.screen.get_size()
        center_x = sw // 2
        start_y = 180
        gap = 60
        btn_width = 300
        btn_height = 50

        self.settings_buttons = []
        available_langs = I18n.get_instance().available_langs()
        current_lang = I18n.get_instance().current_lang()

        for i, lang_id in enumerate(available_langs):
            lang_name = I18n.get_instance().get_from_lang(lang_id, "language")
            is_selected = (lang_id == current_lang)
            self.settings_buttons.append({
                "rect": pygame.Rect(center_x - btn_width // 2, start_y + i * gap, btn_width, btn_height),
                "action": "lang",
                "lang_id": lang_id,
                "text": lang_name,
                "selected": is_selected
            })

        back_y = start_y + len(available_langs) * gap + 30
        self.settings_buttons.append({
            "rect": pygame.Rect(center_x - 100, back_y, 200, 45),
            "action": "back",
            "text": _("settings.back")
        })

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if self.show_dev_popup:
                self.show_dev_popup = False
                return None

            if self.state == "main":
                if self.dev_info_btn.collidepoint(mx, my):
                    self.show_dev_popup = True
                    return None

                for btn in self.buttons:
                    if btn["rect"].collidepoint(mx, my):
                        action = btn["action"]
                        if action == "level_select":
                            self.state = "level_select"
                            self._init_level_buttons()
                            return None
                        elif action == "editor":
                            return {"action": "editor"}
                        elif action == "import_play":
                            return self._import_and_play()
                        elif action == "settings":
                            self.state = "settings"
                            self._init_settings_buttons()
                            return None
                        elif action == "changelog":
                            self.state = "changelog"
                            self.changelog_scroll = 0
                            return None
                        elif action == "quit":
                            return {"action": "quit"}

            elif self.state == "settings":
                for btn in self.settings_buttons:
                    if btn["rect"].collidepoint(mx, my):
                        if btn.get("action") == "back":
                            self.state = "main"
                            self._init_main_buttons()
                            return None
                        elif btn.get("action") == "lang":
                            I18n.get_instance().set_lang(btn["lang_id"])
                            self._init_settings_buttons()
                            self._init_main_buttons()
                            return None

            elif self.state == "level_select":
                for btn in self.level_buttons:
                    if btn["rect"].collidepoint(mx, my):
                        if btn.get("action") == "back":
                            self.state = "main"
                            return None
                        elif "level" in btn:
                            try:
                                map_data = MapData.load(btn["level"]["file"])
                                return {"action": "play", "map_data": map_data}
                            except Exception as e:
                                print(f"{_('level_select.load_failed')}: {e}")
                                return None

            elif self.state == "changelog":
                back_btn = pygame.Rect(self.screen.get_width() // 2 - 100, self.screen.get_height() - 60, 200, 45)
                if back_btn.collidepoint(mx, my):
                    self.state = "main"
                    self._init_main_buttons()
                    return None

        if event.type == pygame.MOUSEWHEEL:
            if self.state == "changelog":
                self.changelog_scroll -= event.y * 30
                self.changelog_scroll = max(0, self.changelog_scroll)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state in ("level_select", "settings", "changelog"):
                    self.state = "main"
                    self._init_main_buttons()
                else:
                    return {"action": "quit"}

        return None

    def _import_and_play(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()
        if filepath:
            try:
                map_data = MapData.load(filepath)
                return {"action": "play", "map_data": map_data}
            except Exception as e:
                print(f"{_('import.failed')}: {e}")
        return None

    def update(self):
        pass

    def draw(self):
        if self.state == "main":
            self._draw_main()
        elif self.state == "level_select":
            self._draw_level_select()
        elif self.state == "settings":
            self._draw_settings()
        elif self.state == "changelog":
            self._draw_changelog()

    def _draw_main(self):
        self.screen.fill((25, 25, 40))

        title = self.font.render(_("menu.title"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect)

        subtitle = self.small_font.render(_("menu.subtitle"), True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)

        mx, my = pygame.mouse.get_pos()
        for btn in self.buttons:
            hover = btn["rect"].collidepoint(mx, my)
            color = (70, 130, 180) if hover else (50, 50, 70)
            pygame.draw.rect(self.screen, color, btn["rect"], border_radius=8)
            pygame.draw.rect(self.screen, (100, 149, 237), btn["rect"], 2, border_radius=8)

            text = self.button_font.render(btn["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

        version_text = self.small_font.render(f"{_('menu.version')} {self.version}", True, (150, 150, 150))
        self.screen.blit(version_text, (10, self.screen.get_height() - 20))

        if self.dev_info_img:
            self.screen.blit(self.dev_info_img, self.dev_info_btn)
        else:
            pygame.draw.rect(self.screen, (100, 149, 237), self.dev_info_btn, border_radius=4)

        if self.show_dev_popup:
            popup_rect = pygame.Rect(20, self.screen.get_height() - 150, 280, 130)
            pygame.draw.rect(self.screen, (40, 40, 60), popup_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 149, 237), popup_rect, 2, border_radius=8)

            title = self.small_font.render(_("dev_info.title"), True, (255, 255, 255))
            self.screen.blit(title, (popup_rect.x + 10, popup_rect.y + 10))

            dev1 = self.small_font.render(f"{_('dev_info.developers')}: 部鑫、TRAE", True, (200, 200, 200))
            self.screen.blit(dev1, (popup_rect.x + 10, popup_rect.y + 40))

            dev2 = self.small_font.render(f"{_('dev_info.ui_design')}: TRAE", True, (200, 200, 200))
            self.screen.blit(dev2, (popup_rect.x + 10, popup_rect.y + 70))

            close_text = self.small_font.render(_("dev_info.click_to_close"), True, (150, 150, 150))
            self.screen.blit(close_text, (popup_rect.x + 10, popup_rect.y + 100))

    def _draw_level_select(self):
        self.screen.fill((25, 25, 40))

        title = self.title_font.render(_("level_select.title"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)

        mx, my = pygame.mouse.get_pos()

        for btn in self.level_buttons:
            hover = btn["rect"].collidepoint(mx, my)

            if btn.get("action") == "back":
                color = (180, 80, 80) if hover else (120, 50, 50)
                pygame.draw.rect(self.screen, color, btn["rect"], border_radius=6)
                pygame.draw.rect(self.screen, (200, 100, 100), btn["rect"], 2, border_radius=6)
                text = self.button_font.render(btn["text"], True, (255, 255, 255))
                text_rect = text.get_rect(center=btn["rect"].center)
                self.screen.blit(text, text_rect)
            else:
                level = btn["level"]
                color = (60, 100, 160) if hover else (40, 40, 60)
                pygame.draw.rect(self.screen, color, btn["rect"], border_radius=8)
                pygame.draw.rect(self.screen, (100, 149, 237), btn["rect"], 2, border_radius=8)

                name_text = self.button_font.render(f"{btn['index'] + 1}. {level['name']}", True, (255, 255, 255))
                name_rect = name_text.get_rect(topleft=(btn["rect"].x + 15, btn["rect"].y + 8))
                self.screen.blit(name_text, name_rect)

                desc_text = self.small_font.render(f"{_('level_select.author')}: {level['author']} | {level['description']}", True, (180, 180, 180))
                desc_rect = desc_text.get_rect(topleft=(btn["rect"].x + 15, btn["rect"].y + 38))
                self.screen.blit(desc_text, desc_rect)

    def _draw_settings(self):
        self.screen.fill((25, 25, 40))

        title = self.title_font.render(_("settings.title"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)

        subtitle = self.small_font.render(_("settings.language"), True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, 130))
        self.screen.blit(subtitle, subtitle_rect)

        mx, my = pygame.mouse.get_pos()

        for btn in self.settings_buttons:
            hover = btn["rect"].collidepoint(mx, my)

            if btn.get("action") == "back":
                color = (180, 80, 80) if hover else (120, 50, 50)
                pygame.draw.rect(self.screen, color, btn["rect"], border_radius=6)
                pygame.draw.rect(self.screen, (200, 100, 100), btn["rect"], 2, border_radius=6)
                text = self.button_font.render(btn["text"], True, (255, 255, 255))
                text_rect = text.get_rect(center=btn["rect"].center)
                self.screen.blit(text, text_rect)
            elif btn.get("action") == "lang":
                if btn.get("selected", False):
                    color = (70, 130, 180)
                    border_color = (100, 149, 237)
                else:
                    color = (50, 50, 70) if hover else (40, 40, 60)
                    border_color = (100, 149, 237) if hover else (80, 80, 100)
                pygame.draw.rect(self.screen, color, btn["rect"], border_radius=8)
                pygame.draw.rect(self.screen, border_color, btn["rect"], 2, border_radius=8)
                text = self.button_font.render(btn["text"], True, (255, 255, 255))
                text_rect = text.get_rect(center=btn["rect"].center)
                self.screen.blit(text, text_rect)
                if btn.get("selected", False):
                    check_mark = self.small_font.render("✓", True, (100, 249, 237))
                    check_rect = check_mark.get_rect(right=btn["rect"].right - 15, centery=btn["rect"].centery)
                    self.screen.blit(check_mark, check_rect)

    def _draw_changelog(self):
        self.screen.fill((25, 25, 40))

        title = self.title_font.render(_("changelog.title"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title, title_rect)

        content_rect = pygame.Rect(50, 90, self.screen.get_width() - 100, self.screen.get_height() - 170)

        pygame.draw.rect(self.screen, (35, 35, 50), content_rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 80, 100), content_rect, 2, border_radius=8)

        y_offset = 110 - self.changelog_scroll

        for entry in self.changelog_data:
            if y_offset > content_rect.bottom:
                break
            if y_offset > content_rect.top - 50:
                version_text = self.button_font.render(f"{entry['version']} ({entry['date']})", True, (100, 149, 237))
                self.screen.blit(version_text, (70, y_offset))
                y_offset += 35

                for change in entry.get("changes", []):
                    if y_offset > content_rect.bottom:
                        break
                    if y_offset > content_rect.top - 20:
                        change_text = self.small_font.render(f"• {change}", True, (200, 200, 200))
                        self.screen.blit(change_text, (90, y_offset))
                    y_offset += 25

                y_offset += 15

        mx, my = pygame.mouse.get_pos()
        back_btn = pygame.Rect(self.screen.get_width() // 2 - 100, self.screen.get_height() - 60, 200, 45)
        hover = back_btn.collidepoint(mx, my)
        color = (180, 80, 80) if hover else (120, 50, 50)
        pygame.draw.rect(self.screen, color, back_btn, border_radius=6)
        pygame.draw.rect(self.screen, (200, 100, 100), back_btn, 2, border_radius=6)
        text = self.button_font.render(_("changelog.back"), True, (255, 255, 255))
        text_rect = text.get_rect(center=back_btn.center)
        self.screen.blit(text, text_rect)

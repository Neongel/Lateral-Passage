import pygame
import sys
import os

os.environ["SDL_IME_SHOW_UI"] = "1"
VERSION = "v1.0.2"

from menu import Menu
from game import Game
from editor import MapEditor
from map_data import MapData
from lang import _


def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption(f"{_('game_name')} {VERSION}")
    clock = pygame.time.Clock()

    state = "menu"
    menu = Menu(screen)
    game = None
    editor = None
    previous_state = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if state == "menu":
                result = menu.handle_event(event)
                if result:
                    action = result.get("action")
                    if action == "play":
                        game = Game(screen, result["map_data"])
                        state = "playing"
                        previous_state = "menu"
                    elif action == "editor":
                        editor = MapEditor(screen)
                        state = "editing"
                        previous_state = "menu"
                    elif action == "quit":
                        running = False

            elif state == "playing":
                result = game.handle_event(event)
                if result == "menu":
                    if previous_state == "editing":
                        state = "editing"
                    else:
                        state = "menu"
                    game = None

            elif state == "editing":
                result = editor.handle_event(event)
                if result == "menu":
                    state = "menu"
                    editor = None
                elif isinstance(result, dict):
                    if result.get("action") == "test":
                        game = Game(screen, result["map_data"])
                        state = "playing"
                        previous_state = "editing"

        if not running:
            break

        if state == "menu":
            menu.update()
            menu.draw()
        elif state == "playing":
            game.update()
            game.draw()
        elif state == "editing":
            editor.update()
            editor.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

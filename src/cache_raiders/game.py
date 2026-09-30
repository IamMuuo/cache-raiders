import pygame

from cache_raiders.entities.entity import Entity
from cache_raiders.entities.player import Player


class Game:
    def __init__(self) -> None:
        pygame.init()
        self._running: bool = True
        self._screen = pygame.display.set_mode(
            (1280, 720),
        )
        self._clock = pygame.time.Clock()
        self._delta_time = 0

        self._player: Entity = Player(self._screen.get_width())

    def run(self) -> None:
        while self._running:
            self._handle_events()
            self._update()
            self._render()

            self._delta_time = self._clock.tick(60) / 1000

        pygame.quit()

    def _update(self) -> None:
        self._player.update(self._delta_time)

    def _render(self) -> None:
        self._screen.fill("black")
        self._player.render(self._screen)
        pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            self._player.handle_input(event)

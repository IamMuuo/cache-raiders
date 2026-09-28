import pygame


class Game:
    def __init__(self) -> None:
        pygame.init()
        self._running: bool = True
        self._screen = pygame.display.set_mode(
            (1280, 720),
        )
        self._clock = pygame.time.Clock()
        self._delta_time = 0

    def run(self) -> None:
        while self._running:
            self._handle_events()
            self._update()
            self._render()

            self._delta_time = self._clock.tick(60) / 1000

        pygame.quit()

    def _update(self) -> None:
        pass

    def _render(self) -> None:
        self._screen.fill("black")
        pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

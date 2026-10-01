import random

import pygame
from pygame.math import Vector2

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

        self._players: list[Player] = []
        self._spawn_players(5)

    def run(self) -> None:
        while self._running:
            self._handle_events()
            self._update()
            self._render()

            self._delta_time = self._clock.tick(60) / 1000

        pygame.quit()

    def _update(self) -> None:
        for player in self._players:
            player.update(self._delta_time)

    def _render(self) -> None:
        self._screen.fill("black")
        for player in self._players:
            player.render(self._screen)
        pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._spawn_players(20)

            for player in self._players:
                player.handle_input(event)

    def _spawn_players(self, count: int) -> None:
        for _ in range(count):
            self._players.append(
                Player(
                    self._screen.get_width(),
                    self._find_spawn_position(),
                )
            )

    def _find_spawn_position(self) -> Vector2:
        sprite_size = Player.SPRITE_SIZE
        max_x = max(0, self._screen.get_width() - sprite_size)
        max_y = max(0, self._screen.get_height() - sprite_size)
        existing_rects = [player.rect for player in self._players]

        best_position = Vector2()
        best_score: tuple[int, int] | None = None
        for _ in range(64):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            candidate_rect = pygame.Rect(x, y, sprite_size, sprite_size)

            overlap_count = 0
            overlap_area = 0
            for existing_rect in existing_rects:
                overlap = candidate_rect.clip(existing_rect)
                area = overlap.width * overlap.height
                if area:
                    overlap_count += 1
                    overlap_area += area

            score = (overlap_count, overlap_area)
            if best_score is None or score < best_score:
                best_position = Vector2(x, y)
                best_score = score
                if score == (0, 0):
                    break

        return best_position

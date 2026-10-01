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
        self._hud_font = pygame.font.Font(None, 22)
        self._hud_panel = pygame.Surface((440, 210), pygame.SRCALPHA)

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
        self._render_hud()
        pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._spawn_players(20)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                self._remove_players(20)

            for player in self._players:
                player.handle_input(event)

    def _spawn_players(self, count: int) -> None:
        existing_rects = [player.rect for player in self._players]
        for _ in range(count):
            player = Player(
                self._screen.get_width(),
                self._find_spawn_position(existing_rects),
            )
            self._players.append(player)
            existing_rects.append(player.rect)

    def _remove_players(self, count: int) -> None:
        keep_count = max(1, len(self._players) - count)
        del self._players[keep_count:]

    def _find_spawn_position(
        self,
        existing_rects: list[pygame.Rect],
    ) -> Vector2:
        sprite_size = Player.SPRITE_SIZE
        max_x = max(0, self._screen.get_width() - sprite_size)
        max_y = max(0, self._screen.get_height() - sprite_size)

        best_position = Vector2()
        best_score: tuple[int, int] | None = None
        for _ in range(64):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            candidate_rect = pygame.Rect(x, y, sprite_size, sprite_size)

            overlapping_indices = candidate_rect.collidelistall(existing_rects)
            overlap_area = 0
            for index in overlapping_indices:
                overlap = candidate_rect.clip(existing_rects[index])
                area = overlap.width * overlap.height
                overlap_area += area

            score = (len(overlapping_indices), overlap_area)
            if best_score is None or score < best_score:
                best_position = Vector2(x, y)
                best_score = score
                if score == (0, 0):
                    break

        return best_position

    def _render_hud(self) -> None:
        particle_count = sum(player.particle_count for player in self._players)
        ship_count = len(self._players)
        lines = (
            f"Ships: {ship_count}",
            f"Particles: {particle_count}",
            f"Objects: {ship_count + particle_count}",
            f"FPS: {self._clock.get_fps():.0f}",
            "Ships: R +20  |  F -20 (min 1)",
            "Particles/player: P +1  |  O -1",
            "P also emits a 60-particle burst",
            "Speed: Shift+= faster  |  - slower",
        )

        self._hud_panel.fill((8, 12, 20, 220))
        pygame.draw.rect(self._hud_panel, (75, 155, 230), self._hud_panel.get_rect(), 2)
        for index, line in enumerate(lines):
            text = self._hud_font.render(line, True, (240, 245, 255))
            self._hud_panel.blit(text, (12, 8 + index * 24))

        self._screen.blit(self._hud_panel, (12, 12))

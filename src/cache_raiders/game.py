from collections import deque
import random
from time import perf_counter

import pygame
from pygame.math import Vector2

from cache_raiders.entities.particle_emitter import ParticleStorageMode
from cache_raiders.entities.player import (
    Player,
    PlayerPositionArrays,
    PlayerPositionMode,
)


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
        self._hud_panel = pygame.Surface((440, 310), pygame.SRCALPHA)

        self._particle_storage_mode = ParticleStorageMode.AOS
        self._player_position_mode = PlayerPositionMode.AOS
        self._player_position_arrays = PlayerPositionArrays()
        self._player_position_samples: dict[PlayerPositionMode, deque[float]] = {
            mode: deque(maxlen=120) for mode in PlayerPositionMode
        }
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
        # Time movement alone so particles and drawing do not skew this comparison.
        position_start = perf_counter()
        if self._player_position_mode is PlayerPositionMode.AOS:
            for player in self._players:
                player.update_position(self._delta_time)
        else:
            self._player_position_arrays.update(
                self._delta_time,
                self._screen.get_width(),
                Player.SPRITE_SIZE,
            )
        elapsed = (perf_counter() - position_start) * 1_000_000
        self._player_position_samples[self._player_position_mode].append(elapsed)

        for player in self._players:
            player.update_emitter(self._delta_time)

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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                self._toggle_particle_storage()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_v:
                self._toggle_player_position_mode()

            for player in self._players:
                player.handle_input(event)

    def _spawn_players(self, count: int) -> None:
        existing_rects = [player.rect for player in self._players]
        for _ in range(count):
            player = Player(
                self._screen.get_width(),
                self._find_spawn_position(existing_rects),
            )
            player.set_particle_storage_mode(self._particle_storage_mode)
            if self._player_position_mode is PlayerPositionMode.SOA:
                player.use_soa_positions(
                    self._player_position_arrays,
                    len(self._players),
                )
            self._players.append(player)
            existing_rects.append(player.rect)
        self._reset_player_position_samples()

    def _toggle_particle_storage(self) -> None:
        if self._particle_storage_mode is ParticleStorageMode.AOS:
            self._particle_storage_mode = ParticleStorageMode.SOA
        else:
            self._particle_storage_mode = ParticleStorageMode.AOS

        for player in self._players:
            player.set_particle_storage_mode(self._particle_storage_mode)

    def _toggle_player_position_mode(self) -> None:
        if self._player_position_mode is PlayerPositionMode.AOS:
            self._player_position_mode = PlayerPositionMode.SOA
            for index, player in enumerate(self._players):
                player.use_soa_positions(self._player_position_arrays, index)
        else:
            for player in self._players:
                player.use_aos_position()
            self._player_position_arrays.clear()
            self._player_position_mode = PlayerPositionMode.AOS

    def _remove_players(self, count: int) -> None:
        keep_count = max(1, len(self._players) - count)
        if keep_count == len(self._players):
            return
        del self._players[keep_count:]
        if self._player_position_mode is PlayerPositionMode.SOA:
            self._player_position_arrays.truncate(keep_count)
        self._reset_player_position_samples()

    def _reset_player_position_samples(self) -> None:
        for samples in self._player_position_samples.values():
            samples.clear()

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
        storage_label = (
            "AoS (faster)"
            if self._particle_storage_mode is ParticleStorageMode.AOS
            else self._particle_storage_mode.value
        )
        aos_time = self._average_position_time(PlayerPositionMode.AOS)
        soa_time = self._average_position_time(PlayerPositionMode.SOA)
        position_winner = self._position_update_winner()
        lines = (
            f"Ships: {ship_count}",
            f"Particles: {particle_count}",
            f"Objects: {ship_count + particle_count}",
            f"FPS: {self._clock.get_fps():.0f}",
            "Ships: R +20  |  F -20 (min 1)",
            "Particles/player: P +1  |  O -1",
            "P also emits a 60-particle burst",
            "Speed: Shift+= faster  |  - slower",
            f"Particle storage: B toggle ({storage_label})",
            f"Player positions: V toggle ({self._player_position_mode.value})",
            f"Player update us: AoS {aos_time} | SoA {soa_time}",
            f"Faster player layout: {position_winner}",
        )

        self._hud_panel.fill((8, 12, 20, 220))
        pygame.draw.rect(self._hud_panel, (75, 155, 230), self._hud_panel.get_rect(), 2)
        for index, line in enumerate(lines):
            text = self._hud_font.render(line, True, (240, 245, 255))
            self._hud_panel.blit(text, (12, 8 + index * 24))

        self._screen.blit(self._hud_panel, (12, 12))

    def _average_position_time(self, mode: PlayerPositionMode) -> str:
        samples = self._player_position_samples[mode]
        if len(samples) < 30:
            return "measuring"
        return f"{sum(samples) / len(samples):.1f}"

    def _position_update_winner(self) -> str:
        aos_samples = self._player_position_samples[PlayerPositionMode.AOS]
        soa_samples = self._player_position_samples[PlayerPositionMode.SOA]
        if len(aos_samples) < 30 or len(soa_samples) < 30:
            return "measuring"
        aos_average = sum(aos_samples) / len(aos_samples)
        soa_average = sum(soa_samples) / len(soa_samples)
        if aos_average < soa_average:
            return "AoS"
        return "SoA"

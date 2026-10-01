from array import array
from enum import Enum
from importlib.resources import as_file, files

import pygame
from pygame.math import Vector2

from .entity import Entity
from .particle_emitter import ParticleEmitter, ParticleStorageMode


class PlayerPositionMode(Enum):
    AOS = "AoS"
    SOA = "SoA"


class PlayerPositionArrays:
    def __init__(self) -> None:
        # Matching indices across these arrays describe one player's state.
        self.x = array("d")
        self.y = array("d")
        self.speed = array("d")

    def append(self, position: Vector2, speed: float) -> None:
        self.x.append(position.x)
        self.y.append(position.y)
        self.speed.append(speed)

    def position(self, index: int) -> Vector2:
        return Vector2(self.x[index], self.y[index])

    def update(self, delta: float, screen_width: int, sprite_width: int) -> None:
        for index in range(len(self.x)):
            x = self.x[index] + self.speed[index] * delta
            if x >= screen_width:
                x = -sprite_width
            self.x[index] = x

    def truncate(self, count: int) -> None:
        # Players are removed from the end, so surviving indices stay stable.
        del self.x[count:]
        del self.y[count:]
        del self.speed[count:]

    def clear(self) -> None:
        self.truncate(0)


class Player(Entity):
    SPRITE_SIZE = 128
    _shared_texture: pygame.Surface | None = None

    def __init__(
        self,
        screen_width: int,
        spawn_position: Vector2,
    ) -> None:
        self._speed = 120
        self._screen_width = screen_width
        texture = Player._shared_texture
        if texture is None:
            rocket = files("cache_raiders").joinpath(
                "assets",
                "images",
                "rocket.png",
            )
            with as_file(rocket) as image_path:
                source = pygame.image.load(str(image_path)).convert_alpha()
            texture = pygame.transform.smoothscale(
                source,
                (self.SPRITE_SIZE, self.SPRITE_SIZE),
            )
            Player._shared_texture = texture
        self._texture = texture
        super().__init__()
        self._position = Vector2(spawn_position)
        self._position_arrays: PlayerPositionArrays | None = None
        self._position_index = 0
        self._emitter = ParticleEmitter()
        self.sync_emitter_position()

    @property
    def position(self) -> Vector2:
        if self._position_arrays is None:
            return self._position
        return self._position_arrays.position(self._position_index)

    @property
    def speed(self) -> float:
        if self._position_arrays is None:
            return self._speed
        return self._position_arrays.speed[self._position_index]

    @property
    def rect(self) -> pygame.Rect:
        return self._texture.get_rect(
            topleft=(int(self.position.x), int(self.position.y))
        )

    @property
    def particle_count(self) -> int:
        return self._emitter.particle_count

    def set_particle_storage_mode(self, mode: ParticleStorageMode) -> None:
        self._emitter.set_storage_mode(mode)

    def use_soa_positions(
        self,
        position_arrays: PlayerPositionArrays,
        index: int,
    ) -> None:
        if self._position_arrays is not None:
            return
        # Copy live state so switching layouts does not move the player.
        position_arrays.append(self._position, self._speed)
        self._position_arrays = position_arrays
        self._position_index = index

    def use_aos_position(self) -> None:
        if self._position_arrays is None:
            return
        self._position = self.position
        self._speed = self.speed
        self._position_arrays = None

    def render(self, surface: pygame.Surface) -> None:
        self.render_particles(surface)
        self.render_ship(surface)

    def render_particles(self, surface: pygame.Surface) -> None:
        self._emitter.render(surface)

    def render_ship(self, surface: pygame.Surface) -> None:
        surface.blit(self._texture, self.position)

    def update(self, delta: float) -> None:
        self.update_position(delta)
        self.sync_emitter_position()
        self.update_emitter(delta)

    def update_position(self, delta: float) -> None:
        if self._position_arrays is not None:
            index = self._position_index
            x = self._position_arrays.x[index] + self.speed * delta
            if x >= self._screen_width:
                x = -self._texture.get_width()
            self._position_arrays.x[index] = x
            return

        self._position.x += self._speed * delta
        if self._position.x >= self._screen_width:
            self._position.x = -self._texture.get_width()

    def update_emitter(self, delta: float) -> None:
        self._emitter.update(delta)

    def sync_emitter_position(self) -> None:
        self._emitter.set_position(self.position + Vector2(8, 64))

    def handle_input(self, event: pygame.event.Event) -> None:
        self._emitter.handle_input(event)
        if event.type != pygame.KEYDOWN:
            return

        plus_pressed = event.key == pygame.K_PLUS or (
            event.key == pygame.K_EQUALS and event.mod & pygame.KMOD_SHIFT
        )
        if plus_pressed:
            self._speed += 100
        elif event.key == pygame.K_MINUS:
            self._speed = max(0, self._speed - 100)
        if self._position_arrays is not None:
            self._position_arrays.speed[self._position_index] = self._speed

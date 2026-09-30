import pygame
from pygame.math import Vector2

from .entity import Entity
from .particle_emitter import ParticleEmitter


class Player(Entity):
    def __init__(self, screen_width: int) -> None:
        self._speed = 120
        self._screen_width = screen_width
        texture = pygame.image.load("assets/images/rocket.png").convert_alpha()
        self._texture = pygame.transform.smoothscale(texture, (128, 128))
        super().__init__()
        self._emitter = ParticleEmitter()
        self._sync_emitter_position()

    def render(self, surface: pygame.Surface) -> None:
        self._emitter.render(surface)
        surface.blit(self._texture, self._position)

    def update(self, delta: float) -> None:
        self._position.x += self._speed * delta
        if self._position.x >= self._screen_width:
            self._position.x = -self._texture.get_width()
        self._sync_emitter_position()
        self._emitter.update(delta)

    def handle_input(self, event: pygame.event.Event) -> None:
        self._emitter.handle_input(event)
        if event.type != pygame.KEYDOWN:
            return

        plus_pressed = event.key == pygame.K_PLUS or (
            event.key == pygame.K_EQUALS and event.mod & pygame.KMOD_SHIFT
        )
        if plus_pressed:
            self._speed += 100

    def _sync_emitter_position(self) -> None:
        self._emitter.set_position(self._position + Vector2(8, 64))

import pygame
from pygame.math import Vector2

from .entity import Entity
from .particle_emitter import ParticleEmitter


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
            source = pygame.image.load("assets/images/rocket.png").convert_alpha()
            texture = pygame.transform.smoothscale(
                source,
                (self.SPRITE_SIZE, self.SPRITE_SIZE),
            )
            Player._shared_texture = texture
        self._texture = texture
        super().__init__()
        self._position = Vector2(spawn_position)
        self._emitter = ParticleEmitter()
        self._sync_emitter_position()

    @property
    def rect(self) -> pygame.Rect:
        return self._texture.get_rect(
            topleft=(int(self._position.x), int(self._position.y))
        )

    @property
    def particle_count(self) -> int:
        return self._emitter.particle_count

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
        elif event.key == pygame.K_MINUS:
            self._speed = max(0, self._speed - 100)

    def _sync_emitter_position(self) -> None:
        self._emitter.set_position(self._position + Vector2(8, 64))

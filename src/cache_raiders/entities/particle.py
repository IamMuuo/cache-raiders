import pygame
from pygame.math import Vector2

from .entity import Entity


class Particle(Entity):
    def __init__(
        self,
        position: Vector2,
        velocity: Vector2,
        lifetime: float,
        color: tuple[int, int, int],
        radius: int = 3,
        initial_age: float = 0.0,
    ) -> None:
        super().__init__()
        if lifetime <= 0:
            raise ValueError("Particle lifetime must be positive")
        if radius <= 0:
            raise ValueError("Particle radius must be positive")

        self._position = Vector2(position)
        self._velocity = Vector2(velocity)
        self._lifetime = lifetime
        self._age = initial_age
        self._color = color
        self._radius = radius

        diameter = radius * 2
        self._surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(self._surface, color, (radius, radius), radius)

    @property
    def is_alive(self) -> bool:
        return self._age < self._lifetime

    @property
    def position(self) -> Vector2:
        return self._position

    @property
    def velocity(self) -> Vector2:
        return self._velocity

    @property
    def lifetime(self) -> float:
        return self._lifetime

    @property
    def age(self) -> float:
        return self._age

    @property
    def color(self) -> tuple[int, int, int]:
        return self._color

    @property
    def radius(self) -> int:
        return self._radius

    def render(self, surface: pygame.Surface) -> None:
        opacity = max(0.0, 1.0 - self._age / self._lifetime)
        self._surface.set_alpha(round(opacity * 255))
        surface.blit(
            self._surface,
            (
                round(self._position.x - self._radius),
                round(self._position.y - self._radius),
            ),
        )

    def update(self, delta: float) -> None:
        self._position += self._velocity * delta
        self._age += delta

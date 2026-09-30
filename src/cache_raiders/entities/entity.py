from abc import ABC, abstractmethod
import pygame
from pygame.math import Vector2


class Entity(ABC):
    def __init__(self) -> None:
        self._position: Vector2 = Vector2()
        self._size: Vector2 = Vector2()
        self._velocity: Vector2 = Vector2()

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, delta: float) -> None:
        raise NotImplementedError

    def handle_input(self) -> None:
        pass

import random

import pygame
from pygame.math import Vector2

from .entity import Entity
from .particle import Particle


class ParticleEmitter(Entity):
    def __init__(
        self,
        emission_interval: float = 0.02,
        particle_lifetime: float = 2.4,
    ) -> None:
        super().__init__()
        if emission_interval <= 0:
            raise ValueError("Emission interval must be positive")
        if particle_lifetime <= 0:
            raise ValueError("Particle lifetime must be positive")

        self._emission_interval = emission_interval
        self._particle_lifetime = particle_lifetime
        self._time_since_emission = 0.0
        self._particles_per_emission = 1
        self._particles: list[Particle] = []

    def set_position(self, position: Vector2) -> None:
        self._position = Vector2(position)

    def render(self, surface: pygame.Surface) -> None:
        for particle in self._particles:
            particle.render(surface)

    def update(self, delta: float) -> None:
        for particle in self._particles:
            particle.update(delta)
        self._particles = [particle for particle in self._particles if particle.is_alive]

        self._time_since_emission += delta
        while self._time_since_emission >= self._emission_interval:
            self._time_since_emission -= self._emission_interval
            for _ in range(self._particles_per_emission):
                self._emit_particle()

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_p:
            self._particles_per_emission += 1
            self._emit_burst(60)
        elif event.key == pygame.K_o:
            self._particles_per_emission = max(0, self._particles_per_emission - 1)

    def _emit_burst(self, count: int) -> None:
        for _ in range(count):
            self._emit_particle(burst=True)

    def _emit_particle(self, burst: bool = False) -> None:
        if burst:
            velocity = Vector2(random.uniform(-180, 90), random.uniform(-150, 150))
            radius = random.randint(3, 7)
        else:
            velocity = Vector2(random.uniform(-120, -55), random.uniform(-45, 45))
            radius = random.randint(2, 5)

        color = random.choice(((70, 175, 255), (130, 220, 255), (255, 190, 90)))
        self._particles.append(
            Particle(
                self._position,
                velocity,
                self._particle_lifetime,
                color,
                radius,
            )
        )

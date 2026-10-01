import random
from array import array
from enum import Enum
from functools import lru_cache

import pygame
from pygame.math import Vector2

from .entity import Entity
from .particle import Particle

PARTICLE_COLORS = ((70, 175, 255), (130, 220, 255), (255, 190, 90))


class ParticleStorageMode(Enum):
    AOS = "AoS"
    SOA = "SoA"


class _SoAParticles:
    def __init__(self) -> None:
        self.x = array("d")
        self.y = array("d")
        self.velocity_x = array("d")
        self.velocity_y = array("d")
        self.age = array("d")
        self.lifetime = array("d")
        self.radius = array("B")
        self.color_index = array("B")

    def __len__(self) -> int:
        return len(self.x)

    def append(
        self,
        x: float,
        y: float,
        velocity_x: float,
        velocity_y: float,
        age: float,
        lifetime: float,
        radius: int,
        color_index: int,
    ) -> None:
        self.x.append(x)
        self.y.append(y)
        self.velocity_x.append(velocity_x)
        self.velocity_y.append(velocity_y)
        self.age.append(age)
        self.lifetime.append(lifetime)
        self.radius.append(radius)
        self.color_index.append(color_index)

    def update(self, delta: float) -> None:
        write_index = 0
        # Pack survivors forward while keeping each particle's fields aligned.
        for read_index in range(len(self)):
            age = self.age[read_index] + delta
            if age >= self.lifetime[read_index]:
                continue

            x = self.x[read_index] + self.velocity_x[read_index] * delta
            y = self.y[read_index] + self.velocity_y[read_index] * delta
            self.x[write_index] = x
            self.y[write_index] = y
            self.velocity_x[write_index] = self.velocity_x[read_index]
            self.velocity_y[write_index] = self.velocity_y[read_index]
            self.age[write_index] = age
            self.lifetime[write_index] = self.lifetime[read_index]
            self.radius[write_index] = self.radius[read_index]
            self.color_index[write_index] = self.color_index[read_index]
            write_index += 1

        for values in self._arrays():
            del values[write_index:]

    def render(self, surface: pygame.Surface) -> None:
        for index in range(len(self)):
            opacity = max(0.0, 1.0 - self.age[index] / self.lifetime[index])
            sprite = _particle_sprite(
                self.color_index[index],
                self.radius[index],
            )
            # Cached sprites are shared; set this particle's fade before blitting.
            sprite.set_alpha(round(opacity * 255))
            surface.blit(
                sprite,
                (
                    round(self.x[index] - self.radius[index]),
                    round(self.y[index] - self.radius[index]),
                ),
            )

    def to_particles(self) -> list[Particle]:
        return [
            Particle(
                Vector2(self.x[index], self.y[index]),
                Vector2(self.velocity_x[index], self.velocity_y[index]),
                self.lifetime[index],
                PARTICLE_COLORS[self.color_index[index]],
                self.radius[index],
                self.age[index],
            )
            for index in range(len(self))
        ]

    def clear(self) -> None:
        for values in self._arrays():
            del values[:]

    def _arrays(self) -> tuple[array, ...]:
        return (
            self.x,
            self.y,
            self.velocity_x,
            self.velocity_y,
            self.age,
            self.lifetime,
            self.radius,
            self.color_index,
        )


@lru_cache(maxsize=None)
def _particle_sprite(color_index: int, radius: int) -> pygame.Surface:
    diameter = radius * 2
    sprite = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    pygame.draw.circle(
        sprite,
        PARTICLE_COLORS[color_index],
        (radius, radius),
        radius,
    )
    return sprite


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
        self._soa_particles = _SoAParticles()
        self._storage_mode = ParticleStorageMode.AOS

    @property
    def particle_count(self) -> int:
        if self._storage_mode is ParticleStorageMode.AOS:
            return len(self._particles)
        return len(self._soa_particles)

    def set_storage_mode(self, mode: ParticleStorageMode) -> None:
        if mode is self._storage_mode:
            return

        # Convert live particles instead of clearing them when B changes modes.
        if mode is ParticleStorageMode.SOA:
            for particle in self._particles:
                self._soa_particles.append(
                    particle.position.x,
                    particle.position.y,
                    particle.velocity.x,
                    particle.velocity.y,
                    particle.age,
                    particle.lifetime,
                    particle.radius,
                    PARTICLE_COLORS.index(particle.color),
                )
            self._particles.clear()
        else:
            self._particles = self._soa_particles.to_particles()
            self._soa_particles.clear()

        self._storage_mode = mode

    def set_position(self, position: Vector2) -> None:
        self._position = Vector2(position)

    def render(self, surface: pygame.Surface) -> None:
        if self._storage_mode is ParticleStorageMode.AOS:
            for particle in self._particles:
                particle.render(surface)
        else:
            self._soa_particles.render(surface)

    def update(self, delta: float) -> None:
        if self._storage_mode is ParticleStorageMode.AOS:
            for particle in self._particles:
                particle.update(delta)
            self._particles = [
                particle for particle in self._particles if particle.is_alive
            ]
        else:
            self._soa_particles.update(delta)

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

        color_index = random.randrange(len(PARTICLE_COLORS))
        color = PARTICLE_COLORS[color_index]
        if self._storage_mode is ParticleStorageMode.AOS:
            self._particles.append(
                Particle(
                    self._position,
                    velocity,
                    self._particle_lifetime,
                    color,
                    radius,
                )
            )
        else:
            self._soa_particles.append(
                self._position.x,
                self._position.y,
                velocity.x,
                velocity.y,
                0.0,
                self._particle_lifetime,
                radius,
                color_index,
            )

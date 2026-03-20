from __future__ import annotations

import math
import random
import pygame

from enemy import Enemy
from player import Player


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Last Stand: Ant Horde")

        self.size = (800, 600)
        self.screen = pygame.display.set_mode(self.size)
        self.clock = pygame.time.Clock()

        self.running = True
        self.state: str = "menu"  # menu | playing

        # Basic font (fallback if system font missing).
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self._reset_run()

    def _reset_run(self) -> None:
        self.wave = 1
        self.phase: str = "player"  # player | enemy
        self.phase_timer = 0.0

        self.player = Player(pos=pygame.Vector2(self.size[0] / 2, self.size[1] / 2))
        self.enemies: list[Enemy] = []
        self._spawn_wave()

    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()
        return 0

    def _handle_event(self, event: pygame.event.Event) -> None:
        if self.state == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = "playing"
                    self._reset_run()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
        elif self.state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    return

                # End player turn manually (cards arrive step 2).
                if self.phase == "player" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._start_enemy_phase()

                # Temporary attack to be able to clear waves (replaced by cards in step 2).
                if self.phase == "player" and event.key == pygame.K_f:
                    self._basic_attack()

    def _update(self, dt: float) -> None:
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        if self.phase == "player":
            move = pygame.Vector2(0, 0)
            if keys[pygame.K_w] or keys[pygame.K_z]:
                move.y -= 1
            if keys[pygame.K_s]:
                move.y += 1
            if keys[pygame.K_a] or keys[pygame.K_q]:
                move.x -= 1
            if keys[pygame.K_d]:
                move.x += 1

            if move.length_squared() > 0:
                move = move.normalize()
                self.player.pos += move * self.player.move_speed * dt
                self.player.clamp_to_arena(*self.size)

        else:
            self.phase_timer += dt

            # Move enemies a bit towards the player during enemy phase.
            for e in self.enemies:
                direction = self.player.pos - e.pos
                if direction.length_squared() > 0.0001:
                    e.pos += direction.normalize() * e.speed * dt

            # If enemy touches player, apply damage and end enemy phase quickly.
            if self._any_enemy_touching_player():
                self._apply_enemy_damage()
                self._start_player_phase()
            elif self.phase_timer >= 1.0:
                # Auto-end enemy phase after a short delay.
                self._start_player_phase()

        # Wave progression.
        self.enemies = [e for e in self.enemies if e.hp > 0]
        if not self.enemies:
            self.player.score += 10
            self.wave += 1
            self._spawn_wave()
            self._start_player_phase()

        # Game over.
        if self.player.hp <= 0:
            self.state = "menu"

    def _draw(self) -> None:
        if self.state == "menu":
            self.screen.fill((25, 25, 25))
            self._draw_centered("Last Stand: Ant Horde", y=220)
            self._draw_centered("[ENTRÉE] Jouer", y=290)
            self._draw_centered("[ÉCHAP] Quitter", y=330)
        else:
            self.screen.fill((35, 35, 35))
            self._draw_arena()
            self._draw_entities()
            self._draw_hud()

    def _draw_centered(self, text: str, *, y: int) -> None:
        surf = self.font.render(text, True, (235, 235, 235))
        rect = surf.get_rect(center=(self.size[0] // 2, y))
        self.screen.blit(surf, rect)

    def _draw_arena(self) -> None:
        pygame.draw.rect(self.screen, (55, 55, 55), pygame.Rect(20, 20, self.size[0] - 40, self.size[1] - 40), 2)

    def _draw_entities(self) -> None:
        # Player
        pygame.draw.circle(self.screen, self.player.color, (int(self.player.pos.x), int(self.player.pos.y)), self.player.radius)

        # Enemies
        for e in self.enemies:
            pygame.draw.circle(self.screen, e.color, (int(e.pos.x), int(e.pos.y)), e.radius)

    def _draw_hud(self) -> None:
        def blit_line(text: str, x: int, y: int) -> None:
            self.screen.blit(self.small_font.render(text, True, (230, 230, 230)), (x, y))

        blit_line(f"PV: {self.player.hp}", 20, 6)
        blit_line(f"Vague: {self.wave}", 120, 6)
        blit_line(f"Score: {self.player.score}", 220, 6)
        blit_line(f"Phase: {'Joueur' if self.phase == 'player' else 'Ennemis'}", 340, 6)

        if self.phase == "player":
            blit_line("[F] Attaque (temporaire)", 20, 30)
            blit_line("[ENTRÉE/Espace] Fin du tour", 220, 30)
        else:
            blit_line("Tour des ennemis...", 20, 30)

    def _spawn_wave(self) -> None:
        # GDD: ennemis = 3 + vague
        count = 3 + self.wave
        for i in range(count):
            kind = self._pick_enemy_kind(i)
            enemy = self._make_enemy(kind)
            self.enemies.append(enemy)

    def _pick_enemy_kind(self, i: int) -> str:
        # Keep variety low for MVP; more tuning later.
        if self.wave >= 3 and i % 5 == 0:
            return "armored"
        if self.wave >= 2 and i % 3 == 0:
            return "fast"
        return "normal"

    def _make_enemy(self, kind: str) -> Enemy:
        # Spawn on arena borders, away from player.
        w, h = self.size
        margin = 25
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            pos = pygame.Vector2(random.uniform(margin, w - margin), margin)
        elif side == "bottom":
            pos = pygame.Vector2(random.uniform(margin, w - margin), h - margin)
        elif side == "left":
            pos = pygame.Vector2(margin, random.uniform(margin, h - margin))
        else:
            pos = pygame.Vector2(w - margin, random.uniform(margin, h - margin))

        # Stats from GDD (adapted by kind).
        if kind == "fast":
            hp = 8 + self.wave
            damage = 3 + self.wave
            speed = 165.0
        elif kind == "armored":
            hp = 20 + self.wave * 3
            damage = 4 + self.wave
            speed = 85.0
        else:
            hp = 10 + self.wave * 2
            damage = 2 + self.wave
            speed = 115.0

        return Enemy(kind=kind, pos=pos, hp=hp, damage=damage, speed=speed)

    def _start_enemy_phase(self) -> None:
        self.phase = "enemy"
        self.phase_timer = 0.0

    def _start_player_phase(self) -> None:
        self.phase = "player"
        self.phase_timer = 0.0

    def _any_enemy_touching_player(self) -> bool:
        for e in self.enemies:
            if (e.pos - self.player.pos).length() <= (e.radius + self.player.radius):
                return True
        return False

    def _apply_enemy_damage(self) -> None:
        total = 0
        for e in self.enemies:
            if (e.pos - self.player.pos).length() <= (e.radius + self.player.radius):
                total += e.damage
        self.player.hp -= total

    def _basic_attack(self) -> None:
        # Temporary: hit the closest enemy in range.
        if not self.enemies:
            return

        best: Enemy | None = None
        best_d2 = math.inf
        for e in self.enemies:
            d2 = (e.pos - self.player.pos).length_squared()
            if d2 < best_d2:
                best_d2 = d2
                best = e

        if best is None:
            return

        max_range = 95.0
        if best_d2 <= max_range * max_range:
            best.hp -= 10


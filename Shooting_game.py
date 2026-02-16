import pygame
import random
import sys

# =====================
# SETTINGS
# =====================
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_SPEED = 5
PLAYER_HEALTH = 100
BULLET_SPEED = -12  # Increased speed for better responsiveness
ENEMY_SPEED = 2  # Slightly slower to give player more time to shoot
SPAWN_DELAY = 1200  # More forgiving spawn rate
ESCAPED_ENEMY_DAMAGE = 20  # Damage for each escaped enemy
ENEMY_DAMAGE = 15  # Increased damage when enemy reaches player
POWERUP_CHANCE = 0.1

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,200,255)
YELLOW = (255,255,0)

MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"

pygame.init()
pygame.mixer.init()

# =====================
# PLAYER CLASS
# =====================
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((50, 60))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.health = PLAYER_HEALTH
        self.speed = PLAYER_SPEED
        self.last_shot = 0
        self.shoot_delay = 300

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.y)  # Shoot from center of player top
            self.game.all_sprites.add(bullet)
            self.game.bullets.add(bullet)

# =====================
# BULLET CLASS
# =====================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))  # Larger bullet for better visibility
        self.image.fill(YELLOW)
        # Draw a bright outline for better visibility
        pygame.draw.rect(self.image, WHITE, (0, 0, 10, 20), 1)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y  # Bullets spawn just above the player

    def update(self):
        self.rect.y += BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

# =====================
# ENEMY CLASS (GetForce Shooter)
# =====================
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Create a small GetForce shooter object (diamond-shaped)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        # Draw a diamond shape for GetForce shooter
        points = [(15, 0), (30, 15), (15, 30), (0, 15)]
        pygame.draw.polygon(self.image, RED, points)
        # Add a center dot
        pygame.draw.circle(self.image, YELLOW, (15, 15), 3)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -30
        self.escaped = False  # Track if enemy escaped

    def update(self):
        self.rect.y += ENEMY_SPEED
        if self.rect.top > HEIGHT:
            # Mark as escaped but don't kill yet - let play_loop handle it
            self.escaped = True

# =====================
# POWERUP CLASS
# =====================
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice(["health", "rapid"])
        self.image = pygame.Surface((25,25))
        self.image.fill(GREEN if self.type == "health" else YELLOW)
        self.rect = self.image.get_rect(center=(x,y))

    def update(self):
        self.rect.y += 3
        if self.rect.top > HEIGHT:
            self.kill()

# =====================
# GAME CLASS
# =====================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("GetForce Shooter")
        self.clock = pygame.time.Clock()
        self.state = MENU
        self.running = True
        self.font = pygame.font.SysFont(None, 36)

        self.bg_y1 = 0
        self.bg_y2 = -HEIGHT

    def new_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        self.player = Player(self)
        self.all_sprites.add(self.player)

        self.score = 0
        self.last_spawn = pygame.time.get_ticks()
        self.game_time = 0  # Track game duration for difficulty scaling

    def run(self):
        while self.running:
            if self.state == MENU:
                self.menu_loop()
            elif self.state == PLAYING:
                self.play_loop()
            elif self.state == GAME_OVER:
                self.game_over_loop()

    def menu_loop(self):
        while self.state == MENU:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.state = None
                if event.type == pygame.KEYDOWN:
                    self.new_game()
                    self.state = PLAYING

            self.screen.fill(BLACK)
            text = self.font.render("Press Any Key to Start", True, WHITE)
            self.screen.blit(text, (WIDTH//2 - 150, HEIGHT//2))
            pygame.display.flip()

    def play_loop(self):
        while self.state == PLAYING:
            self.clock.tick(FPS)
            self.game_time += self.clock.get_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.state = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.shoot()

            # Auto-shooting mechanism - continuous bullets
            self.player.shoot()

            # Dynamic difficulty: Spawn enemies faster as score increases (more carefully)
            current_spawn_delay = max(600, SPAWN_DELAY - (self.score // 100) * 100)
            
            # Spawn enemies
            now = pygame.time.get_ticks()
            if now - self.last_spawn > current_spawn_delay:
                enemy = Enemy()
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.last_spawn = now

            self.all_sprites.update()

            # Bullet hits - Destroy enemies with bullets
            hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
            for hit in hits:
                self.score += 10
                if random.random() < POWERUP_CHANCE:
                    power = PowerUp(hit.rect.centerx, hit.rect.centery)
                    self.all_sprites.add(power)
                    self.powerups.add(power)

            # Check for escaped enemies (reached bottom without being destroyed)
            escaped_enemies = [enemy for enemy in self.enemies if enemy.escaped]
            for enemy in escaped_enemies:
                self.player.health -= ESCAPED_ENEMY_DAMAGE
                enemy.kill()  # Now remove from all groups
                if self.player.health <= 0:
                    self.state = GAME_OVER

            # Enemy hits player - COMPULSORY ELIMINATION: High damage if not destroyed
            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            for hit in hits:
                self.player.health -= ENEMY_DAMAGE  # Use ENEMY_DAMAGE constant
                if self.player.health <= 0:
                    self.state = GAME_OVER

            # Powerups
            hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for hit in hits:
                if hit.type == "health":
                    self.player.health = min(PLAYER_HEALTH, self.player.health + 20)
                if hit.type == "rapid":
                    self.player.shoot_delay = 100

            self.draw()

    def game_over_loop(self):
        while self.state == GAME_OVER:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.state = None
                if event.type == pygame.KEYDOWN:
                    self.state = MENU

            self.screen.fill(BLACK)
            text = self.font.render(f"Game Over! Score: {self.score}", True, WHITE)
            self.screen.blit(text, (WIDTH//2 - 160, HEIGHT//2))
            pygame.display.flip()

    def draw(self):
        self.screen.fill((20,20,30))
        self.all_sprites.draw(self.screen)

        # Health bar
        pygame.draw.rect(self.screen, RED, (10,10,100,10))
        pygame.draw.rect(self.screen, GREEN, (10,10,100*(self.player.health/PLAYER_HEALTH),10))

        # Health text
        health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (10, 30))

        # Score text - fixed positioning
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect()
        score_rect.topright = (WIDTH - 10, 10)
        self.screen.blit(score_text, score_rect)

        # Difficulty level indicator
        difficulty_level = min(5, (self.score // 100) + 1)
        difficulty_text = self.font.render(f"Level: {difficulty_level}", True, YELLOW)
        difficulty_rect = difficulty_text.get_rect()
        difficulty_rect.topright = (WIDTH - 10, 50)
        self.screen.blit(difficulty_text, difficulty_rect)

        # Enemy count indicator
        enemy_count = len(self.enemies)
        enemy_text = self.font.render(f"Enemies: {enemy_count}", True, BLUE)
        self.screen.blit(enemy_text, (10, 60))

        # Warning text if health is low
        if self.player.health <= 30:
            warning_text = self.font.render("CRITICAL HEALTH!", True, RED)
            warning_rect = warning_text.get_rect()
            warning_rect.center = (WIDTH // 2, 50)
            self.screen.blit(warning_text, warning_rect)

        pygame.display.flip()


# =====================
# START GAME
# =====================
game = Game()
game.run()

pygame.quit()
sys.exit()

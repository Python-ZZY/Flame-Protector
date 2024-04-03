try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

import pygame as pg
import math
import random
import sys
import os

vec = pg.math.Vector2

WIDTH, HEIGHT = 800, 600
FIRE_SIZE = 300
ADD_PARTICLES = pg.USEREVENT

def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

def temp_to_color(temp):
    temp /= 100

    red = 0
    green = 0
    blue = 0

    if temp <= 66:
        red = 255
        green = temp
        green = 99.4708025861 * math.log(green) - 161.1195681661

        if temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
    else:
        red = temp - 60
        red = 329.698727446 * math.pow(red, -0.1332047592)

        green = temp - 60
        green = 288.1221695283 * math.pow(green, -0.0755148492)

        blue = 255

    red = min(max(red, 0), 255)
    green = min(max(green, 0), 255)
    blue = min(max(blue, 0), 255)

    return int(red), int(green), int(blue)

class Scene:
    def __init__(self, fps=60, loop=True):
        self.screen = pg.display.get_surface()
        self.fps = fps
        self.clock = pg.time.Clock()
        self.scene_running = False

        self.effect_sprites = pg.sprite.Group()

        self.init()
        if loop:
            self.loop()

    def init(self):
        pass

    def loop(self):
        self.scene_running = True
        while self.scene_running:
            self.screen.fill((0, 0, 0))
            self.update()
            self.draw()
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.onexit()
                self.events(event)
            
            self.clock.tick(self.fps)
            pg.display.flip()

    def onexit(self):
        self.quit_scene()
        
    def quit_scene(self):
        self.scene_running = False

    def draw(self):
        pass
    
    def update(self):
        pass

    def events(self, event):
        pass
    
class Particle(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        
        self.speed = -pg.math.clamp(game.temp / 500, 1.4, 3)
        self.offset = random.random() * .006
        self.origin_x = x
        
        self.color_offset = random.randint(1200, 1800)
        
        s = pg.math.clamp((game.temp + y) / 100, 16, 30)
        self.image = pg.Surface((s, s))
        self.image.fill(temp_to_color(self.game.temp))
        self.rect = self.image.get_frect(center=(x, y))
        self.last_color = 0

    def update(self):
        self.rect.x = self.origin_x + math.cos(pg.time.get_ticks() * self.offset) * 10
        self.rect.y += self.speed

        if random.random() < 0.045:
            self.image = pg.transform.scale_by(self.image, 0.9)
            self.rect = self.image.get_rect(center=self.rect.center)
            if self.rect.width <= 3:
                self.kill()
                return

        if self.rect.bottom < 0 or self.rect.x > WIDTH or self.rect.right < 0:
            self.kill()
            return

        now = pg.time.get_ticks()
        if now - self.last_color >= 200:
            self.last_color = now
            self.image.fill(temp_to_color(self.game.temp + (self.rect.y / HEIGHT) * self.color_offset))
        
class Game(Scene):
    best_score = 0
    
    def init(self):
        pg.mixer.music.load(get_path("assets/flame.mp3"))
        pg.mixer.music.play(-1)

        self.temp = random.randint(7000, 9000)
        
        self.fire = pg.sprite.Group()
        self.fire_pos = ((WIDTH - FIRE_SIZE) / 2, (WIDTH + FIRE_SIZE) / 2)

        self.last_add_particle = 0
        self.last_update_clock = 0
        self.start_game_time = pg.time.get_ticks()
        
        self.font = pg.font.Font(get_path("assets/font.ttf"), 18)
        self.update_tip("Feed me more files as fuel!")
        self.update_clock(self.start_game_time)
        
        self.files = []
        self.score = 0

    @property
    def alive(self):
        return self.temp > 1000
        
    def add_temp(self, value):
        self.temp = pg.math.clamp(int(self.temp + value), 1000, 9000)
        self.update_tip(self.tip)

    def update_tip(self, tip):
        self.tip = tip
        self.temp_r = self.font.render(f"Temperature: {self.temp}K\n{self.tip}", True, temp_to_color(self.temp))

    def update_clock(self, now=None):
        if now: self.score = int((now - self.start_game_time) / 1000)
        self.clock_r = self.font.render(f"Score: {self.score}\nBest score: {self.best_score}", True, (255, 255, 255))
        
    def events(self, event):
        if self.alive:
            if event.type == pg.DROPFILE:
                if event.file in self.files:
                    self.update_tip("This file has been thrown into the fire!")
                else:
                    self.files.append(event.file)
                    size = os.path.getsize(event.file)
                    self.add_temp(n := int(size / 20))
                    self.update_tip(f"This file is {size}B.\nTemperature +{n}K")
                    pg.mixer.Sound(get_path("assets/gain.mp3")).play()

        else:
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                self.init()
                
    def update(self):
        self.fire.update()
        
        if self.alive:
            now = pg.time.get_ticks()
            if now - self.last_add_particle >= 300:
                self.last_add_particle = now
                
                for i in range(70):
                    self.fire.add(Particle(self, random.randint(self.fire_pos[0], self.fire_pos[1]), HEIGHT + random.randint(0, 100)))
                    # self.fire.add(Particle(self, random.randint(*self.fire_pos), HEIGHT + random.randint(0, 100)))
                    # python version problems

                self.add_temp(-100)
                if not self.alive:
                    if self.score > self.best_score:
                        self.best_score = self.score
                        self.update_clock()
                    self.update_tip("Game Over!\nPress <Spacebar> to reset the fire")

            if now - self.last_update_clock >= 1000:
                self.last_update_clock = now
                self.update_clock(now)
            
    def draw(self):
        self.screen.fill((0, 0, 0))
        self.fire.draw(self.screen)
        self.screen.blit(self.temp_r, (10, 10))
        self.screen.blit(self.clock_r, (WIDTH - self.clock_r.get_width() - 10, 10))

if __name__ == "__main__":
    pg.init()
    pg.display.set_mode((WIDTH, HEIGHT), pg.SCALED)
    pg.display.set_caption("Flame Protector")
    pg.display.set_icon(pg.image.load(get_path("assets/icon.ico")))
    Game()

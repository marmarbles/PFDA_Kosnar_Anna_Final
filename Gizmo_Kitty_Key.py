import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Gizmo's Kitty Key Adventure!")

WIDTH, HEIGHT = 1000, 800
FPS = 45
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, direction=False):
    path = join(dir1, dir2)  # Corrected path joining
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        frames = int(image[0])
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        width = sprite_sheet.get_width() // frames
        height = sprite_sheet.get_height()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        image = image[1:]
        if direction:
            all_sprites[image.replace(".png", "_left")] = sprites
            all_sprites[image.replace(".png", "_right")] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height):
        super().__init__()
        self.sprite = None
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.SPRITES = load_sprite_sheets("Sprites", "",  True)
        self.jump_count = 0
        self.onFloor = False
        self.corrected = False

    def jump(self):
        self.rect.y -= self.rect.h
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0 
        self.jump_count = 1 
        if self.jump_count == 1:
            self.fall_count = 0 

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        if (self.rect.y > 700):
            self.rect.y = 673
            self.y_vel = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def landed(self):
        self.fall_count = 0 
        self.y_vel = 0 
        self.jump_count = 0 
        self.onFloor = True

    def hit_head(self):
        self.count = 0 
        self.y_vel *= -1 

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.y_vel != 0:
            if self.jump_count == 1:
                sprite_sheet = "run"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet.capitalize() + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.mask = pygame.mask.from_surface(self.sprite)
        self.animation_count += 1

    def loop(self, fps):
        if not self.onFloor:
            self.y_vel += (self.fall_count / fps) * self.GRAVITY
            self.corrected = False
        self.move(self.x_vel, self.y_vel)
        if self.onFloor and not self.corrected:
            self.rect.y -= self.rect.h
            self.corrected = True

        self.fall_count += 1
        self.update_sprite()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.update()

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        


def get_background(name):
    image = pygame.image.load(join("Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            # elif dy < 0:
            #     player.rect.top = obj.rect.bottom 
            #     player.hit_head()

        collided_objects.append(obj)
   
    return collided_objects 

 

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    if keys[pygame.K_a]:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d]:
        player.move_right(PLAYER_VEL)
    if keys[pygame.K_SPACE] and player.onFloor:
        player.onFloor = False
        player.jump()

    handle_vertical_collision(player, objects, player.y_vel)


def main():
    clock = pygame.time.Clock()
    background, bg_image = get_background("PFDA_Background.png")

    block_size = 96

    player = Player(100, 100, 40, 31)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(WIDTH // block_size + 1)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),  Block(block_size * 4, HEIGHT - block_size * 4, block_size),
                Block(block_size * 7, HEIGHT - block_size * 6, block_size),  Block(block_size * 8, HEIGHT - block_size * 6, block_size),  
                Block(block_size * 9, HEIGHT - block_size * 6, block_size)]
    offset_x = 0 
    scroll_area_width = 200 

    pygame.mixer.music.load("Pawprint_Panic!.mp3")
    pygame.mixer.music.play(-1)  # -1 means loop indefinitely

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        # if event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_SPACE and player.jump_count < 2:
        #             player.jump()

        player.loop(FPS)
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0 ):
            offset_x += player.x_vel 

    pygame.quit()
    quit()


if __name__ == "__main__":
    main()

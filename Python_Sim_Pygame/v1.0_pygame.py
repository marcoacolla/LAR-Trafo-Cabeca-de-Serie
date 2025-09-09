import pygame
from World.World import World as world
import os
from Player.Player import Player
from Camera.Camera import Camera

pygame.init()
screen = pygame.display.set_mode((800, 600))  # largura x altura
pygame.display.set_caption("Minha Janela Pygame")




# Carregar imagem do mapa
map_path = os.path.join(os.path.dirname(__file__), 'World', 'Obstacles', 'Untitled.png')
map_image = pygame.image.load(map_path).convert()

PLAYER_SIZE = 40
from World.World import World
SPAWN_X, SPAWN_Y = World.find_spawnpoint(map_image, PLAYER_SIZE)
player = Player(SPAWN_X, SPAWN_Y)
camera = Camera(800, 600)

clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.move(keys)

    # Verificar colisão do player com paredes
    player_rect = pygame.Rect(player.x, player.y, player.size, player.size)
    if player.state == 'vivo':
        for px in range(player_rect.left, player_rect.right):
            for py in range(player_rect.top, player_rect.bottom):
                if 0 <= px < map_image.get_width() and 0 <= py < map_image.get_height():
                    cor = map_image.get_at((px, py))[:3]
                    # Verde não é parede
                    if cor == (255, 255, 255):
                        continue
                    player.set_dead()
                    break
            if player.is_dead():
                break

    camera.update(player)

    # Desenhar o mapa com deslocamento da câmera
    screen.fill((220, 230, 255))
    screen.blit(map_image, (-camera.offset_x, -camera.offset_y))

    # Desenhar o player centralizado usando a câmera
    centered_rect = camera.apply(player_rect)
    player.draw(screen)

    if player.is_dead():
        def reset_player():
            player.set_alive(SPAWN_X, SPAWN_Y)
        camera.death_screen(screen, player, reset_player)
        continue
    pygame.display.flip()
    clock.tick(60)
    



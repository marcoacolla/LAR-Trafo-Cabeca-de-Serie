import pygame
from World.World import World as world
import os
from Player.Player import Player
from Camera.Camera import Camera
from Player.Pathing.Curvature import Curvature

pygame.init()
screen = pygame.display.set_mode((800, 600))  # largura x altura
pygame.display.set_caption("Minha Janela Pygame")




# Carregar imagem do mapa
map_path = os.path.join(os.path.dirname(__file__), 'World', 'Obstacles', 'Untitled.png')
map_image = pygame.image.load(map_path).convert()

from World.World import World
SPAWN_POINT = (200,200)
camera = Camera(800, 600)
player = Player(SPAWN_POINT, screen, camera)


clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.move(keys)



    # Atualiza câmera antes de desenhar (offset/scale)
    camera.update(player)

    # Limpa e desenha o mapa (aplica escala)
    screen.fill((220, 230, 255))
    if hasattr(camera, 'scale') and camera.scale != 1.0:
        map_w = int(map_image.get_width() * camera.scale)
        map_h = int(map_image.get_height() * camera.scale)
        scaled_map = pygame.transform.scale(map_image, (map_w, map_h))
        screen.blit(scaled_map, (-camera.offset_x * camera.scale, -camera.offset_y * camera.scale))
    else:
        screen.blit(map_image, (-camera.offset_x, -camera.offset_y))


    # Verificar colisão do player com paredes usando hitbox rotacionada
    # Obtemos dois polígonos: um em coordenadas de tela para debug, e outro em
    # coordenadas do mundo para a checagem e amostragem de pixels do mapa.
    screen_polygon = player.get_hitbox_polygon(camera_or_offset=camera)
    world_polygon = player.get_rotated_hitbox()
    # Desenha a hitbox rotacionada (debug) em tela
    pygame.draw.polygon(screen, (255, 0, 0), screen_polygon, 1)


    

    player.draw(camera_or_offset=camera)
    player.curvature.update(screen)

    

    


    if player.state == 'vivo':
        # point-in-polygon test for pixels inside the rotated hitbox
        # compute integer bounding box of polygon in world coordinates to limit work
        import math
        xs = [p[0] for p in world_polygon]
        ys = [p[1] for p in world_polygon]
        minx = max(int(math.floor(min(xs))), 0)
        maxx = min(int(math.ceil(max(xs))), map_image.get_width() - 1)
        miny = max(int(math.floor(min(ys))), 0)
        maxy = min(int(math.ceil(max(ys))), map_image.get_height() - 1)

        def point_in_poly(x, y, poly):
            # ray-casting algorithm
            inside = False
            j = len(poly) - 1
            for i in range(len(poly)):
                xi, yi = poly[i]
                xj, yj = poly[j]
                intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
                if intersect:
                    inside = not inside
                j = i
            return inside

        collided = False
        for px in range(minx, maxx + 1):
            if collided:
                break
            for py in range(miny, maxy + 1):
                # use world coordinates for point-in-polygon and map sampling
                world_x = px + 0.5
                world_y = py + 0.5
                if point_in_poly(world_x, world_y, world_polygon):
                    map_x = int(world_x)
                    map_y = int(world_y)
                    # If the map was scaled for rendering, sample the scaled_map
                    if hasattr(camera, 'scale') and camera.scale != 1.0:
                        # scaled_map was created earlier when rendering
                        map_px = int(world_x * camera.scale)
                        map_py = int(world_y * camera.scale)
                        if 0 <= map_px < scaled_map.get_width() and 0 <= map_py < scaled_map.get_height():
                            cor = scaled_map.get_at((map_px, map_py))[:3]
                        else:
                            cor = (255, 255, 255)
                    else:
                        if 0 <= map_x < map_image.get_width() and 0 <= map_y < map_image.get_height():
                            cor = map_image.get_at((map_x, map_y))[:3]
                        else:
                            cor = (255, 255, 255)

                    if cor == (255, 255, 255):
                        continue
                    player.set_dead()
                    collided = True
                    break

    

    if player.is_dead():
        def reset_player():
            player.respawn(SPAWN_POINT)
        camera.death_screen(screen, player, reset_player)
        continue


    pygame.display.flip()
    clock.tick(60)
    



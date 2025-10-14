import pygame
import math
from World.World import World as world
import os
from Player.Player import Player
from Camera.Camera import Camera
from Player.Pathing.Curvature import Curvature

pygame.init()
screen = pygame.display.set_mode((800, 600))  # largura x altura
pygame.display.set_caption("Pygame Trafo Simulator")




# Carregar imagem do mapa
map_path = os.path.join(os.path.dirname(__file__), 'World', 'Obstacles', 'Mapa1_debug.png')
map_image = pygame.image.load(map_path).convert()


# Lightweight: find a green pixel (centroid of green area) to use as spawn and to ignore in collisions
def find_green_center(img, thresh=200):
    w, h = img.get_width(), img.get_height()
    totx = toty = count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            if g >= thresh and r < 100 and b < 100:
                totx += x; toty += y; count += 1
    if count == 0:
        return None
    return (totx / count, toty / count)


def find_blue_center(img):
    """Find centroid of a blue marker by testing if B is significantly
    larger than R and G (robust to different blue intensities).
    Returns (x,y) in image/world coordinates or None if not found."""
    w, h = img.get_width(), img.get_height()
    totx = toty = count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            # blue if b is notably higher than r and g and has decent intensity
            if b > max(r, g) + 30 and b > 80:
                totx += x; toty += y; count += 1
    if count == 0:
        return None
    return (totx / count, toty / count)


# Build a virtual collision map once: a grid (bytearray per row) where 1 means occupied
def build_collision_grid(img):
    w, h = img.get_width(), img.get_height()
    grid = [bytearray(w) for _ in range(h)]
    occupied = 0
    for y in range(h):
        row = grid[y]
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            # treat strong green as spawn/empty, white as empty, blue marker as empty;
            # everything else is collision
            # ignore green spawn area
            if g >= 200 and r < 100 and b < 100:
                continue
            # ignore white background
            if (r, g, b) == (255, 255, 255):
                continue
            # ignore blue marker (B significantly larger than R/G and reasonably bright)
            if b > max(r, g) + 30 and b > 80:
                continue
            row[x] = 1
            occupied += 1
    return grid, occupied


# Build collision map once
collision_grid, occupied_pixels = build_collision_grid(map_image)
print(f"Collision grid built: {occupied_pixels} occupied pixels")

# determine spawn from green area if present
found = find_green_center(map_image)
if found:
    mx, my = found
    SPAWN_POINT = (mx, my)
else:
    SPAWN_POINT = (200, 200)

camera = Camera(800, 600)
player = Player(SPAWN_POINT, screen, camera)
from World.Trafo import Trafo

# spawn a trafo at blue marker if present, otherwise use a fallback near player
blue_found = find_blue_center(map_image)
if blue_found:
    bx, by = blue_found
    trafo = Trafo(bx, by, size=60)
else:
    try:
        trafo = Trafo(SPAWN_POINT[0] + 120, SPAWN_POINT[1], size=60)
    except Exception:
        trafo = Trafo(SPAWN_POINT[0] + 120 if isinstance(SPAWN_POINT, tuple) else 300, SPAWN_POINT[1] if isinstance(SPAWN_POINT, tuple) else 200, size=60)


clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # forward key events to player
        try:
            player.handle_event(event)
        except Exception:
            pass

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


    

    # update trafo (it will follow the player if picked) and draw it first
    try:
        trafo.update(dt)
        # attempt pickup if not already picked
        if not trafo.picked and player.state == 'vivo':
            picked = player.try_pickup(trafo)
            if picked:
                print('Trafo picked up!')
    except Exception:
        pass

    try:
        trafo.draw(screen, camera)
    except Exception:
        pass

    # draw player on top of trafo
    player.draw(camera_or_offset=camera)
    player.curvature.update(screen)

    # Draw UI: current mode in bottom-left of camera view with semi-transparent background
    try:
        font = pygame.font.SysFont(None, 20)
        mode_text = font.render(f'Mode: {player.curve_mode}', True, (255, 255, 255))
        padding = 8
        # position at bottom-left
        x = padding
        y = screen.get_height() - mode_text.get_height() - padding

        # draw semi-transparent background for readability
        bg_w = mode_text.get_width() + padding * 2
        bg_h = mode_text.get_height() + padding
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        screen.blit(bg_surf, (x - padding, y - padding//2))

        screen.blit(mode_text, (x, y))
    except Exception:
        pass


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
                    # fast bounds check then collision grid lookup (precomputed)
                    if not (0 <= map_x < map_image.get_width() and 0 <= map_y < map_image.get_height()):
                        continue
                    try:
                        if collision_grid[map_y][map_x]:
                            # occupied according to virtual map -> collision
                            player.set_dead()
                            collided = True
                            break
                    except Exception:
                        # on any unexpected error default to safe (no collision)
                        continue

    

    if player.is_dead():
        def reset_player():
            player.respawn(SPAWN_POINT)
        camera.death_screen(screen, player, reset_player)
        continue


    pygame.display.flip()
    clock.tick(60)
    



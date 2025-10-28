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
map_path = os.path.join(os.path.dirname(__file__), 'World', 'Obstacles', 'Map1.png')
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
    # remember initial trafo spawn so we can reset it on player death
    trafo.initial_pos = (bx, by)
else:
    try:
        trafo = Trafo(SPAWN_POINT[0] + 120, SPAWN_POINT[1], size=60)
        trafo.initial_pos = (SPAWN_POINT[0] + 120, SPAWN_POINT[1])
    except Exception:
        trafo = Trafo(SPAWN_POINT[0] + 120 if isinstance(SPAWN_POINT, tuple) else 300, SPAWN_POINT[1] if isinstance(SPAWN_POINT, tuple) else 200, size=60)
        try:
            trafo.initial_pos = (SPAWN_POINT[0] + 120 if isinstance(SPAWN_POINT, tuple) else 300, SPAWN_POINT[1] if isinstance(SPAWN_POINT, tuple) else 200)
        except Exception:
            trafo.initial_pos = (300, 200)


clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60)
    # Use event.pump() + key polling instead of pygame.event.get() to avoid
    # platform-specific exceptions inside event conversion. We detect edge
    # key presses to emulate KEYDOWN for the space key (toggle mode) and ESC
    # to quit.
    try:
        pygame.event.pump()
    except Exception:
        try:
            pygame.joystick.quit()
        except Exception:
            pass
        try:
            pygame.joystick.init()
        except Exception:
            pass

    keys = pygame.key.get_pressed()
    if 'prev_keys' not in globals():
        prev_keys = keys
    try:
        if keys[pygame.K_SPACE] and not prev_keys[pygame.K_SPACE]:
            player.toggle_mode()
        # speed mode shortcuts: 1 = rápida (100%), 2 = média (60%), 3 = lenta (30%)
        if keys[pygame.K_1] and not prev_keys[pygame.K_1]:
            try:
                player.set_speed_mode('rápida')
            except Exception:
                pass
        if keys[pygame.K_2] and not prev_keys[pygame.K_2]:
            try:
                player.set_speed_mode('média')
            except Exception:
                pass
        if keys[pygame.K_3] and not prev_keys[pygame.K_3]:
            try:
                player.set_speed_mode('lenta')
            except Exception:
                pass
        if keys[pygame.K_ESCAPE]:
            running = False
    except Exception:
        pass
    prev_keys = keys

    # compute movement speed from player base and current speed multiplier
    try:
        move_speed = player.base_speed * player.get_speed_multiplier()
    except Exception:
        move_speed = 3
    player.move(keys, speed=move_speed)

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
    screen_edges = player.get_hitbox_polygon(camera_or_offset=camera)
    world_polygon = player.get_rotated_hitbox()
    # Desenha a hitbox rotacionada (debug) em tela
    for kind, data in player.get_hitbox_polygon(camera_or_offset=camera):
        if kind == "edge":
            pygame.draw.line(screen, (255, 0, 0), *data, 1)
        elif kind == "side":
            # lateral sides: draw in a distinct color (magenta) and slightly thicker
            pygame.draw.line(screen, (255, 0, 255), *data, 2)
        elif kind == "wheel":
            pygame.draw.polygon(screen, (0, 255, 0), data, 1)


    

    # update trafo (it will follow the player if picked) and draw it first
    try:
        trafo.update(dt)
        # attempt pickup if not already picked
        if not trafo.picked and player.state == 'vivo':
            # First: check if any 'edge' or 'wheel' part collides with the trafo
            # If so, player dies.
            def seg_intersect(a1, a2, b1, b2):
                # segment intersection (excluding colinear edge cases handled permissively)
                (x1, y1), (x2, y2) = a1, a2
                (x3, y3), (x4, y4) = b1, b2
                denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
                if abs(denom) < 1e-9:
                    return False
                ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
                ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
                return 0.0 <= ua <= 1.0 and 0.0 <= ub <= 1.0

            def point_in_poly(x, y, poly):
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

            def poly_rect_collision(poly, rect):
                # rect is pygame.Rect in world coords
                # 1) any polygon vertex inside rect
                for (px, py) in poly:
                    if rect.collidepoint(px, py):
                        return True
                # 2) any rect corner inside polygon
                corners = [(rect.left, rect.top), (rect.right, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)]
                for (cx, cy) in corners:
                    if point_in_poly(cx + 0.0, cy + 0.0, poly):
                        return True
                # 3) any segment of poly intersects any rect edge
                rect_edges = [
                    ((rect.left, rect.top), (rect.right, rect.top)),
                    ((rect.right, rect.top), (rect.right, rect.bottom)),
                    ((rect.right, rect.bottom), (rect.left, rect.bottom)),
                    ((rect.left, rect.bottom), (rect.left, rect.top)),
                ]
                for i in range(len(poly)):
                    a1 = poly[i]
                    a2 = poly[(i + 1) % len(poly)]
                    for b1, b2 in rect_edges:
                        if seg_intersect(a1, a2, b1, b2):
                            return True
                return False

            def line_rect_collision(p1, p2, rect):
                # 1) either endpoint inside rect
                if rect.collidepoint(p1) or rect.collidepoint(p2):
                    return True
                # 2) intersects rect edges
                rect_edges = [
                    ((rect.left, rect.top), (rect.right, rect.top)),
                    ((rect.right, rect.top), (rect.right, rect.bottom)),
                    ((rect.right, rect.bottom), (rect.left, rect.bottom)),
                    ((rect.left, rect.bottom), (rect.left, rect.top)),
                ]
                for b1, b2 in rect_edges:
                    if seg_intersect(p1, p2, b1, b2):
                        return True
                return False

            # Use a slightly smaller collision rect for the trafo so its
            # hitbox better matches the visual square on screen.
            trafo_rect = trafo.get_collision_rect() if hasattr(trafo, 'get_collision_rect') else trafo.get_rect()
            parts = player.get_rotated_hitbox()
            trafo_collision = False
            for kind, data in parts:
                if kind == 'wheel':
                    if poly_rect_collision(data, trafo_rect):
                        trafo_collision = True
                        break
                elif kind in ('edge', 'line'):
                    p1, p2 = data
                    if line_rect_collision(p1, p2, trafo_rect):
                        trafo_collision = True
                        break
            if trafo_collision:
                player.set_dead()
            else:
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
        try:
            speed_label = player.speed_mode
            speed_pct = int(player.get_speed_multiplier() * 100)
        except Exception:
            speed_label = 'rápida'
            speed_pct = 100
        mode_text = font.render(f'Mode: {player.curve_mode}  Velocidade: {speed_label} ({speed_pct}%)', True, (255, 255, 255))
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
        # Collision check handling the new hitbox format: a list of parts
        # Each part is either ("wheel", polygon) or ("edge", (p1, p2)).
        import math

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

        def check_poly_collision(poly):
            # compute integer bounding box of polygon to limit work
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            minx = max(int(math.floor(min(xs))), 0)
            maxx = min(int(math.ceil(max(xs))), map_image.get_width() - 1)
            miny = max(int(math.floor(min(ys))), 0)
            maxy = min(int(math.ceil(max(ys))), map_image.get_height() - 1)

            for px in range(minx, maxx + 1):
                for py in range(miny, maxy + 1):
                    world_x = px + 0.5
                    world_y = py + 0.5
                    if point_in_poly(world_x, world_y, poly):
                        map_x = int(world_x)
                        map_y = int(world_y)
                        if not (0 <= map_x < map_image.get_width() and 0 <= map_y < map_image.get_height()):
                            continue
                        try:
                            if collision_grid[map_y][map_x]:
                                return True
                        except Exception:
                            continue
            return False

        def check_line_collision(p1, p2):
            # sample points along the line at ~1px spacing and check grid
            x1, y1 = p1
            x2, y2 = p2
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)
            if length < 1e-6:
                # degenerate: treat single point
                ix, iy = int(round(x1)), int(round(y1))
                if 0 <= ix < map_image.get_width() and 0 <= iy < map_image.get_height():
                    try:
                        return bool(collision_grid[iy][ix])
                    except Exception:
                        return False
                return False

            steps = int(math.ceil(length))
            for i in range(steps + 1):
                t = float(i) / float(steps)
                wx = x1 + dx * t
                wy = y1 + dy * t
                ix = int(wx)
                iy = int(wy)
                if not (0 <= ix < map_image.get_width() and 0 <= iy < map_image.get_height()):
                    continue
                try:
                    if collision_grid[iy][ix]:
                        return True
                except Exception:
                    continue
            return False

        collided = False
        # get the hitbox parts in world coordinates
        parts = player.get_rotated_hitbox()
        for kind, data in parts:
            if collided:
                break
            try:
                if kind == 'wheel':
                    # data is poly (list of points)
                    if check_poly_collision(data):
                        player.set_dead()
                        collided = True
                        break
                elif kind in ('edge', 'line', 'side'):
                    p1, p2 = data
                    if check_line_collision(p1, p2):
                        player.set_dead()
                        collided = True
                        break
                else:
                    # unknown part: if it's a polygon-like sequence assume polygon
                    if isinstance(data, (list, tuple)) and len(data) >= 3:
                        if check_poly_collision(data):
                            player.set_dead()
                            collided = True
                            break
            except Exception:
                # safe fallback: ignore this part on error
                continue

    if player.is_dead():
        def reset_player():
            # drop trafo (if carried) and reset it to its initial spawn
            try:
                if hasattr(trafo, 'picked') and trafo.picked:
                    trafo.drop()
                if hasattr(trafo, 'initial_pos'):
                    ix, iy = trafo.initial_pos
                    trafo.x = ix
                    trafo.y = iy
                    trafo.picked = False
                    trafo.carrier = None
            except Exception:
                pass
            player.respawn(SPAWN_POINT)
        camera.death_screen(screen, player, reset_player)
        continue


    pygame.display.flip()
    clock.tick(60)
    



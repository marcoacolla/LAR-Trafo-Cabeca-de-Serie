import pygame
import math
from World.World import World as world
import os
from Player.Player import Player
from Camera.Camera import Camera
from Player.Pathing.Curvature import Curvature

pygame.init()
# Main display and layout: reserve a right-side panel for customizable UI
PANEL_WIDTH = 300  # largura padrão do painel lateral (personalizável)
SCREEN_W = 800 + PANEL_WIDTH
SCREEN_H = 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))  # largura x altura
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

camera = Camera(SCREEN_W - PANEL_WIDTH, SCREEN_H)
player = Player(SPAWN_POINT, screen, camera)
from World.Trafo import Trafo
# optional joystick controller (provided in Player/Joystick.py)

from Player.Joystick import Joystick as JoystickController

# Hardcore mode: when True, death is blocking and player cannot move until respawn.
# When False, death shows an overlay but player can still move; if the player
# exits the collision area the death state is cleared.
hardcore_mode = False

# control mode for input: 'keyboard' or 'joystick'
control_mode = 'keyboard'
joystick_controller = JoystickController()
# prefer explicit availability flag from the adapter
try:
    joystick_available = bool(getattr(joystick_controller, 'available', False))
except Exception:
    joystick_available = False
# last printed control mode to avoid repeated logs
last_printed_control_mode = control_mode

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

# -------------------------
# SidePanel: minimal, customizable right-side UI (module-level)
# -------------------------
class SidePanel:
    def __init__(self, x, y, w, h, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font or pygame.font.SysFont(None, 20)
        # screens: list of dict {'title': str, 'options': [(label, callback_or_None), ...]}
        self.screens = []
        self.current = 0
        self.selected = 0

    def add_screen(self, title, options):
        self.screens.append({'title': title, 'options': options})

    def next_screen(self):
        if not self.screens:
            return
        self.current = (self.current + 1) % len(self.screens)
        self.selected = 0

    def prev_screen(self):
        if not self.screens:
            return
        self.current = (self.current - 1) % len(self.screens)
        self.selected = 0

    def select_next(self):
        opts = self._opts()
        if not opts:
            return
        self.selected = (self.selected + 1) % len(opts)

    def select_prev(self):
        opts = self._opts()
        if not opts:
            return
        self.selected = (self.selected - 1) % len(opts)

    def activate(self):
        opts = self._opts()
        if not opts:
            return
        label, cb = opts[self.selected]
        try:
            if callable(cb):
                cb()
            else:
                print(f"Selected: {label}")
        except Exception:
            print(f"Error running callback for: {label}")

    def _opts(self):
        if not self.screens:
            return []
        return self.screens[self.current].get('options', [])

    def draw(self, surf):
        # background
        pygame.draw.rect(surf, (30, 30, 30), self.rect)
        # title
        if not self.screens:
            t = self.font.render('Panel (empty)', True, (255,255,255))
            surf.blit(t, (self.rect.x + 8, self.rect.y + 8))
            return
        title = self.screens[self.current].get('title', '')
        t = self.font.render(title, True, (255,255,255))
        surf.blit(t, (self.rect.x + 8, self.rect.y + 8))

        # options
        opts = self._opts()
        oy = self.rect.y + 8 + t.get_height() + 8
        pad = 6
        for idx, (label, _) in enumerate(opts):
            y = oy + idx * (self.font.get_height() + pad)
            if y + self.font.get_height() > self.rect.bottom - 8:
                break
            if idx == self.selected:
                # highlight
                highlight_rect = pygame.Rect(self.rect.x + 6, y - 2, self.rect.width - 12, self.font.get_height() + 4)
                pygame.draw.rect(surf, (70,70,120), highlight_rect)
            txt = self.font.render(label, True, (240,240,240))
            surf.blit(txt, (self.rect.x + 12, y))

    def update_mode_display(self, new_mode):
        # optional hook used by existing code to notify UI of mode change
        # if a screen has an option named 'Mode' we update its label
        try:
            for s in self.screens:
                for i, (label, cb) in enumerate(s.get('options', [])):
                    if label.startswith('Mode:'):
                        s['options'][i] = (f'Mode: {new_mode}', cb)
        except Exception:
            pass

# Instantiate a SidePanel on the right and populate with default screens
panel_x = SCREEN_W - PANEL_WIDTH
panel_y = 0
panel_h = SCREEN_H
panel_w = PANEL_WIDTH
ui = SidePanel(panel_x, panel_y, panel_w, panel_h)

def _toggle_hardcore():
    global hardcore_mode
    hardcore_mode = not hardcore_mode
    print(f"Hardcore mode set to: {hardcore_mode}")

def _reset_trafo():
    try:
        if hasattr(trafo, 'initial_pos'):
            ix, iy = trafo.initial_pos
            trafo.x = ix
            trafo.y = iy
            trafo.picked = False
            trafo.carrier = None
            print('Trafo reset to initial position')
    except Exception:
        pass

ui.add_screen('Main', [
    (f'Mode: {getattr(player, "curve_mode", "unknown")}', None),
    ('Toggle Hardcore', _toggle_hardcore),
    ('Reset Trafo', _reset_trafo),
])

ui.add_screen('Joystick', [
    ('Control: ' + control_mode.upper(), None),
    ('Set Speed Rápida', lambda: player.set_speed_mode('rápida')),
    ('Set Speed Média', lambda: player.set_speed_mode('média')),
    ('Set Speed Lenta', lambda: player.set_speed_mode('lenta')),
])

# expose ui variable in globals (some existing code checks globals().get('ui'))
globals()['ui'] = ui



clock = pygame.time.Clock()
running = True
# timestamp (ms) until which a trafo-caused death should be preserved to avoid flicker
trafo_death_expire = 0
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
    # poll CAN joystick (if present) to update its internal state
    try:
        if getattr(joystick_controller, 'available', False) and hasattr(joystick_controller, 'poll'):
            try:
                joystick_controller.poll()
                player.lights = joystick_controller.lights
            except Exception:
                # if poll fails, mark unavailable so toggle won't try to use it
                try:
                    joystick_controller.available = False
                except Exception:
                    pass
    except Exception:
        pass

    # flag to indicate death caused by trafo this frame (prevents immediate clearing)
    trafo_caused_death = False

    # Process selector (mode) messages from CAN joystick adapter if changed
    try:
        if getattr(joystick_controller, 'available', False) and getattr(joystick_controller, 'hasChangedMode', False):
            try:
                sel = getattr(joystick_controller, 'currentMode', 0)
                # Map selector values to internal mode names (follow turtle app logic)
                mode_map = {
                    1: 'straight',
                    2: 'diagonal',
                    4: 'pivotal',
                    8: 'icamento'
                }
                new_mode = mode_map.get(sel)
                if new_mode:
                    try:
                        player.setMode(new_mode)
                    except Exception:
                        pass
                    # Try to update any UI adapter if present (optional)
                    try:
                        ui_obj = globals().get('ui')
                        if ui_obj is not None and hasattr(ui_obj, 'update_mode_display'):
                            ui_obj.update_mode_display(new_mode)
                    except Exception:
                        pass
            finally:
                # clear change flag so we don't reprocess the same selection
                try:
                    joystick_controller.hasChangedMode = False
                except Exception:
                    pass
    except Exception:
        pass

    try:
        if getattr(joystick_controller, 'available', False) and getattr(joystick_controller, 'hasChangedSpeed', False):
            try:
                sel = getattr(joystick_controller, 'currentSpeed', 0)
                # Map selector values to internal mode names (follow turtle app logic)
                speed_map = {
                    0: 'rápida',
                    1: 'média',
                    3: 'lenta'
                }
                new_speed = speed_map.get(sel)
                print(new_speed)
                if new_speed:
                    try:
                        player.set_speed_mode(new_speed)
                    except Exception:
                        pass
            finally:
                # clear change flag so we don't reprocess the same selection
                try:
                    joystick_controller.hasChangedSpeed = False
                except Exception:
                    pass
    except Exception:
        pass

    keys = pygame.key.get_pressed()
    if 'prev_keys' not in globals():
        prev_keys = keys
    try:
        if keys[pygame.K_SPACE] and not prev_keys[pygame.K_SPACE]:
            player.toggle_mode()
        # toggle control mode between keyboard and joystick (press C)
        if keys[pygame.K_c] and not prev_keys[pygame.K_c]:
            if control_mode == 'keyboard':
                # try enable joystick only if controller reported available
                if joystick_available:
                    control_mode = 'joystick'
                else:
                    # inform user but don't switch state
                    print('Joystick not available; staying in KEYBOARD mode')
            else:
                control_mode = 'keyboard'
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

    # Panel navigation keys (Tab to cycle screens, arrows to move, Enter to activate)
    try:
        if keys[pygame.K_TAB] and not prev_keys[pygame.K_TAB]:
            ui.next_screen()
        if keys[pygame.K_RIGHT] and not prev_keys[pygame.K_RIGHT]:
            ui.next_screen()
        if keys[pygame.K_LEFT] and not prev_keys[pygame.K_LEFT]:
            ui.prev_screen()
        if keys[pygame.K_UP] and not prev_keys[pygame.K_UP]:
            ui.select_prev()
        if keys[pygame.K_DOWN] and not prev_keys[pygame.K_DOWN]:
            ui.select_next()
        if keys[pygame.K_RETURN] and not prev_keys[pygame.K_RETURN]:
            ui.activate()
    except Exception:
        pass

    # Zoom controls (j = zoom out, k = zoom in)
    try:
        # zoom amount per frame scaled by dt so it's framerate independent
        ZOOM_SPEED = 0.04
        MIN_SCALE = 0.25
        MAX_SCALE = 4.0
        zoom_changed = False
        if keys[pygame.K_j]:
            camera.scale = max(MIN_SCALE, camera.scale - ZOOM_SPEED * (dt / 16.0))
            zoom_changed = True
        if keys[pygame.K_k]:
            camera.scale = min(MAX_SCALE, camera.scale + ZOOM_SPEED * (dt / 16.0))
            zoom_changed = True
        if zoom_changed:
            # re-center camera when zoom changes
            camera.update(player)
    except Exception:
        pass

    # compute movement speed from player base and current speed multiplier
    try:
        move_speed = player.base_speed * player.get_speed_multiplier()
    except Exception:
        move_speed = 3
    # If joystick control is active and controller reports available, use joystick inputs
    try:
        if control_mode == 'joystick':
            if getattr(joystick_controller, 'available', False):
                try:
                    lx, ly, rx, ry = joystick_controller.getJoystickValues()
                    player.move_with_joystick((lx, ly, rx, ry), speed=move_speed)
                except Exception as e:
                    # if joystick access fails at runtime, fall back to keyboard
                    control_mode = 'keyboard'
                    print(f'Joystick error: reverting to KEYBOARD control({e})')
                    player.move(keys, speed=move_speed)
            else:
                # joystick not available at runtime; fall back
                control_mode = 'keyboard'
                print('Joystick not available at runtime; switching to KEYBOARD')
                player.move(keys, speed=move_speed)
        else:
            player.move(keys, speed=move_speed)
    except Exception:
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
    '''
    # Desenha a hitbox rotacionada (debug) em tela
    for kind, data in player.get_hitbox_polygon(camera_or_offset=camera):
        if kind == "edge":
            pygame.draw.line(screen, (255, 0, 0), *data, 1)
        elif kind == "side":
            # lateral sides: draw in a distinct color (magenta) and slightly thicker
            pygame.draw.line(screen, (255, 0, 255), *data, 2)
        elif kind == "wheel":
            pygame.draw.polygon(screen, (0, 255, 0), data, 1)
    '''

    

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
            # Determine forward vector from player's heading to identify front edge
            try:
                px, py = player.getPosition()
                heading_rad = math.radians(player.getHeading())
                forward_vec = (math.sin(heading_rad), -math.cos(heading_rad))
            except Exception:
                px = py = 0.0
                forward_vec = (0.0, -1.0)

            # Prepare debug logging when trafo is near player to diagnose missed collisions
            debug_near = False
            try:
                dx = trafo.x - px
                dy = trafo.y - py
                dist = math.hypot(dx, dy)
                # only enable verbose debug when within reasonable proximity to avoid spam
                debug_near = dist < 400
            except Exception:
                debug_near = False

            # collect diagnostics to report if no collision is found
            diag_wheels = []
            diag_edges = []

            for idx, (kind, data) in enumerate(parts):
                if kind == 'wheel':
                    # wheel polygons are lethal. Use polygon/rect test first,
                    # then fallback to axis-aligned bounding-box (AABB) test
                    try:
                        hit = poly_rect_collision(data, trafo_rect)
                    except Exception:
                        hit = False

                    reason = 'poly'
                    if not hit:
                        try:
                            xs = [p[0] for p in data]
                            ys = [p[1] for p in data]
                            wmin = min(xs); wmax = max(xs)
                            hmin = min(ys); hmax = max(ys)
                            wheel_aabb = pygame.Rect(wmin, hmin, wmax - wmin, hmax - hmin)
                            if wheel_aabb.colliderect(trafo_rect):
                                hit = True
                                reason = 'aabb'
                        except Exception:
                            hit = False

                    diag_wheels.append({
                        'idx': idx,
                        'hit': hit,
                        'reason': reason,
                        'aabb': (locals().get('wmin', None), locals().get('wmax', None), locals().get('hmin', None), locals().get('hmax', None))
                    })

                    if hit:
                        try:
                            if debug_near:
                                #print(f"[TRAFO DEBUG] wheel idx={idx} collision detected ({reason})")
                                pass
                        except Exception:
                            pass
                        trafo_collision = True
                        break

                elif kind == 'edge' or kind == 'line':
                    # Only the front-facing edge should be lethal; determine
                    # frontness by midpoint dot with forward vector.
                    try:
                        p1, p2 = data
                        midx = (p1[0] + p2[0]) * 0.5
                        midy = (p1[1] + p2[1]) * 0.5
                        vx = midx - px
                        vy = midy - py
                        dot = vx * forward_vec[0] + vy * forward_vec[1]
                        is_front = dot > 0
                        diag_edges.append({'p1': p1, 'p2': p2, 'midx': midx, 'midy': midy, 'dot': dot, 'is_front': is_front})
                        if is_front:
                            if line_rect_collision(p1, p2, trafo_rect):
                                try:
                                    if debug_near:
                                        #print(f"[TRAFO DEBUG] front edge collision at midpoint=({midx:.1f},{midy:.1f}) dot={dot:.2f}")
                                        pass
                                except Exception:
                                    pass
                                trafo_collision = True
                                break
                    except Exception:
                        # ignore and continue
                        pass

            # If we didn't detect collision but debug_near is True, print diagnostics
            if (not trafo_collision) and debug_near:
                try:
                    #print("[TRAFO DEBUG] no lethal collision detected. Diagnostics:")
                    #print(f"  trafo_rect={trafo_rect}")
                    #print(f"  player_pos=({px:.1f},{py:.1f}), forward={forward_vec}")
                    for w in diag_wheels:
                        pass
                    for e in diag_edges:
                        pass
                except Exception:
                    pass
            if trafo_collision:
                    try:
                        player.set_dead()
                        trafo_caused_death = True
                        # preserve death state for a short time to avoid flicker (500 ms)
                        try:
                            expire = pygame.time.get_ticks() + 500
                            trafo_death_expire = expire
                            # also set lock on player to prevent any immediate revival
                            try:
                                player.death_lock_until = expire
                            except Exception:
                                pass
                        except Exception:
                            trafo_death_expire = trafo_death_expire or 0
                    except Exception:
                        pass
            else:
                # Use player's own pickup logic (works in world coords)
                try:
                    # Only allow pickup when in 'icamento' mode and cursor >= 0.8
                    allow_pickup = False
                    try:
                        if getattr(player, 'curve_mode', None) == 'icamento' and getattr(player, 'icamento_cursor', 0.0) >= 0.8:
                            allow_pickup = True
                    except Exception:
                        allow_pickup = False

                    if allow_pickup:
                        picked = player.try_pickup(trafo)
                    else:
                        picked = False
                except Exception:
                    picked = False
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
        # draw control mode + zoom + hardcore state at top-left for quick debug
        try:
            hud_text = font.render(f'Control: {control_mode.upper()}  Zoom: {camera.scale:.2f}  Hardcore: {"ON" if hardcore_mode else "OFF"}', True, (255,255,255))
            screen.blit(hud_text, (8, 8))
            # print control mode change only once to avoid log spam
            if control_mode != last_printed_control_mode:
                print(f'Control mode: {control_mode.upper()}')
                last_printed_control_mode = control_mode
        except Exception:
            pass
        # Delegate icamento UI drawing to Player
        try:
            if hasattr(player, 'draw_icamento_ui'):
                player.draw_icamento_ui(screen)
        except Exception:
            pass
    except Exception:
        pass


    # Always perform collision checks so we can clear death in non-hardcore mode
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

    # If we're in permissive (non-hardcore) death and no collision is present
    # anymore, clear the dead state so the overlay disappears and the player
    # can continue normally.
    # respect short trafo death timeout to avoid flicker: only clear if timeout expired
    try:
        now_ms = pygame.time.get_ticks()
    except Exception:
        now_ms = 0
    if not collided and player.is_dead() and not hardcore_mode and now_ms > trafo_death_expire:
        try:
            player.set_alive()
        except Exception:
            pass

    if player.is_dead():
        if hardcore_mode:
            # blocking death screen (original behavior)
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
        else:
            # permissive death: show a non-blocking overlay but allow movement.
            try:
                fonte = pygame.font.SysFont(None, 48)
                texto = fonte.render('Você morreu! (modo permissivo) Mova para sair.', True, (255, 0, 0))
                # semi-transparent background
                bg_w = texto.get_width() + 40
                bg_h = texto.get_height() + 24
                bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 150))
                sx = screen.get_width()//2 - bg_w//2
                sy = screen.get_height()//2 - bg_h//2
                screen.blit(bg_surf, (sx, sy))
                screen.blit(texto, (sx + 20, sy + 12))
            except Exception:
                pass
            # Do not continue; allow loop to run so player can move out of collision.


    try:
        ui.draw(screen)
    except Exception:
        pass
    pygame.display.flip()
    clock.tick(60)
    



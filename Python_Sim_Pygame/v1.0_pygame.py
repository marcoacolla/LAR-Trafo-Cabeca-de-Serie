import pygame
import math
from World.World import World as world
import os
from Player.Player import Player
from Camera.Camera import Camera
from Player.Pathing.Curvature import Curvature
# UI manager (modular screens placed in `ui/` package)
try:
    from ui.manager import UIManager
except Exception:
    # best-effort import; if running from different cwd this may fail
    UIManager = None

# -------------------------
# SidePanel: minimal, customizable right-side UI (module-level)
# -------------------------
class SidePanel:
    def __init__(self, x, y, w, h, font=None, layout='vertical'):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font or pygame.font.SysFont(None, 20)
        # screens: list of dict {'title': str, 'options': [(label, callback_or_None), ...]}
        self.screens = []
        self.current = 0
        self.selected = 0
        # layout: 'vertical' (default) or 'horizontal' for side-by-side options
        self.layout = layout

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
        self.selected += 1
        if self.selected >= len(opts):
            self.selected = 0

    def select_prev(self):
        opts = self._opts()
        if not opts:
            return
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(opts) - 1

    def handle_action(self, action):
        """Generic action handler for joystick or external callers.
        Actions: 'next_screen','prev_screen','select_next','select_prev','activate'"""
        try:
            if action == 'next_screen':
                self.next_screen()
            elif action == 'prev_screen':
                self.prev_screen()
            elif action == 'select_next':
                self.select_next()
            elif action == 'select_prev':
                self.select_prev()
            elif action == 'activate':
                self.activate()
        except Exception:
            pass

    def process_key_event(self, key):
        """Process a pygame key constant as an edge event.
        Keeps mapping centralized so joystick code can call `ui.handle_action` later."""
        if key in (pygame.K_TAB, pygame.K_RIGHT):
            self.next_screen()
        elif key == pygame.K_LEFT:
            self.prev_screen()
        elif key == pygame.K_UP:
            self.select_prev()
        elif key == pygame.K_DOWN:
            self.select_next()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.activate()

    def activate(self):
        opts = self._opts()
        if not opts:
            return
        label, cb = opts[self.selected]
        try:
            if callable(cb):
                cb()
        except Exception:
            pass

    def _opts(self):
        if not self.screens:
            return []
        return self.screens[self.current].get('options', [])

    def draw(self, surf):
        # compute a compact background box sized to fit the title and options
        if not self.screens:
            t = self.font.render('Panel (empty)', True, (255,255,255))
            empty_w = t.get_width() + 24
            empty_h = t.get_height() + 16
            content_rect = pygame.Rect(self.rect.right - empty_w - 8, self.rect.y + 8, empty_w, empty_h)
            pygame.draw.rect(surf, (30, 30, 30), content_rect)
            surf.blit(t, (content_rect.x + 8, content_rect.y + 8))
            return

        title = self.screens[self.current].get('title', '')
        t = self.font.render(title, True, (255,255,255))

        opts = self._opts()
        pad = 6
        # available width inside the panel to place content
        max_width = max(16, self.rect.width - 16)

        # compute content size depending on layout
        if self.layout == 'vertical':
            max_opt_w = 0
            for label, _ in opts:
                s = self.font.render(label, True, (240,240,240))
                max_opt_w = max(max_opt_w, s.get_width())
            content_w = min(max_width, max(t.get_width(), max_opt_w) + 24)
            content_h = t.get_height() + 8 + len(opts) * (self.font.get_height() + pad) + 16
        else:
            # simulate horizontal wrapping to compute width and height
            start_x = 0
            x = 0
            rows = 1
            row_height = self.font.get_height()
            pad_x = 12
            pad_y = 8
            max_row_w = 0
            for label, _ in opts:
                s = self.font.render(label, True, (240,240,240))
                item_w = s.get_width() + 12
                if x + item_w > max_width:
                    max_row_w = max(max_row_w, x)
                    x = 0
                    rows += 1
                x += item_w + pad_x
            max_row_w = max(max_row_w, x)
            content_w = min(max_width, max(t.get_width(), max_row_w) + 24)
            content_h = t.get_height() + 8 + rows * row_height + (rows - 1) * pad_y + 16

        # place content box at the bottom left of the screen
        surf_w, surf_h = surf.get_width(), surf.get_height()
        # sobe o painel mais para cima (ex: 48 pixels do fundo ao invés de 16)
        content_rect = pygame.Rect(8, surf_h - content_h - 48, content_w, content_h)
        # fundo branco
        pygame.draw.rect(surf, (255, 255, 255), content_rect)
        # borda vermelha grossa
        pygame.draw.rect(surf, (220, 0, 0), content_rect, 3)
        # título azul
        surf.blit(self.font.render(title, True, (0, 70, 220)), (content_rect.x + 8, content_rect.y + 8))

        oy = content_rect.y + 8 + t.get_height() + 8
        # vertical layout (original behavior)
        if self.layout == 'vertical':
            for idx, (label, _) in enumerate(opts):
                y = oy + idx * (self.font.get_height() + pad)
                if y + self.font.get_height() > content_rect.bottom - 8:
                    break
                if idx == self.selected:
                    highlight_rect = pygame.Rect(content_rect.x + 6, y - 2, content_rect.width - 12, self.font.get_height() + 4)
                    pygame.draw.rect(surf, (0,70,220), highlight_rect)
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    txt = self.font.render(label, True, (0, 70, 220))
                surf.blit(txt, (content_rect.x + 12, y))
        else:
            # horizontal layout: place options side-by-side, wrap to next row if needed
            start_x = 8
            x = start_x
            y = oy
            row_height = self.font.get_height()
            pad_x = 12
            pad_y = 8
            for idx, (label, _) in enumerate(opts):
                # calcula largura do item com cor correta
                if idx == self.selected:
                    item_w = self.font.render(label, True, (255,255,255)).get_width() + 12
                else:
                    item_w = self.font.render(label, True, (0,70,220)).get_width() + 12

                # wrap to next row if doesn't fit
                if x + item_w > content_rect.width - 16:
                    x = start_x
                    y += row_height + pad_y
                # desenha highlight e texto
                if idx == self.selected:
                    highlight_rect = pygame.Rect(content_rect.x + x - 6, y - 2, item_w + 6, row_height + 4)
                    pygame.draw.rect(surf, (0,70,220), highlight_rect)
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    txt = self.font.render(label, True, (0, 70, 220))
                surf.blit(txt, (content_rect.x + x + 6, y))
                x += item_w + pad_x

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


pygame.init()
# Main display and layout: reserve a right-side panel for customizable UI
PANEL_WIDTH = 300  # largura padrão do painel lateral (personalizável)
SCREEN_W = 800 + PANEL_WIDTH
SCREEN_H = 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))  # largura x altura
pygame.display.set_caption("Pygame Trafo Simulator")
selected_map_path = None
try:
    # show start menu and collect initial options (runs its own small event loop)
    from ui.menu_screen import run_start_menu
    try:
        from ui.screens.map_select_screen import run_map_select_menu
    except Exception:
        run_map_select_menu = None
    import sys as _sys
    _initial_cfg = {'hardcore': False, 'fullscreen': False}
    _cfg_res, _action = run_start_menu(screen, _initial_cfg)
    selected_map_path = None
    # if menu requested map selection, loop until a map is chosen or user exits
    while _action == 'map_select':
        if run_map_select_menu is not None:
            sel = run_map_select_menu(screen)
        else:
            sel = None
        if sel:
            selected_map_path = sel
            break
        # user canceled map selection -> show start menu again
        _cfg_res, _action = run_start_menu(screen, _cfg_res)
    if _action == 'exit':
        pygame.quit()
        _sys.exit(0)
    # apply selected flags (will apply fullscreen later once camera exists)
    hardcore_mode = bool(_cfg_res.get('hardcore', False))
    start_menu_desired_fullscreen = bool(_cfg_res.get('fullscreen', False))
except Exception:
    # fallback defaults
    hardcore_mode = False
    start_menu_desired_fullscreen = False
    selected_map_path = None
# Fullscreen state tracking: windowed size and flag
is_fullscreen = False
_windowed_size = (SCREEN_W, SCREEN_H)

def toggle_fullscreen():
    """Toggle fullscreen (F11 or Alt+Enter). Updates `screen`, `camera`, and `ui` where possible."""
    global is_fullscreen, screen, camera, _windowed_size
    try:
        # remember previous screen size to compute offsets
        try:
            old_w, old_h = screen.get_width(), screen.get_height()
        except Exception:
            old_w, old_h = _windowed_size

        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            # store the current windowed size so we can restore later
            try:
                _windowed_size = (old_w, old_h)
            except Exception:
                pass
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode(_windowed_size)

        # Update camera dimensions so centering/scale continue to work
        try:
            camera.width = screen.get_width()
            camera.height = screen.get_height()
        except Exception:
            pass

        # Update UI manager or SidePanel to adapt to new screen size if present
        try:
            ui_obj = globals().get('ui')
            if ui_obj is not None:
                new_w, new_h = screen.get_width(), screen.get_height()
                # UIManager: preserve position relative to screen using proportional mapping
                try:
                    if hasattr(ui_obj, 'panel_rect'):
                        pr = ui_obj.panel_rect
                        # compute previous position ratios relative to old screen
                        try:
                            rx = pr.x / float(old_w) if old_w > 0 else 0.0
                            ry = pr.y / float(old_h) if old_h > 0 else 0.0
                        except Exception:
                            rx = 0.02
                            ry = 0.75
                        # map to new screen keeping same pixel size
                        pr.x = int(max(0, min(new_w - pr.width, round(rx * new_w))))
                        pr.y = int(max(0, min(new_h - pr.height, round(ry * new_h))))
                        ui_obj.panel_rect = pr
                    if hasattr(ui_obj, 'screen'):
                        ui_obj.screen = screen
                except Exception:
                    pass

                # SidePanel: preserve relative position as well (not always anchored)
                try:
                    if hasattr(ui_obj, 'rect'):
                        r = ui_obj.rect
                        try:
                            rx = r.x / float(old_w) if old_w > 0 else 1.0
                            ry = r.y / float(old_h) if old_h > 0 else 0.0
                        except Exception:
                            rx = 1.0
                            ry = 0.0
                        r.x = int(max(0, min(new_w - r.width, round(rx * new_w))))
                        r.y = int(max(0, min(new_h - r.height, round(ry * new_h))))
                        # if panel height was intended to span full height, preserve that
                        if r.height != new_h and (abs(r.height - old_h) < 8):
                            r.height = new_h
                        ui_obj.rect = r
                except Exception:
                    pass
        except Exception:
            pass

        # debug print removed
    except Exception:
        pass




# Carregar imagem do mapa
if 'selected_map_path' in globals() and selected_map_path:
    map_path = selected_map_path
else:
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
            # Only treat BLACK as collision/death
            # Everything else (green spawn, white, gray path, blue marker) is safe
            if r < 50 and g < 50 and b < 50:  # Black pixels cause death
                row[x] = 1
                occupied += 1
    return grid, occupied


# Build collision map once
collision_grid, occupied_pixels = build_collision_grid(map_image)
# debug print removed

# determine spawn from green area if present
found = find_green_center(map_image)
if found:
    mx, my = found
    SPAWN_POINT = (mx, my)
else:
    SPAWN_POINT = (200, 200)

camera = Camera(SCREEN_W, SCREEN_H)
player = Player(SPAWN_POINT, screen, camera)
# If startup menu requested fullscreen, apply it now (camera exists for toggle)
try:
    if start_menu_desired_fullscreen and not is_fullscreen:
        toggle_fullscreen()
except Exception:
    pass
from World.Trafo import Trafo
# optional joystick controller (provided in Player/Joystick.py)

from Player.Joystick import Joystick as JoystickController

# Hardcore mode: when True, death is blocking and player cannot move until respawn.
# When False, death shows an overlay but player can still move; if the player
# exits the collision area the death state is cleared.
# `hardcore_mode` is initialized from the start menu above (variable already set)

# control mode for input: 'keyboard' or 'joystick'
control_mode = 'keyboard'

# Instantiate a SidePanel on the right and populate with default screens
# Instantiate a compact bottom-left UI manager if available, else fall back to SidePanel
if UIManager is not None:
    # compute panel_rect using the actual surface size so the panel stays
    # anchored to the bottom even when the window was toggled to fullscreen
    try:
        sw, sh = screen.get_size()
        panel_rect = (8, sh - 120, 320, 100)
    except Exception:
        panel_rect = (8, SCREEN_H - 120, 320, 100)
    ui = UIManager(screen, panel_rect=panel_rect, player=player)
else:
    # fallback: older SidePanel on the right
    sw, sh = screen.get_size()
    panel_x = sw - PANEL_WIDTH
    panel_y = 0
    panel_h = sh
    panel_w = PANEL_WIDTH
    ui = SidePanel(panel_x, panel_y, panel_w, panel_h, layout='horizontal')


joystick_controller = JoystickController(ui)
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
    trafo = Trafo(bx, by, size=60, image_path='trafo_image/trafo.png')
    # remember initial trafo spawn so we can reset it on player death
    trafo.initial_pos = (bx, by)
else:
    try:
        trafo = Trafo(SPAWN_POINT[0] + 120, SPAWN_POINT[1], size=60, image_path='trafo_image/trafo.png')
        trafo.initial_pos = (SPAWN_POINT[0] + 120, SPAWN_POINT[1])
    except Exception:
        trafo = Trafo(SPAWN_POINT[0] + 120 if isinstance(SPAWN_POINT, tuple) else 300, SPAWN_POINT[1] if isinstance(SPAWN_POINT, tuple) else 200, size=60, image_path='trafo_image/trafo.png')
        try:
            trafo.initial_pos = (SPAWN_POINT[0] + 120 if isinstance(SPAWN_POINT, tuple) else 300, SPAWN_POINT[1] if isinstance(SPAWN_POINT, tuple) else 200)
        except Exception:
            trafo.initial_pos = (300, 200)

        # Timestamp (ms) when trafo was last picked up; used to display a HUD indicator.
        trafo_pickup_time = 0
        # How long (ms) to show the pickup indicator
        TRAFO_PICKUP_DISPLAY_MS = 1500



def _toggle_hardcore():
    global hardcore_mode
    hardcore_mode = not hardcore_mode
    # debug print removed

def _reset_trafo():
    try:
        if hasattr(trafo, 'initial_pos'):
            ix, iy = trafo.initial_pos
            trafo.x = ix
            trafo.y = iy
            trafo.picked = False
            trafo.carrier = None
            # debug print removed
    except Exception:
        pass

def goto_screen_by_title(title):
    """Set the panel to the screen with the given title (if exists)."""
    try:
        for i, s in enumerate(ui.screens):
            if s.get('title') == title:
                # push current screen onto ui history so back returns here
                try:
                    if getattr(ui, 'history', None) is not None:
                        ui.history.append(ui.current)
                except Exception:
                    pass
                ui.current = i
                ui.selected = 0
                return
    except Exception:
        pass
    # debug print removed

ui.add_screen('Main', [
    (f'Mode: {getattr(player, "curve_mode", "unknown")}', None),
    ('Sensores', lambda: goto_screen_by_title('Sensores')),
    ('Toggle Hardcore', _toggle_hardcore),
    ('Reset Trafo', _reset_trafo),
])

# (Removed placeholder screens 'Joystick' and 'Sensores' — keep UI focused on Main/Menu_01)

# Menu_01: new screen shown when selecting Menu from Main
ui.add_screen('Menu_01', [
    ('Funções de Segurança', lambda: goto_screen_by_title('FS_MENU')),
    ('Sensores', lambda: goto_screen_by_title('Sensores')),
    ('Luz Sinalz.', lambda: goto_screen_by_title('FS_LIGHTS')),
],)
# Sensores: informational screen (registered so goto_screen_by_title finds it)
ui.add_screen('Sensores', [
    # no selectable options; display-only handled by UIManager.draw
])
try:
    for s in ui.screens:
        if s.get('title') == 'Sensores':
            s['navigable'] = False
            break
except Exception:
    pass

# Sensores page 2: additional sensor diagnostics
ui.add_screen('Sensores_2', [
    # display-only
])
try:
    for s in ui.screens:
        if s.get('title') == 'Sensores_2':
            s['navigable'] = False
            break
except Exception:
    pass
# Make Menu_01 NOT navigable with left/right arrows; only reachable via activation
try:
    for s in ui.screens:
        if s.get('title') == 'Menu_01':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_MENU: Funções de Segurança submenu
ui.add_screen('FS_MENU', [
    ('Funções Basicas', lambda: goto_screen_by_title('FS_BASIC')),
    ('Funções Avançadas', lambda: goto_screen_by_title('FS_ADVANCED')),
])
# Make FS_MENU non-navigable (reachable only from Menu_01)
try:
    for s in ui.screens:
        if s.get('title') == 'FS_MENU':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_ADVANCED: Funções Avançadas submenu (stacked options)
ui.add_screen('FS_ADVANCED', [
    ('Selecionar colunas', lambda: goto_screen_by_title('FS_SELECT_COLUMNS')),
    ('Modo operação', lambda: goto_screen_by_title('FS_OPMODE')),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_ADVANCED':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_SELECT_COLUMNS: selection UI that draws a small robot with 4 wheel options
ui.add_screen('FS_SELECT_COLUMNS', [
    ('Roda TL', None),
    ('Roda TR', None),
    ('Roda BL', None),
    ('Roda BR', None),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_SELECT_COLUMNS':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_OPMODE: Modo operação submenu (stacked options: Malha aberta / Malha fechada)
ui.add_screen('FS_OPMODE', [
    ('Malha aberta', None),
    ('Malha fechada', None),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_OPMODE':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_LIGHTS: Luz sinalizadora submenu (two side-by-side options)
ui.add_screen('FS_LIGHTS', [
    ('Habilitar', None),
    ('Desabilitar', None),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_LIGHTS':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_BASIC: Funções Basicas submenu (two side-by-side options)
ui.add_screen('FS_BASIC', [
    ('Autonivelamento', lambda: goto_screen_by_title('FS_AUTONIVEL')),
    ('Freio', lambda: goto_screen_by_title('FS_FREIO')),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_BASIC':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_AUTONIVEL: Autonivelamento screen (Habilitar / Desabilitar side-by-side)
ui.add_screen('FS_AUTONIVEL', [
    ('Habilitar', None),
    ('Desabilitar', None),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_AUTONIVEL':
            s['navigable'] = False
            break
except Exception:
    pass

# FS_FREIO: Freio screen (Habilitar / Desabilitar side-by-side)
ui.add_screen('FS_FREIO', [
    ('Habilitar', None),
    ('Desabilitar', None),
])
try:
    for s in ui.screens:
        if s.get('title') == 'FS_FREIO':
            s['navigable'] = False
            break
except Exception:
    pass

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
    # process mouse button down events separately and forward to UI (safe, limited)
    try:
        for ev in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
            try:
                if globals().get('ui') is not None and hasattr(globals().get('ui'), 'process_mouse_event'):
                    globals().get('ui').process_mouse_event(ev)
            except Exception:
                pass
    except Exception:
        # ignore event polling issues to preserve existing behavior
        pass
    # Process keydown events for actions that are better handled as discrete events
    try:
        for ev in pygame.event.get([pygame.KEYDOWN]):
            try:
                # F11 toggles fullscreen
                if ev.key == pygame.K_F11:
                    toggle_fullscreen()
                # Alt+Enter also toggles fullscreen on many platforms
                if ev.key == pygame.K_RETURN and (ev.mod & pygame.KMOD_ALT):
                    toggle_fullscreen()
                # forward KEYDOWN to UI manager if it can accept event objects
                if globals().get('ui') is not None and hasattr(globals().get('ui'), 'process_key_event'):
                    # keep compatibility: process_key_event expects a key constant
                    try:
                        globals().get('ui').process_key_event(ev.key)
                    except Exception:
                        pass
            except Exception:
                pass
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
                # debug print removed
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

    # Panel navigation keys (Tab to cycle screens, arrows to move, Enter to activate)
    try:
        # use edge-detection: key pressed now and not pressed previously
        if keys[pygame.K_TAB] and not prev_keys[pygame.K_TAB]:
            ui.process_key_event(pygame.K_TAB)
        if keys[pygame.K_UP] and not prev_keys[pygame.K_UP]:
            ui.process_key_event(pygame.K_UP)
        if keys[pygame.K_DOWN] and not prev_keys[pygame.K_DOWN]:
            ui.process_key_event(pygame.K_DOWN)
        if keys[pygame.K_LEFT] and not prev_keys[pygame.K_LEFT]:
            ui.process_key_event(pygame.K_LEFT)
        if keys[pygame.K_RIGHT] and not prev_keys[pygame.K_RIGHT]:
            ui.process_key_event(pygame.K_RIGHT)
        if keys[pygame.K_RETURN] and not prev_keys[pygame.K_RETURN]:
            ui.process_key_event(pygame.K_RETURN)
    except Exception:
        pass

    prev_keys = keys

    # Panel navigation keys (Tab to cycle screens, arrows to move, Enter to activate)
    try:
        if keys[pygame.K_TAB] and not prev_keys[pygame.K_TAB]:
            ui.next_screen()
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
                    # debug print removed
                    player.move(keys, speed=move_speed)
            else:
                # joystick not available at runtime; fall back
                control_mode = 'keyboard'
                # debug print removed
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
                    try:
                        trafo_pickup_time = pygame.time.get_ticks()
                    except Exception:
                        pass
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
        mode_str = f'Mode: {player.curve_mode}  Velocidade: {speed_label} ({speed_pct}%)'
        # draw control mode + zoom + hardcore state at top-left for quick debug
        try:
            hud_text = font.render(f'Control: {control_mode.upper()}  Zoom: {camera.scale:.2f}  Hardcore: {"ON" if hardcore_mode else "OFF"}', True, (255,255,255))
            screen.blit(hud_text, (8, 8))
            # print control mode change only once to avoid log spam
            if control_mode != last_printed_control_mode:
                # debug print removed
                last_printed_control_mode = control_mode
        except Exception:
            pass
        # Persistent badge showing that trafo is currently carried (screen-anchored)
        try:
            if 'trafo' in globals() and getattr(trafo, 'picked', False):
                badge_font = pygame.font.SysFont(None, 20)
                badge_txt = badge_font.render('Trafo: CARRIED', True, (255, 255, 255))
                bx, by = 8, 36
                bg = pygame.Surface((badge_txt.get_width() + 12, badge_txt.get_height() + 8), pygame.SRCALPHA)
                bg.fill((200, 40, 40, 200))
                screen.blit(bg, (bx - 6, by - 4))
                screen.blit(badge_txt, (bx, by))
        except Exception:
            pass
        # Delegate icamento UI drawing to Player
        try:
            if hasattr(player, 'draw_icamento_ui'):
                player.draw_icamento_ui(screen)
        except Exception:
            pass
        # Draw a transient indicator when trafo was recently picked up
        try:
            now_pick = pygame.time.get_ticks()
            if 'trafo_pickup_time' in globals() and trafo_pickup_time and (now_pick - trafo_pickup_time) < TRAFO_PICKUP_DISPLAY_MS:
                # Use a larger, more visible font and place the indicator
                # just above the bottom-left HUD so it's easy to spot.
                pick_font = pygame.font.SysFont(None, 28)
                pick_txt = pick_font.render('Trafo picked up!', True, (40, 220, 40))
                # position above the lower-left mode string
                pad = 8
                mode_y = screen.get_height() - font.get_height() - pad
                py = mode_y - pick_txt.get_height() - 12
                px = screen.get_width() // 2 - pick_txt.get_width() // 2
                bg = pygame.Surface((pick_txt.get_width() + 20, pick_txt.get_height() + 12), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 180))
                screen.blit(bg, (px - 10, py - 6))
                screen.blit(pick_txt, (px, py))
        except Exception:
            pass
        # Restore original bottom-left mode display
        padding = 8
        x = padding
        y = screen.get_height() - font.get_height() - padding
        bg_w = font.size(mode_str)[0] + padding * 2
        bg_h = font.get_height() + padding
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        screen.blit(bg_surf, (x - padding, y - padding//2))
        mode_text_render = font.render(mode_str, True, (255, 255, 255))
        screen.blit(mode_text_render, (x, y))
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
        # Determine mode text and warning
        # Map curve_mode to display string
        curve_mode = getattr(player, 'curve_mode', 'desconhecido')
        if curve_mode in ('straight', 'curve'):
            mode_text = 'Modo: Normal'
        elif curve_mode == 'pivotal':
            mode_text = 'Modo: Rotação'
        elif curve_mode == 'diagonal':
            mode_text = 'Modo: Desliza'
        elif curve_mode == 'icamento':
            mode_text = 'Modo: Içamento'
        else:
            mode_text = f'Modo: {curve_mode}'
        warning = None
        # Trigger warning if player.lights[0] (red light) is on
        if hasattr(player, 'lights') and len(player.lights) > 0 and player.lights[0]:
            warning = 'ERRO'
        # Otherwise, use error/warning attributes
        elif hasattr(player, 'error') and player.error:
            warning = str(player.error)
        elif hasattr(player, 'warning') and player.warning:
            warning = str(player.warning)
        # If error is True, show 'ERRO'
        if warning and warning.lower() == 'erro':
            warning = 'ERRO'
        ui.draw(screen, mode_text=mode_text, warning=warning)
    except Exception:
        pass
    pygame.display.flip()
    clock.tick(60)
    



"""
Trafo Simulator - Main game loop and orchestration.

This file is now focused on the main game loop and game orchestration.
Game logic has been modularized into separate files for better maintainability:
- config.py: Configuration and constants
- initialization.py: Game initialization
- collision.py: Collision detection
- accelerometer.py: Accelerometer simulation
- input_handler.py: Input processing
- rendering.py: Rendering and drawing

This makes the code more modular, testable, and maintainable.
"""

import pygame
import math
import os
import sys

from game.tutorial_progress import (
    get_next_tutorial_map,
    is_tutorial_map,
    mark_tutorial_level_completed,
)

# Import configuration
from game.config import (
    SCREEN_W, SCREEN_H, PANEL_WIDTH, BOTTOM_BAR_HEIGHT,
    TARGET_FPS, CONTROL_MODE_KEYBOARD, CONTROL_MODE_JOYSTICK,
    DEFAULT_HARDCORE_MODE, DEFAULT_FULLSCREEN_MODE, DEFAULT_TTC_CONTROL,
    CAN_MOVEMENT_NEUTRAL, CAN_MOVEMENT_MAX, CAN_MOVEMENT_MIN,
    ACCELEROMETER_MAX_VALUE, TRAFO_DEATH_LOCK_MS, TRAFO_PICKUP_DISPLAY_MS,
    COLOR_SKY_BLUE,
)

# Import modules
from game.initialization import setup_game_objects
from game.input_handler import InputHandler
from game.collision import (
    find_green_center, find_blue_center, check_player_collision_with_map, 
    poly_rect_collision, line_rect_collision
)
from game.accelerometer import (
    calculate_accelerometer_value, determine_light_mode, get_icamento_mm,
    can_pickup_trafo,
)
from game.rendering import (
    draw_map, draw_ui_panels, draw_hud_info, draw_trafo_carried_badge,
    draw_trafo_pickup_indicator, draw_collision_overlay, setup_world_view_rect,
)

# Import UI
from ui.menu_screen import run_start_menu
from ui.control_screen import run_control_screen
from ui.pausemenu import create_pause_menu

try:
    from ui.screens.map_select_screen import run_map_select_menu, run_tutorial_select_menu
except Exception:
    run_map_select_menu = None
    run_tutorial_select_menu = None


PROJECT_ROOT = os.path.dirname(__file__)
TUTORIAL_COMPLETED_BANNER_MS = 2600


def toggle_fullscreen():
    """Toggle fullscreen mode."""
    global screen, is_fullscreen, _windowed_size
    try:
        if is_fullscreen:
            screen = pygame.display.set_mode(_windowed_size)
            is_fullscreen = False
        else:
            _windowed_size = screen.get_size()
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            is_fullscreen = True
    except Exception:
        pass


def show_start_menu():
    """Show the start menu and map selection."""
    global selected_map_path, hardcore_mode, ttc_control, start_menu_desired_fullscreen
    
    _initial_cfg = {'hardcore': False, 'fullscreen': False}
    _cfg_res, _action = run_start_menu(screen, _initial_cfg)
    selected_map_path = None
    
    # Loop until a map is chosen or user exits
    while _action == 'map_select' or _action == 'control' or _action == 'tutorial':
        if _action == 'control':
            # Show control screen
            _control_action = run_control_screen(screen)
            if _control_action == 'exit':
                pygame.quit()
                sys.exit(0)
            # Return to start menu
            _cfg_res, _action = run_start_menu(screen, _cfg_res)
        elif _action == 'map_select':
            if run_map_select_menu is not None:
                sel = run_map_select_menu(screen)
            else:
                sel = None
            
            if sel:
                selected_map_path = sel
                break
            
            _cfg_res, _action = run_start_menu(screen, _cfg_res)
        elif _action == 'tutorial':
            if run_tutorial_select_menu is not None:
                sel = run_tutorial_select_menu(screen, PROJECT_ROOT)
            else:
                sel = get_next_tutorial_map(PROJECT_ROOT)
            if sel:
                selected_map_path = sel
                break

            _cfg_res, _action = run_start_menu(screen, _cfg_res)
    
    if _action == 'exit':
        pygame.quit()
        sys.exit(0)
    
    # Apply settings
    hardcore_mode = bool(_cfg_res.get('hardcore', False))
    start_menu_desired_fullscreen = bool(_cfg_res.get('fullscreen', False))
    ttc_control = bool(_cfg_res.get('ttc_control', False))
    
    return selected_map_path


def reset_trafo():
    """Reset trafo to its initial position."""
    global trafo
    try:
        if hasattr(trafo, 'initial_pos'):
            ix, iy = trafo.initial_pos
            trafo.x = ix
            trafo.y = iy
            trafo.picked = False
            trafo.carrier = None
    except Exception:
        pass


def goto_screen_by_title(title):
    """Navigate to UI screen by title."""
    try:
        for i, s in enumerate(ui.screens):
            if s.get('title') == title:
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


def toggle_hardcore():
    """Toggle hardcore mode."""
    global hardcore_mode
    hardcore_mode = not hardcore_mode


def toggle_ttc_control():
    """Toggle ttc control mode."""
    global ttc_control, control_mode, joystick_available
    ttc_control = not ttc_control
    
    try:
        if ttc_control:
            control_mode = 'ttc_active'
        elif joystick_available:
            control_mode = CONTROL_MODE_JOYSTICK
        else:
            control_mode = CONTROL_MODE_KEYBOARD
    except Exception:
        pass


def init_tutorial_state(map_path, dialogue_mgr, event_map):
    """Initialize tutorial progression tracking for the current map."""
    global is_current_map_tutorial, tutorial_available_event_ids
    global tutorial_visited_event_ids, tutorial_phase_completed
    global tutorial_completion_show_until, tutorial_completion_zone
    global tutorial_completion_mode

    is_current_map_tutorial = is_tutorial_map(PROJECT_ROOT, map_path)

    tutorial_available_event_ids = set()
    tutorial_visited_event_ids = set()
    tutorial_phase_completed = False
    tutorial_completion_show_until = 0
    tutorial_completion_zone = None
    tutorial_completion_mode = 'dialogue'

    if not is_current_map_tutorial:
        return

    try:
        phase_config = {}
        if event_map is not None and hasattr(event_map, 'get_phase_config'):
            phase_config = event_map.get_phase_config() or {}

        tutorial_completion_mode = str(phase_config.get('completion_condition', 'dialogue')).lower()

        if tutorial_completion_mode == 'zone' and event_map is not None and hasattr(event_map, 'get_completion_zone'):
            tutorial_completion_zone = event_map.get_completion_zone()
    except Exception:
        tutorial_completion_mode = 'dialogue'
        tutorial_completion_zone = None

    try:
        available_ids = dialogue_mgr.get_available_dialog_ids()
        tutorial_available_event_ids = {int(v) for v in available_ids if int(v) > 0}
    except Exception:
        tutorial_available_event_ids = set()


def setup_ui_screens():
    """Setup all UI screens and menus."""
    # Main screen
    ui.add_screen('Main', [
        (f'Mode: {getattr(player, "curve_mode", "unknown")}', None),
        ('Sensores', lambda: goto_screen_by_title('Sensores')),
        ('Controle', lambda: goto_screen_by_title('Controle')),
        ('Toggle Hardcore', toggle_hardcore),
        ('Reset Trafo', reset_trafo),
    ])

    # Menu_01: Functions submenu
    ui.add_screen('Menu_01', [
        ('Funções de Segurança', lambda: goto_screen_by_title('FS_MENU')),
        ('Sensores', lambda: goto_screen_by_title('Sensores')),
        ('Luz Sinalz.', lambda: goto_screen_by_title('FS_LIGHTS')),
    ])
    
    # Sensores screens (display-only)
    ui.add_screen('Sensores', [])
    try:
        for s in ui.screens:
            if s.get('title') == 'Sensores':
                s['navigable'] = False
                break
    except Exception:
        pass

    ui.add_screen('Sensores_2', [])
    try:
        for s in ui.screens:
            if s.get('title') == 'Sensores_2':
                s['navigable'] = False
                break
    except Exception:
        pass

    # Controle screen (with back button)
    ui.add_screen('Controle', [
        ('Voltar', lambda: goto_screen_by_title('Main')),
    ])

    # Make Menu_01 non-navigable
    try:
        for s in ui.screens:
            if s.get('title') == 'Menu_01':
                s['navigable'] = False
                break
    except Exception:
        pass

    # FS_MENU: Safety Functions submenu
    ui.add_screen('FS_MENU', [
        ('Funções Basicas', lambda: goto_screen_by_title('FS_BASIC')),
        ('Funções Avançadas', lambda: goto_screen_by_title('FS_ADVANCED')),
    ])
    try:
        for s in ui.screens:
            if s.get('title') == 'FS_MENU':
                s['navigable'] = False
                break
    except Exception:
        pass

    # FS_BASIC and FS_ADVANCED submenus
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

    # Individual feature screens
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

    globals()['ui'] = ui


# ============================================================================
# INITIALIZATION
# ============================================================================

# Create a temporary screen for menus
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Trafo Simulador de Treinamento")

# Show start menu
selected_map_path = show_start_menu()

# Setup game objects
game_state = setup_game_objects(screen=None, selected_map_path=selected_map_path)

# Extract game objects
screen = game_state['screen']
map_image = game_state['map_image']
collision_grid = game_state['collision_grid']
dialogue_manager = game_state['dialogue_manager']
player = game_state['player']
camera = game_state['camera']
trafo = game_state['trafo']
ui = game_state['ui']
joystick_controller = game_state['joystick_controller']
joystick_available = game_state['joystick_available']
spawn_point = game_state['spawn_point']
event_map = game_state['event_map']

# ===== APPLY EventMap PHASE CONFIGURATIONS =====
# Remover trafo se a configuração do mapa diz para não spawnar
if not event_map.has_trafo_spawn():
    trafo = None
    print("[Game] Trafo desativado para este mapa (phase_config: spawn_trafo=False)")

# Forçar modo hardcore se necessário
if event_map.is_hardcore_mode_forced():
    hardcore_mode = True
    print("[Game] Modo Hardcore FORÇADO neste mapa (phase_config: force_hardcore_mode=True)")

# Obter modos de operação disponíveis, restringir ao player
available_robot_modes = event_map.get_available_robot_modes()
player.available_modes = available_robot_modes  # ← Repassar restrição ao player
print(f"[Game] Modos de operação disponíveis neste mapa: {available_robot_modes}")
# ===== END EventMap CONFIGURATION =====

# Initialize game state variables
is_fullscreen = False
_windowed_size = (SCREEN_W, SCREEN_H)
start_menu_desired_fullscreen = False
ttc_control = DEFAULT_TTC_CONTROL
hardcore_mode = hardcore_mode  # Se foi forçado acima, mantém True
control_mode = 'ttc_active' if ttc_control else (CONTROL_MODE_JOYSTICK if joystick_available else CONTROL_MODE_KEYBOARD)
last_printed_control_mode = control_mode

is_current_map_tutorial = False
tutorial_available_event_ids = set()
tutorial_visited_event_ids = set()
tutorial_phase_completed = False
tutorial_completion_show_until = 0
tutorial_completion_zone = None

can_movement_value = CAN_MOVEMENT_NEUTRAL
current_accelerometer_value = 0
trafo_pickup_time = 0
trafo_death_expire = 0

lever_state = {
    'mode_position': 0,
    'speed_position': 1,
}

# Setup UI screens
setup_ui_screens()
init_tutorial_state(selected_map_path, dialogue_manager, event_map)

# Helper functions for PauseMenu callbacks
def _get_global_var(key):
    """Get a global variable value."""
    try:
        return globals()[key]
    except KeyError:
        return None

def _set_global_var(key, value):
    """Set a global variable value."""
    try:
        globals()[key] = value
    except Exception:
        pass


def _close_joystick_controller(ctrl):
    """Best-effort shutdown of joystick/CAN resources."""
    try:
        if ctrl is not None and hasattr(ctrl, 'close'):
            ctrl.close()
    except Exception:
        pass

# Create pause menu with callbacks
pause_menu = create_pause_menu(
    toggle_fullscreen_fn=toggle_fullscreen,
    get_global_fn=_get_global_var,
    set_global_fn=_set_global_var,
)

# Apply fullscreen if requested
if start_menu_desired_fullscreen and not is_fullscreen:
    try:
        toggle_fullscreen()
    except Exception:
        pass

# Initialize input handler
input_handler = InputHandler()
# Initialize previous keys state to enable edge detection from the start
input_handler.update_previous_keys(pygame.key.get_pressed())

# ============================================================================
# MAIN GAME LOOP
# ============================================================================

clock = pygame.time.Clock()
running = True
trafo_caused_death = False

# Fixed timestep: 60 ticks por segundo para lógica
LOGIC_TICK_TIME = 16.67  # ms (1000 / 60)
accumulated_time = 0.0   # acumulador de tempo real

while running:
    # Render loop sem limite de FPS. A lógica usa fixed timestep de 60 ticks.
    dt_real = clock.tick(0)  # tempo real em ms desde último frame
    accumulated_time += dt_real
    pending_pause_action = None
    
    # ========== EVENT HANDLING ==========
    try:
        pygame.event.pump()
    except Exception:
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
        except Exception:
            pass

    # Window close (X button)
    try:
        for _ in pygame.event.get([pygame.QUIT]):
            running = False
            break
    except Exception:
        pass

    if not running:
        break
    
    # Mouse events
    try:
        for ev in pygame.event.get([pygame.MOUSEBUTTONDOWN]):
            try:
                if pause_menu.is_open:
                    handled, action = pause_menu.handle_mouse_event(ev)
                    if action is not None:
                        pending_pause_action = action
                    if handled:
                        continue
                if globals().get('ui') is not None and hasattr(globals().get('ui'), 'process_mouse_event'):
                    globals().get('ui').process_mouse_event(ev)
            except Exception:
                pass
    except Exception:
        pass
    
    # Keyboard events
    try:
        for ev in pygame.event.get([pygame.KEYDOWN]):
            try:
                if ev.key == pygame.K_F11:
                    toggle_fullscreen()
                if ev.key == pygame.K_RETURN and (ev.mod & pygame.KMOD_ALT):
                    toggle_fullscreen()
                if (not pause_menu.is_open) and globals().get('ui') is not None and hasattr(globals().get('ui'), 'process_key_event'):
                    try:
                        globals().get('ui').process_key_event(ev.key)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass
    
    # Joystick polling
    try:
        if getattr(joystick_controller, 'available', False) and hasattr(joystick_controller, 'poll'):
            try:
                joystick_controller.poll()
                # Copy values to avoid aliasing player and joystick internal lists.
                player.lights = list(joystick_controller.lights)
            except Exception:
                joystick_controller.available = False
    except Exception:
        pass

    # ========== FIXED LOGIC TIMESTEP (60 ticks/segundo) ==========
    # Processa quantos ticks de lógica forem necessários
    while accumulated_time >= LOGIC_TICK_TIME:
        accumulated_time -= LOGIC_TICK_TIME
        dt = LOGIC_TICK_TIME  # cada tick sempre usa 16.67ms
        
        # Incrementa contador de ticks lógicos (sincroniza pisca de alertas, etc.)
        player.logic_tick_count += 1
        trafo_caused_death = False

        # Process mode change from joystick
        try:
            if getattr(joystick_controller, 'available', False) and getattr(joystick_controller, 'hasChangedMode', False):
                try:
                    sel = getattr(joystick_controller, 'currentMode', 0)
                    mode_map = {
                        1: 'straight',
                        2: 'diagonal',
                        4: 'pivotal',
                        8: 'icamento'
                    }
                    new_mode = mode_map.get(sel)
                    if new_mode and new_mode in available_robot_modes:
                        try:
                            player.setMode(new_mode)
                        except Exception:
                            pass
                    elif new_mode:
                        # Modo não está disponível neste mapa
                        print(f"[Game] Modo '{new_mode}' não disponível. Modos: {available_robot_modes}")
                finally:
                    joystick_controller.hasChangedMode = False
        except Exception:
            pass

        # Process speed change from joystick
        try:
            if getattr(joystick_controller, 'available', False) and getattr(joystick_controller, 'hasChangedSpeed', False):
                try:
                    sel = getattr(joystick_controller, 'currentSpeed', 0)
                    speed_map = {
                        0: 'rápida',
                        1: 'média',
                        3: 'lenta'
                    }
                    new_speed = speed_map.get(sel)
                    if new_speed:
                        player.set_speed_mode(new_speed)
                finally:
                    joystick_controller.hasChangedSpeed = False
        except Exception:
            pass

        # ========== INPUT PROCESSING ==========
        keys = pygame.key.get_pressed()
        
        # Process keyboard input
        try:
            input_handler.process_space_key(keys, player)
            input_handler.process_speed_keys(keys, player)
            input_handler.process_lever_keys(keys, lever_state)
            
            if not pause_menu.is_open:
                pause_result = input_handler.process_pause_keys(keys, pause_menu)
                if pause_result == 'exit_game':
                    running = False
            
            if not pause_menu.is_open:
                input_handler.process_ui_navigation_keys(keys, ui)
            
            if not pause_menu.is_open:
                zoom_changed = input_handler.process_zoom_keys(keys, camera, dt)
                if zoom_changed:
                    camera.update(player)
        except Exception:
            pass

        input_handler.update_previous_keys(keys)

        # ========== GAME LOGIC (executado a 60 ticks/segundo) ==========
        
        # Calculate movement speed
        try:
            move_speed = player.base_speed * player.get_speed_multiplier()
        except Exception:
            move_speed = 3
        
        # Process movement
        if not pause_menu.is_open:
            try:
                control_mode = input_handler.process_movement(
                    keys, player, joystick_controller,
                    ttc_control, move_speed, dt_ms=dt
                )
            except Exception:
                pass

        # Process dialogue manager
        try:
            current_dialog_id = 0
            if dialogue_manager.enabled and hasattr(player, 'get_body_polygon'):
                current_dialog_id = dialogue_manager.process_player_polygon(player.get_body_polygon(), auto_print=False)

            if is_current_map_tutorial and (not tutorial_phase_completed):
                if tutorial_completion_mode == 'zone' and tutorial_completion_zone is not None and hasattr(player, 'get_body_polygon'):
                    try:
                        if poly_rect_collision(player.get_body_polygon(), tutorial_completion_zone):
                            tutorial_phase_completed = True
                            mark_tutorial_level_completed(PROJECT_ROOT, selected_map_path)
                            tutorial_completion_show_until = pygame.time.get_ticks() + TUTORIAL_COMPLETED_BANNER_MS
                    except Exception:
                        pass
                elif tutorial_completion_mode == 'dialogue':
                    if current_dialog_id in tutorial_available_event_ids:
                        tutorial_visited_event_ids.add(current_dialog_id)

                    # Fallback: a tutorial phase completes after all event blocks in EventMap are visited.
                    if tutorial_available_event_ids and tutorial_available_event_ids.issubset(tutorial_visited_event_ids):
                        tutorial_phase_completed = True
                        mark_tutorial_level_completed(PROJECT_ROOT, selected_map_path)
                        tutorial_completion_show_until = pygame.time.get_ticks() + TUTORIAL_COMPLETED_BANNER_MS
                else:
                    # completion_condition is set to 'none' or an unknown value; do nothing.
                    pass
        except Exception:
            pass

        # Calculate accelerometer and determine light alerts
        try:
            current_accelerometer_value = calculate_accelerometer_value(player, map_image)
            icamento_mm = get_icamento_mm(player)
            external_lights_active = bool(getattr(joystick_controller, 'available', False))
            
            chosen_mode, chosen_hz, chosen_level, fixed_light_mode = determine_light_mode(
                current_accelerometer_value, icamento_mm, dialogue_manager
            )

            # Local alert lights are computed independently and then merged with TTC.
            local_red = False
            local_yellow = False

            if fixed_light_mode == 'alerta':
                local_yellow = True
            elif fixed_light_mode == 'critico':
                local_red = True
            elif chosen_mode is not None:
                try:
                    hz = float(chosen_hz)
                except Exception:
                    hz = 0.0

                if hz > 0:
                    half_period_ticks = 60.0 / hz
                    full_period_ticks = half_period_ticks * 2.0
                    cycle_position = int(player.logic_tick_count % full_period_ticks)
                    blink_on = cycle_position < half_period_ticks
                    if chosen_mode == 'critico':
                        local_red = bool(blink_on)
                    else:
                        local_yellow = bool(blink_on)

            if external_lights_active:
                # Coexistence rule: TTC state is preserved; local alerts only add ON states.
                player.lights[0] = bool(player.lights[0] or local_red)
                player.lights[2] = bool(player.lights[2] or local_yellow)
            else:
                # No TTC available: local alert system fully drives the warning lamps.
                player.lights[0] = local_red
                player.lights[2] = local_yellow

            # Send accelerometer via CAN if available
            if getattr(joystick_controller, 'available', False) and hasattr(joystick_controller, 'send_inclinometer'):
                joystick_controller.send_inclinometer(current_accelerometer_value)
        except Exception:
            current_accelerometer_value = 0
            try:
                if not bool(getattr(joystick_controller, 'available', False)):
                    player.lights[0] = False
                    player.lights[2] = False
            except Exception:
                pass

        # Update camera
        camera.update(player)

        # ========== TRAFO INTERACTIONS ==========
        try:
            trafo.update(dt)
            
            if not trafo.picked and player.state == 'vivo':
                # Check trafo collision with player
                trafo_rect = trafo.get_collision_rect() if hasattr(trafo, 'get_collision_rect') else trafo.get_rect()
                parts = player.get_rotated_hitbox()
                trafo_collision = False

                try:
                    px, py = player.getPosition()
                    heading_rad = math.radians(player.getHeading())
                    forward_vec = (math.sin(heading_rad), -math.cos(heading_rad))
                except Exception:
                    px = py = 0.0
                    forward_vec = (0.0, -1.0)

                for idx, (kind, data) in enumerate(parts):
                    if kind == 'wheel':
                        try:
                            hit = poly_rect_collision(data, trafo_rect)
                        except Exception:
                            hit = False

                        if not hit:
                            try:
                                xs = [p[0] for p in data]
                                ys = [p[1] for p in data]
                                wmin = min(xs); wmax = max(xs)
                                hmin = min(ys); hmax = max(ys)
                                wheel_aabb = pygame.Rect(wmin, hmin, wmax - wmin, hmax - hmin)
                                if wheel_aabb.colliderect(trafo_rect):
                                    hit = True
                            except Exception:
                                pass

                        if hit:
                            trafo_collision = True
                            break

                    elif kind in ('edge', 'line'):
                        try:
                            p1, p2 = data
                            midx = (p1[0] + p2[0]) * 0.5
                            midy = (p1[1] + p2[1]) * 0.5
                            vx = midx - px
                            vy = midy - py
                            dot = vx * forward_vec[0] + vy * forward_vec[1]
                            
                            if dot > 0:
                                if line_rect_collision(p1, p2, trafo_rect):
                                    trafo_collision = True
                                    break
                        except Exception:
                            pass

                if trafo_collision:
                    try:
                        player.set_dead()
                        trafo_caused_death = True
                        expire = pygame.time.get_ticks() + TRAFO_DEATH_LOCK_MS
                        trafo_death_expire = expire
                        try:
                            player.death_lock_until = expire
                        except Exception:
                            pass
                    except Exception:
                        pass
                else:
                    # Try pickup
                    if can_pickup_trafo(player):
                        try:
                            picked = player.try_pickup(trafo)
                            if picked:
                                trafo_pickup_time = pygame.time.get_ticks()
                        except Exception:
                            pass
        except Exception:
            pass

        # ========== COLLISION WITH MAP ==========
        collided = check_player_collision_with_map(player, collision_grid, map_image)
        
        if collided:
            player.set_dead()
        elif player.is_dead() and not hardcore_mode:
            try:
                now_ms = pygame.time.get_ticks()
            except Exception:
                now_ms = 0
            
            if now_ms > trafo_death_expire:
                try:
                    player.set_alive()
                except Exception:
                    pass

    # ========== EVENT HANDLING E PAUSE MENU (executados FORA do loop de lógica) ==========
    # Keyboard events
    try:
        for ev in pygame.event.get([pygame.KEYDOWN]):
            try:
                if ev.key == pygame.K_F11:
                    toggle_fullscreen()
                if ev.key == pygame.K_RETURN and (ev.mod & pygame.KMOD_ALT):
                    toggle_fullscreen()
                if (not pause_menu.is_open) and globals().get('ui') is not None and hasattr(globals().get('ui'), 'process_key_event'):
                    try:
                        globals().get('ui').process_key_event(ev.key)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    # Process pause menu
    try:
        pause_menu.update_settings_references()
        menu_action = pause_menu.handle_input(pygame.key.get_pressed(), input_handler.prev_keys)
        if menu_action is None:
            menu_action = pending_pause_action
        
        if menu_action == 'exit_menu':
            try:
                current_cfg = {
                    'hardcore': bool(hardcore_mode),
                    'fullscreen': bool(is_fullscreen),
                    'ttc_control': bool(ttc_control),
                }
                pause_menu.close()
                _cfg_res, _action = run_start_menu(screen, current_cfg, from_pause=True)
                hardcore_mode = bool(_cfg_res.get('hardcore', hardcore_mode))
                ttc_control = bool(_cfg_res.get('ttc_control', ttc_control))
                desired_fullscreen = bool(_cfg_res.get('fullscreen', is_fullscreen))

                _selected_map = None
                while _action in ('control', 'map_select', 'tutorial'):
                    if _action == 'control':
                        _control_action = run_control_screen(screen)
                        if _control_action == 'exit':
                            pygame.quit()
                            sys.exit(0)
                        _cfg_res, _action = run_start_menu(screen, _cfg_res, from_pause=True)
                        continue

                    if _action == 'map_select':
                        _selected = None
                        if run_map_select_menu is not None:
                            try:
                                _selected = run_map_select_menu(screen)
                            except Exception:
                                _selected = None

                        if _selected:
                            _selected_map = _selected
                            break

                        # Esc/cancel in map selector returns to start menu instead of gameplay.
                        _cfg_res, _action = run_start_menu(screen, _cfg_res, from_pause=True)
                        continue

                    if _action == 'tutorial':
                        _selected = None
                        if run_tutorial_select_menu is not None:
                            try:
                                _selected = run_tutorial_select_menu(screen, PROJECT_ROOT)
                            except Exception:
                                _selected = None
                        else:
                            _selected = get_next_tutorial_map(PROJECT_ROOT)

                        if _selected:
                            _selected_map = _selected
                            break

                        # Esc/cancel in tutorial selector returns to start menu instead of gameplay.
                        _cfg_res, _action = run_start_menu(screen, _cfg_res, from_pause=True)

                if _selected_map:
                    selected_map_path = _selected_map
                    _close_joystick_controller(joystick_controller)
                    game_state = setup_game_objects(screen=None, selected_map_path=selected_map_path)

                    screen = game_state['screen']
                    map_image = game_state['map_image']
                    collision_grid = game_state['collision_grid']
                    dialogue_manager = game_state['dialogue_manager']
                    player = game_state['player']
                    camera = game_state['camera']
                    trafo = game_state['trafo']
                    ui = game_state['ui']
                    joystick_controller = game_state['joystick_controller']
                    joystick_available = game_state['joystick_available']
                    spawn_point = game_state['spawn_point']
                    event_map = game_state['event_map']

                    # Apply EventMap phase configurations
                    if not event_map.has_trafo_spawn():
                        trafo = None
                        print("[Game] Trafo desativado para este mapa")
                    
                    if event_map.is_hardcore_mode_forced():
                        hardcore_mode = True
                        print("[Game] Modo Hardcore FORÇADO neste mapa")
                    
                    available_robot_modes = event_map.get_available_robot_modes()
                    player.available_modes = available_robot_modes  # ← Repassar restrição ao player
                    print(f"[Game] Modos de operação disponíveis: {available_robot_modes}")

                    setup_ui_screens()

                    try:
                        _windowed_size = screen.get_size()
                    except Exception:
                        _windowed_size = (SCREEN_W, SCREEN_H)
                    is_fullscreen = False

                    control_mode = 'ttc_active' if ttc_control else (CONTROL_MODE_JOYSTICK if joystick_available else CONTROL_MODE_KEYBOARD)
                    last_printed_control_mode = control_mode

                    can_movement_value = CAN_MOVEMENT_NEUTRAL
                    current_accelerometer_value = 0
                    trafo_pickup_time = 0
                    trafo_death_expire = 0
                    init_tutorial_state(selected_map_path, dialogue_manager, event_map)

                if desired_fullscreen != bool(is_fullscreen):
                    toggle_fullscreen()
                if _action == 'exit':
                    _close_joystick_controller(joystick_controller)
                    pygame.quit()
                    sys.exit(0)
            except Exception:
                pass
        elif menu_action == 'exit_game':
            _close_joystick_controller(joystick_controller)
            pygame.quit()
            sys.exit(0)
    except Exception:
        pass

    # ========== RENDERING (executado a cada frame, sem limite de FPS) ==========
    
    # Verifica morte do jogador fora do loop de lógica
    show_collision_overlay = False
    if player.is_dead():
        if hardcore_mode:
            def reset_player():
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
                player.respawn(spawn_point)
            
            camera.death_screen(screen, player, reset_player)
            continue
        else:
            show_collision_overlay = True
    
    screen.fill(COLOR_SKY_BLUE)
    
    # Setup world view
    world_view_rect = setup_world_view_rect(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT)
    
    try:
        sw, sh = screen.get_size()
    except Exception:
        sw, sh = SCREEN_W, SCREEN_H
    
    try:
        camera.width = max(1, int(sw - PANEL_WIDTH))
        camera.height = max(1, int(sh - BOTTOM_BAR_HEIGHT))
    except Exception:
        pass

    # Draw map
    draw_map(screen, map_image, camera, world_view_rect)

    # Draw UI panels
    draw_ui_panels(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT)

    # Draw trafo
    try:
        prev_clip = screen.get_clip()
        world_clip_rect = pygame.Rect(0, 0, max(1, screen.get_width() - PANEL_WIDTH), 
                                      max(1, screen.get_height() - BOTTOM_BAR_HEIGHT))
        screen.set_clip(world_clip_rect)
        trafo.draw(screen, camera)
    except Exception:
        pass

    # Draw player
    player.draw(camera_or_offset=camera)
    player.curvature.update(screen)
    
    try:
        screen.set_clip(prev_clip)
    except Exception:
        pass

    # Draw HUD
    draw_hud_info(screen, player, camera, control_mode, hardcore_mode, 
                  ttc_control, current_accelerometer_value, ACCELEROMETER_MAX_VALUE)

    # Draw trafo carried badge
    if 'trafo' in globals() and getattr(trafo, 'picked', False):
        draw_trafo_carried_badge(screen)

    # Draw player icamento UI
    try:
        if hasattr(player, 'draw_icamento_ui'):
            player.draw_icamento_ui(screen)
    except Exception:
        pass

    # Draw trafo pickup indicator
    draw_trafo_pickup_indicator(screen, trafo_pickup_time)

    # Draw UI manager
    try:
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
        if hasattr(player, 'lights') and len(player.lights) > 0 and player.lights[0]:
            warning = 'ERRO'
        elif hasattr(player, 'error') and player.error:
            warning = str(player.error)
        elif hasattr(player, 'warning') and player.warning:
            warning = str(player.warning)
        
        if warning and warning.lower() == 'erro':
            warning = 'ERRO'
        
        ui.draw(screen, mode_text=mode_text, warning=warning)
    except Exception:
        pass

    # Draw dialogue
    try:
        if dialogue_manager.enabled:
            dialogue_manager.draw_dialog_box(screen, reserved_right=PANEL_WIDTH, 
                                            reserved_bottom=BOTTOM_BAR_HEIGHT)
    except Exception:
        pass

    # Draw pause menu
    try:
        pause_menu.draw(screen)
    except Exception:
        pass

    # Draw tutorial completion feedback
    try:
        if tutorial_completion_show_until > pygame.time.get_ticks():
            viewport_w = max(1, screen.get_width() - PANEL_WIDTH)
            viewport_h = max(1, screen.get_height() - BOTTOM_BAR_HEIGHT)
            viewport_rect = pygame.Rect(0, 0, viewport_w, viewport_h)

            title_font = pygame.font.SysFont(None, 86)
            sub_font = pygame.font.SysFont(None, 34)

            title = title_font.render('FASE CONCLUIDA', True, (236, 255, 244))
            subtitle = sub_font.render('Proxima fase desbloqueada', True, (198, 232, 255))

            content_w = max(title.get_width(), subtitle.get_width())
            content_h = title.get_height() + 12 + subtitle.get_height()
            box_w = content_w + 56
            box_h = content_h + 32
            box_x = viewport_rect.x + (viewport_rect.width - box_w) // 2
            box_y = viewport_rect.y + (viewport_rect.height - box_h) // 2

            box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_surface.fill((8, 28, 52, 205))
            screen.blit(box_surface, (box_x, box_y))

            pygame.draw.rect(screen, (76, 188, 255), pygame.Rect(box_x, box_y, box_w, box_h), 2)
            pygame.draw.rect(screen, (44, 180, 92), pygame.Rect(box_x + 6, box_y + 6, box_w - 12, box_h - 12), 2)

            title_x = box_x + (box_w - title.get_width()) // 2
            title_y = box_y + 10
            subtitle_x = box_x + (box_w - subtitle.get_width()) // 2
            subtitle_y = title_y + title.get_height() + 12

            shadow = title_font.render('FASE CONCLUIDA', True, (10, 18, 30))
            screen.blit(shadow, (title_x + 2, title_y + 2))
            screen.blit(title, (title_x, title_y))
            screen.blit(subtitle, (subtitle_x, subtitle_y))
    except Exception:
        pass

    # Draw collision overlay
    if show_collision_overlay:
        draw_collision_overlay(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT)

    pygame.display.flip()


_close_joystick_controller(joystick_controller)
pygame.quit()




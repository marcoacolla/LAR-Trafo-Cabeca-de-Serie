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

# Import configuration
from game.config import (
    SCREEN_W, SCREEN_H, PANEL_WIDTH, BOTTOM_BAR_HEIGHT,
    TARGET_FPS, CONTROL_MODE_KEYBOARD, CONTROL_MODE_JOYSTICK,
    DEFAULT_HARDCORE_MODE, DEFAULT_FULLSCREEN_MODE, DEFAULT_JOYSTICK_LEADING,
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
from ui.pausemenu import create_pause_menu

try:
    from ui.screens.map_select_screen import run_map_select_menu
except Exception:
    run_map_select_menu = None


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
    global selected_map_path, hardcore_mode, joystick_leading, start_menu_desired_fullscreen
    
    _initial_cfg = {'hardcore': False, 'fullscreen': False}
    _cfg_res, _action = run_start_menu(screen, _initial_cfg)
    selected_map_path = None
    
    # Loop until a map is chosen or user exits
    while _action == 'map_select':
        if run_map_select_menu is not None:
            sel = run_map_select_menu(screen)
        else:
            sel = None
        
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
    joystick_leading = bool(_cfg_res.get('joystick_leading', True))
    
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


def toggle_joystick_leading():
    """Toggle joystick leading mode."""
    global joystick_leading, control_mode, joystick_available
    joystick_leading = not joystick_leading
    
    try:
        if joystick_leading and joystick_available:
            control_mode = CONTROL_MODE_JOYSTICK
        else:
            control_mode = CONTROL_MODE_KEYBOARD
    except Exception:
        pass


def setup_ui_screens():
    """Setup all UI screens and menus."""
    # Main screen
    ui.add_screen('Main', [
        (f'Mode: {getattr(player, "curve_mode", "unknown")}', None),
        ('Sensores', lambda: goto_screen_by_title('Sensores')),
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

# Initialize game state variables
is_fullscreen = False
_windowed_size = (SCREEN_W, SCREEN_H)
start_menu_desired_fullscreen = False
joystick_leading = DEFAULT_JOYSTICK_LEADING
hardcore_mode = DEFAULT_HARDCORE_MODE
control_mode = CONTROL_MODE_JOYSTICK if (joystick_leading and joystick_available) else CONTROL_MODE_KEYBOARD
last_printed_control_mode = control_mode

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
                player.lights = joystick_controller.lights
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
                    if new_mode:
                        try:
                            player.setMode(new_mode)
                        except Exception:
                            pass
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
                    joystick_leading, move_speed, dt_ms=dt
                )
            except Exception:
                pass

        # Process dialogue manager
        try:
            if dialogue_manager.enabled and hasattr(player, 'get_body_polygon'):
                dialogue_manager.process_player_polygon(player.get_body_polygon(), auto_print=False)
        except Exception:
            pass

        # Calculate accelerometer and determine light alerts
        try:
            current_accelerometer_value = calculate_accelerometer_value(player, map_image)
            icamento_mm = get_icamento_mm(player)
            
            chosen_mode, chosen_hz, chosen_level, fixed_light_mode = determine_light_mode(
                current_accelerometer_value, icamento_mm, dialogue_manager
            )

            if fixed_light_mode == 'alerta':
                player.lights[0] = False
                player.lights[2] = True
            elif fixed_light_mode == 'critico':
                player.lights[2] = False
                player.lights[0] = True
            elif chosen_mode is not None:
                if chosen_mode == 'critico':
                    player.lights[2] = False
                else:
                    player.lights[0] = False
                player.blink_alert(chosen_hz, chosen_mode)
            else:
                player.lights[0] = False
                player.lights[2] = False

            # Send accelerometer via CAN if available
            if getattr(joystick_controller, 'available', False) and hasattr(joystick_controller, 'send_inclinometer'):
                joystick_controller.send_inclinometer(current_accelerometer_value)
        except Exception:
            current_accelerometer_value = 0
            try:
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
                    'joystick_leading': bool(joystick_leading),
                }
                pause_menu.close()
                _cfg_res, _action = run_start_menu(screen, current_cfg, from_pause=True)
                hardcore_mode = bool(_cfg_res.get('hardcore', hardcore_mode))
                joystick_leading = bool(_cfg_res.get('joystick_leading', joystick_leading))
                desired_fullscreen = bool(_cfg_res.get('fullscreen', is_fullscreen))
                if _action == 'map_select':
                    _selected = None
                    if run_map_select_menu is not None:
                        try:
                            _selected = run_map_select_menu(screen)
                        except Exception:
                            _selected = None

                    if _selected:
                        selected_map_path = _selected
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

                        setup_ui_screens()

                        try:
                            _windowed_size = screen.get_size()
                        except Exception:
                            _windowed_size = (SCREEN_W, SCREEN_H)
                        is_fullscreen = False

                        control_mode = CONTROL_MODE_JOYSTICK if (joystick_leading and joystick_available) else CONTROL_MODE_KEYBOARD
                        last_printed_control_mode = control_mode

                        can_movement_value = CAN_MOVEMENT_NEUTRAL
                        current_accelerometer_value = 0
                        trafo_pickup_time = 0
                        trafo_death_expire = 0

                if desired_fullscreen != bool(is_fullscreen):
                    toggle_fullscreen()
                if _action == 'exit':
                    pygame.quit()
                    sys.exit(0)
            except Exception:
                pass
        elif menu_action == 'exit_game':
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
                  joystick_leading, current_accelerometer_value, ACCELEROMETER_MAX_VALUE)

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

    # Draw collision overlay
    if show_collision_overlay:
        draw_collision_overlay(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT)

    pygame.display.flip()


pygame.quit()




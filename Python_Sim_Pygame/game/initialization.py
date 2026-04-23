"""
Initialization module - Handles all game initialization logic.
Loads resources, initializes objects, and sets up the game state.
"""

import pygame
import os
from .config import (
    SCREEN_W, SCREEN_H, PANEL_WIDTH, BOTTOM_BAR_HEIGHT,
    DEFAULT_SPAWN_POINT, TRAFO_SIZE, CONTROL_MODE_KEYBOARD,
    CONTROL_MODE_JOYSTICK, DEFAULT_TTC_CONTROL,
)
from .collision import find_green_center, find_blue_center, build_collision_grid
from World.World import World as world
from World.Dialogue import DialogueManager
from World.Trafo import Trafo
from World.EventMapManager import EventMapManager
from Player.Player import Player
from Camera.Camera import Camera
from Player.Joystick import Joystick as JoystickController


def init_pygame():
    """Initialize pygame and set window properties."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Trafo Simulador de Treinamento")
    
    # Load and set icon
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'World', 'trafo_image', 'trafo.png')
        if os.path.exists(icon_path):
            pygame.display.set_icon(pygame.image.load(icon_path))
    except Exception:
        pass
    
    return screen


def load_map(selected_map_path=None):
    """Load the game map image."""
    if selected_map_path:
        map_path = selected_map_path
    else:
        map_path = os.path.join(os.path.dirname(__file__), 'World', 'Obstacles', 'Map1.png')
    
    map_image = pygame.image.load(map_path).convert()
    return map_path, map_image


def infer_dialogue_phase_from_map(path):
    """Infer dialogue phase from map filename."""
    try:
        return os.path.splitext(os.path.basename(path))[0]
    except Exception:
        return 'Mapa Tutorial Alertas de Inclinação'


def init_dialogue_manager(project_root, map_path, map_image):
    """Initialize the dialogue manager."""
    dialogue_phase = infer_dialogue_phase_from_map(map_path)
    
    return DialogueManager(
        project_root=project_root,
        obstacle_map_path=map_path,
        obstacle_map_size=map_image.get_size(),
        phase=dialogue_phase,
    )


def init_player_and_camera(screen, spawn_point):
    """Initialize player and camera objects."""
    camera = Camera(max(1, SCREEN_W - PANEL_WIDTH), max(1, SCREEN_H - BOTTOM_BAR_HEIGHT))
    player = Player(spawn_point, screen, camera)
    
    return player, camera


def init_trafo(event_map, spawn_point):
    """Initialize the trafo at position defined by EventMap."""
    trafo_spawn = event_map.get_trafo_spawn()
    
    trafo = Trafo(trafo_spawn[0], trafo_spawn[1], 
                 size=TRAFO_SIZE, image_path='trafo_image/trafo.png')
    trafo.initial_pos = trafo_spawn
    
    return trafo


def init_joystick_controller(ui):
    """Initialize joystick controller."""
    joystick_controller = JoystickController(ui)
    
    try:
        joystick_available = bool(getattr(joystick_controller, 'available', False))
    except Exception:
        joystick_available = False
    
    return joystick_controller, joystick_available


def determine_initial_control_mode(ttc_control, joystick_available):
    """Determine the initial control mode."""
    try:
        if ttc_control:
            return 'ttc_active'
        elif joystick_available:
            return CONTROL_MODE_JOYSTICK
    except Exception:
        pass
    return CONTROL_MODE_KEYBOARD


def setup_game_objects(screen, selected_map_path=None):
    """
    Complete game initialization routine.
    Returns a dictionary with all initialized game objects and state.
    EventMapManager é agora responsável pela lógica do mapa (spawn points, colisões, etc.).
    """
    # Initialize pygame
    screen = init_pygame()
    
    # Load map
    map_path, map_image = load_map(selected_map_path)
    
    # Load EventMap - responsável pela lógica do mapa
    event_map = EventMapManager(map_path)
    
    # Build collision grid from map visualization
    collision_grid, occupied_pixels = build_collision_grid(map_image)
    
    # Get spawn point from EventMap (now the source of truth)
    spawn_point = event_map.get_player_spawn()
    
    # Initialize dialogue manager
    dialogue_manager = init_dialogue_manager(
        os.path.dirname(os.path.dirname(__file__)),
        map_path,
        map_image
    )
    
    # Initialize player and camera
    player, camera = init_player_and_camera(screen, spawn_point)
    
    # Update camera with map bounds
    try:
        camera.map_width = map_image.get_width()
        camera.map_height = map_image.get_height()
    except Exception:
        pass
    
    # Initialize trafo from EventMap
    trafo = init_trafo(event_map, spawn_point)
    
    # Initialize UI (import here to avoid circular imports)
    try:
        from ui.manager import UIManager
    except Exception:
        UIManager = None
    
    if UIManager is not None:
        try:
            sw, sh = screen.get_size()
        except Exception:
            sw, sh = SCREEN_W, SCREEN_H
        
        panel_h = 120
        ui_panel_rect = (sw - PANEL_WIDTH, max(0, sh - BOTTOM_BAR_HEIGHT - panel_h), 
                        PANEL_WIDTH, panel_h)
        ui = UIManager(screen, panel_rect=ui_panel_rect, player=player)
    else:
        from ui.sidepanel import SidePanel
        try:
            sw, sh = screen.get_size()
        except Exception:
            sw, sh = SCREEN_W, SCREEN_H
        
        panel_x = sw - PANEL_WIDTH
        panel_y = 0
        panel_h = max(64, sh - panel_y)
        panel_w = PANEL_WIDTH
        ui = SidePanel(panel_x, panel_y, panel_w, panel_h, layout='horizontal')
    
    # Initialize joystick
    joystick_controller, joystick_available = init_joystick_controller(ui)
    
    return {
        'screen': screen,
        'map_image': map_image,
        'map_path': map_path,
        'event_map': event_map,
        'collision_grid': collision_grid,
        'dialogue_manager': dialogue_manager,
        'player': player,
        'camera': camera,
        'trafo': trafo,
        'ui': ui,
        'joystick_controller': joystick_controller,
        'joystick_available': joystick_available,
        'spawn_point': spawn_point,
    }

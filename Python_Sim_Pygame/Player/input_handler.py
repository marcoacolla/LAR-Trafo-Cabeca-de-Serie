"""
Input handler module - Handles all keyboard and joystick input processing.
Separates input logic from main game loop for better maintainability.
"""

import pygame
from config import CONTROL_MODE_KEYBOARD, CONTROL_MODE_JOYSTICK


class InputHandler:
    """Handles all input processing for the game."""
    
    def __init__(self):
        self.prev_keys = None
        self.control_mode = CONTROL_MODE_KEYBOARD
    
    def update_previous_keys(self, current_keys):
        """Update the previous keys state."""
        self.prev_keys = current_keys
    
    def is_key_pressed_this_frame(self, key, current_keys):
        """Check if a key was just pressed (edge detection)."""
        if self.prev_keys is None:
            return current_keys[key]
        return current_keys[key] and not self.prev_keys[key]
    
    def process_space_key(self, current_keys, player):
        """Process space key for mode toggle."""
        if self.is_key_pressed_this_frame(pygame.K_SPACE, current_keys):
            try:
                player.toggle_mode()
                return True
            except Exception:
                pass
        return False
    
    def process_speed_keys(self, current_keys, player):
        """Process speed mode shortcuts (1, 2, 3)."""
        if self.is_key_pressed_this_frame(pygame.K_1, current_keys):
            try:
                player.set_speed_mode('rápida')
                return True
            except Exception:
                pass
        
        if self.is_key_pressed_this_frame(pygame.K_2, current_keys):
            try:
                player.set_speed_mode('média')
                return True
            except Exception:
                pass
        
        if self.is_key_pressed_this_frame(pygame.K_3, current_keys):
            try:
                player.set_speed_mode('lenta')
                return True
            except Exception:
                pass
        
        return False
    
    def process_lever_keys(self, current_keys, lever_state):
        """Process lever position keys (LEFT/RIGHT/UP/DOWN)."""
        changed = False
        
        if self.is_key_pressed_this_frame(pygame.K_LEFT, current_keys):
            lever_state['mode_position'] = 0
            changed = True
        
        if self.is_key_pressed_this_frame(pygame.K_RIGHT, current_keys):
            lever_state['mode_position'] = 1
            changed = True
        
        if self.is_key_pressed_this_frame(pygame.K_UP, current_keys):
            lever_state['speed_position'] = max(0, lever_state['speed_position'] - 1)
            changed = True
        
        if self.is_key_pressed_this_frame(pygame.K_DOWN, current_keys):
            lever_state['speed_position'] = min(2, lever_state['speed_position'] + 1)
            changed = True
        
        return changed
    
    def process_fullscreen_keys(self, current_keys, toggle_fullscreen_fn):
        """Process fullscreen toggle keys (F11, Alt+Enter)."""
        # Note: This is handled separately in the main loop due to event handling
        pass
    
    def process_pause_keys(self, current_keys, pause_menu):
        """Process pause menu keys (P for pause, ESC)."""
        if self.is_key_pressed_this_frame(pygame.K_p, current_keys) and not pause_menu.is_open:
            pause_menu.open()
            return True
        
        if self.is_key_pressed_this_frame(pygame.K_ESCAPE, current_keys):
            if pause_menu.is_open:
                pause_menu.close()
                return True
            else:
                return 'exit_game'
        
        return False
    
    def process_ui_navigation_keys(self, current_keys, ui):
        """Process UI navigation keys (TAB, arrows, ENTER)."""
        if ui is None:
            return
        
        try:
            if self.is_key_pressed_this_frame(pygame.K_TAB, current_keys):
                ui.next_screen()
            
            if self.is_key_pressed_this_frame(pygame.K_UP, current_keys):
                ui.select_prev()
            
            if self.is_key_pressed_this_frame(pygame.K_DOWN, current_keys):
                ui.select_next()
            
            if self.is_key_pressed_this_frame(pygame.K_RETURN, current_keys):
                ui.activate()
        except Exception:
            pass
    
    def process_zoom_keys(self, current_keys, camera, dt):
        """Process zoom control keys (J = zoom out, K = zoom in)."""
        from config import ZOOM_SPEED, MIN_CAMERA_SCALE, MAX_CAMERA_SCALE
        
        zoom_changed = False
        
        if current_keys[pygame.K_j]:
            camera.scale = max(MIN_CAMERA_SCALE, camera.scale - ZOOM_SPEED * (dt / 16.0))
            zoom_changed = True
        
        if current_keys[pygame.K_k]:
            camera.scale = min(MAX_CAMERA_SCALE, camera.scale + ZOOM_SPEED * (dt / 16.0))
            zoom_changed = True
        
        return zoom_changed
    
    def process_movement(self, current_keys, player, joystick_controller, 
                        ttc_control, move_speed, pause_menu_open=False):
        """
        Process player movement from keyboard or joystick.
        Returns the control mode used ('keyboard', 'joystick', or 'ttc_active').
        """
        if pause_menu_open:
            return self.control_mode
        
        try:
            if ttc_control:
                # TTC control is active - NO movement using joystick or keyboard
                self.control_mode = 'ttc_active'
            else:
                # TTC control is OFF - Normal mode using joystick or keyboard
                if getattr(joystick_controller, 'available', False):
                    lx, ly, rx, ry = joystick_controller.getJoystickValues()
                    player.move_with_joystick((lx, ly, rx, ry), speed=move_speed)
                    self.control_mode = CONTROL_MODE_JOYSTICK
                else:
                    # no CAN joystick available: fallback to keyboard
                    self.control_mode = CONTROL_MODE_KEYBOARD
                    player.move(current_keys, speed=move_speed)
        except Exception:
            player.move(current_keys, speed=move_speed)
            self.control_mode = CONTROL_MODE_KEYBOARD
        
        return self.control_mode

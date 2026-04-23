"""
Rendering module - Handles all drawing and visual rendering logic.
Separates rendering from game logic for better maintainability.
"""

import pygame
from .config import (
    PANEL_WIDTH,
    BOTTOM_BAR_HEIGHT,
    COLOR_BG_LIGHT,
    COLOR_BORDER,
    COLOR_BORDER_DARK,
    COLOR_SHADOW,
    COLOR_SHADOW_ALPHA,
    COLOR_SKY_BLUE,
    TRAFO_PICKUP_DISPLAY_MS,
)


def draw_map(screen, map_image, camera, world_view_rect):
    """Draw the game map with camera offset and zoom."""
    prev_clip = screen.get_clip()
    screen.set_clip(world_view_rect)
    
    if hasattr(camera, 'scale') and camera.scale != 1.0:
        map_w = int(map_image.get_width() * camera.scale)
        map_h = int(map_image.get_height() * camera.scale)
        scaled_map = pygame.transform.scale(map_image, (map_w, map_h))
        screen.blit(scaled_map, (-camera.offset_x * camera.scale, -camera.offset_y * camera.scale))
    else:
        screen.blit(map_image, (-camera.offset_x, -camera.offset_y))
    
    screen.set_clip(prev_clip)


def draw_ui_panels(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT):
    """Draw the right-side and bottom UI panels with styling."""
    try:
        sw = screen.get_width()
        sh = screen.get_height()
        
        # Draw right-side UI bar
        ui_x = max(0, sw - PANEL_WIDTH)
        ui_rect = pygame.Rect(ui_x, 0, PANEL_WIDTH, sh)
        
        # Drop shadow
        shadow_rect = ui_rect.move(4, 4)
        try:
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, COLOR_SHADOW_ALPHA))
            screen.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
        except Exception:
            pygame.draw.rect(screen, COLOR_SHADOW, shadow_rect)
        
        # Main background and borders
        pygame.draw.rect(screen, COLOR_BG_LIGHT, ui_rect)
        pygame.draw.rect(screen, COLOR_BORDER, ui_rect, 2)
        outline_rect = ui_rect.inflate(2, 2)
        pygame.draw.rect(screen, COLOR_BORDER_DARK, outline_rect, 1)

        # Bottom bar: same style
        bottom_rect = pygame.Rect(0, max(0, sh - BOTTOM_BAR_HEIGHT), 
                                  max(1, sw - PANEL_WIDTH), BOTTOM_BAR_HEIGHT)
        bottom_shadow_rect = bottom_rect.move(0, 2)
        
        try:
            bottom_shadow = pygame.Surface((bottom_shadow_rect.width, bottom_shadow_rect.height), 
                                          pygame.SRCALPHA)
            bottom_shadow.fill((0, 0, 0, 58))
            screen.blit(bottom_shadow, (bottom_shadow_rect.x, bottom_shadow_rect.y))
        except Exception:
            pygame.draw.rect(screen, (90, 98, 112), bottom_shadow_rect)
        
        pygame.draw.rect(screen, COLOR_BG_LIGHT, bottom_rect)
        pygame.draw.rect(screen, COLOR_BORDER, bottom_rect, 2)
        bottom_outline = bottom_rect.inflate(0, 1)
        pygame.draw.rect(screen, COLOR_BORDER_DARK, bottom_outline, 1)

        # Connector line at junction
        jx = max(0, sw - PANEL_WIDTH)
        jy = max(0, sh - BOTTOM_BAR_HEIGHT)
        pygame.draw.line(screen, COLOR_BORDER, (jx, jy), (jx, sh - 1), 2)
    except Exception:
        pass


def draw_hud_info(screen, player, camera, control_mode, hardcore_mode, 
                  ttc_control, accelerometer_value, ACCELEROMETER_MAX_VALUE):
    """Draw HUD information (control mode, zoom, accelerometer, etc)."""
    try:
        font = pygame.font.SysFont(None, 20)
        
        # Top-left info: control mode, zoom, hardcore, ttc_control
        hud_label = f'Control: {control_mode.upper()}  Zoom: {camera.scale:.2f}  ' \
                    f'Hardcore: {"ON" if hardcore_mode else "OFF"}  TTC.Ctrl: {"ON" if ttc_control else "OFF"}'
        hud_text = font.render(hud_label, True, (255, 255, 255))
        hud_outline = font.render(hud_label, True, (0, 0, 0))
        hud_x, hud_y = 8, 8
        
        # Draw text outline
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(hud_outline, (hud_x + ox, hud_y + oy))
        screen.blit(hud_text, (hud_x, hud_y))
        
        # Accelerometer display
        accel_text = font.render(f'Acelerômetro: {accelerometer_value} / {ACCELEROMETER_MAX_VALUE}', 
                                True, (255, 100, 100))
        screen.blit(accel_text, (8, 32))
        
        # Mode and speed display
        try:
            speed_label = player.speed_mode
            speed_pct = int(player.get_speed_multiplier() * 100)
        except Exception:
            speed_label = 'rápida'
            speed_pct = 100
        
        mode_str = f'Mode: {player.curve_mode}  Velocidade: {speed_label} ({speed_pct}%)'
        
        # Bottom-left display
        padding = 8
        x = padding
        y = screen.get_height() - font.get_height() - padding
        bg_w = font.size(mode_str)[0] + padding * 2
        bg_h = font.get_height() + padding
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        screen.blit(bg_surf, (x - padding, y - padding // 2))
        mode_text_render = font.render(mode_str, True, (255, 255, 255))
        screen.blit(mode_text_render, (x, y))
        
    except Exception:
        pass


def draw_trafo_carried_badge(screen):
    """Draw a badge indicating trafo is being carried."""
    try:
        badge_font = pygame.font.SysFont(None, 20)
        badge_txt = badge_font.render('Trafo: CARRIED', True, (255, 255, 255))
        bx, by = 8, 36
        bg = pygame.Surface((badge_txt.get_width() + 12, badge_txt.get_height() + 8), pygame.SRCALPHA)
        bg.fill((200, 40, 40, 200))
        screen.blit(bg, (bx - 6, by - 4))
        screen.blit(badge_txt, (bx, by))
    except Exception:
        pass


def draw_trafo_pickup_indicator(screen, trafo_pickup_time):
    """Draw transient indicator when trafo was recently picked up."""
    try:
        font = pygame.font.SysFont(None, 20)
        now_pick = pygame.time.get_ticks()
        
        if trafo_pickup_time and (now_pick - trafo_pickup_time) < TRAFO_PICKUP_DISPLAY_MS:
            pick_font = pygame.font.SysFont(None, 28)
            pick_txt = pick_font.render('Trafo picked up!', True, (40, 220, 40))
            
            # Position above lower-left
            pad = 8
            mode_y = screen.get_height() - font.get_height() - pad
            py = mode_y - pick_txt.get_height() - 12
            px = screen.get_width() // 2 - pick_txt.get_width() // 2
            
            bg = pygame.Surface((pick_txt.get_width() + 20, pick_txt.get_height() + 12), 
                              pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, (px - 10, py - 6))
            screen.blit(pick_txt, (px, py))
    except Exception:
        pass


def draw_collision_overlay(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT):
    """Draw the collision warning overlay."""
    try:
        fonte = pygame.font.SysFont(None, 48)

        world_w = max(1, int(screen.get_width() - PANEL_WIDTH))
        world_h = max(1, int(screen.get_height() - BOTTOM_BAR_HEIGHT))
        viewport_rect = pygame.Rect(0, 0, world_w, world_h)

        # Keeps the warning legible when the available viewport gets narrow.
        line_texts = ['Colisão Detectada!', 'Mova para sair.']
        rendered_lines = [fonte.render(line, True, (255, 0, 0)) for line in line_texts]

        line_gap = 8
        max_line_w = max(line.get_width() for line in rendered_lines)
        text_h = sum(line.get_height() for line in rendered_lines) + line_gap

        # Semi-transparent background
        bg_w = max_line_w + 40
        bg_h = text_h + 24
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))

        sx = viewport_rect.x + (viewport_rect.width - bg_w) // 2
        sy = viewport_rect.y + (viewport_rect.height - bg_h) // 2

        screen.blit(bg_surf, (sx, sy))

        y = sy + 12
        for line in rendered_lines:
            lx = sx + (bg_w - line.get_width()) // 2
            screen.blit(line, (lx, y))
            y += line.get_height() + line_gap
    except Exception:
        pass


def setup_world_view_rect(screen, PANEL_WIDTH, BOTTOM_BAR_HEIGHT):
    """Setup the world view rectangle for clipping."""
    try:
        sw, sh = screen.get_size()
    except Exception:
        from .config import SCREEN_W, SCREEN_H
        sw, sh = SCREEN_W, SCREEN_H
    
    world_view_w = max(1, int(sw - PANEL_WIDTH))
    world_view_h = max(1, int(sh - BOTTOM_BAR_HEIGHT))
    return pygame.Rect(0, 0, world_view_w, world_view_h)

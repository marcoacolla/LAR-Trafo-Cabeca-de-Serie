import pygame
from .screens.screen_base import ScreenBase

class UIManager:
    """Simple UI manager for bottom-left panel.
    Keeps screens modular; exposes navigation API compatible with previous code.
    """
    def __init__(self, screen, panel_rect=None, font=None, player=None):
        self.screen = screen
        self.font = font or pygame.font.SysFont(None, 28)
        self.screens = []
        self.current = 0
        self.selected = 0
        self.player = player
        if panel_rect is None:
            sw, sh = screen.get_width(), screen.get_height()
            self.panel_rect = pygame.Rect(8, 100, 260, 70)
            print(f"[UIManager] Panel position: {self.panel_rect}")
        else:
            self.panel_rect = pygame.Rect(panel_rect)

    def add_screen(self, title, options):
        self.screens.append({'title': title, 'options': list(options)})

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
        self.selected = min(self.selected + 1, len(opts) - 1)

    def select_prev(self):
        opts = self._opts()
        if not opts:
            return
        self.selected = max(self.selected - 1, 0)

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
        except Exception as e:
            print(f"Error running callback for {label}: {e}")

    def _opts(self):
        if not self.screens:
            return []
        return self.screens[self.current].get('options', [])

    def update_mode_display(self, new_mode):
        try:
            for s in self.screens:
                for i, (label, cb) in enumerate(s.get('options', [])):
                    if label.startswith('Mode:'):
                        s['options'][i] = (f'Mode: {new_mode}', cb)
        except Exception:
            pass

    def draw(self, surf=None, mode_text=None, warning=None):
        self.panel_rect.y = 450
        if surf is None:
            surf = self.screen
        # panel background
        pygame.draw.rect(surf, (255, 255, 255), self.panel_rect)
        pygame.draw.rect(surf, (200, 0, 0), self.panel_rect, 2)
        if not self.screens:
            t = self.font.render('Panel (empty)', True, (0, 0, 0))
            surf.blit(t, (self.panel_rect.x + 8, self.panel_rect.y + 8))
            return
        title = self.screens[self.current].get('title', '')
        # Custom main screen layout
        if title == 'Main':
            # Top row: mode, battery, exclamation
            pad = 10
            top_y = self.panel_rect.y + pad
            x = self.panel_rect.x + pad
            # Battery icon (monochrome blue)
            bx = x
            by = top_y + 2
            bw, bh = 22, 12
            pygame.draw.rect(surf, (0,70,220), (bx, by, bw, bh), 2)
            # Battery fill based on player.battery_level (0.0 to 1.0)
            battery_level = .5
            if self.player and hasattr(self.player, 'battery_level'):
                try:
                    battery_level = max(0.0, min(1.0, float(self.player.battery_level)))
                except Exception:
                    battery_level = 1.0
            fill_w = int((bw-4) * battery_level)
            pygame.draw.rect(surf, (0,120,255), (bx+2, by+2, fill_w, bh-4))
            pygame.draw.rect(surf, (0,70,220), (bx+bw, by+4, 4, 4))  # battery tip
            # Exclamation icon (blue/white logic)
            ex_x = bx + bw + 18
            ex_y = by + bh//2
            # Check player.lights[4] for blue sirene
            blue_sirene = False
            if self.player and hasattr(self.player, 'lights') and len(self.player.lights) > 4:
                blue_sirene = bool(self.player.lights[4])
            if blue_sirene:
                # Draw a larger blue ball, then white exclamation
                pygame.draw.circle(surf, (0,70,220), (ex_x, ex_y), 12)
                excl = self.font.render('!', True, (255,255,255))
                surf.blit(excl, (ex_x-5, ex_y-8))
            else:
                pygame.draw.circle(surf, (255,255,255), (ex_x, ex_y), 8)
                excl = self.font.render('!', True, (0,70,220))
                surf.blit(excl, (ex_x-5, ex_y-8))
            # Mode text
            mode_str = mode_text or 'Modo: desconhecido'
            mode_render = self.font.render(mode_str, True, (0, 70, 220))
            mode_x = ex_x + 18
            surf.blit(mode_render, (mode_x, top_y))
            # Bottom row: right side "Menu ->" + arrow
            menu_str = 'Menu'
            arrow_str = '→'
            menu_render = self.font.render(menu_str, True, (0,70,220))
            # Try to render arrow, fallback to '>' if font doesn't support
            try:
                arrow_render = self.font.render(arrow_str, True, (0,70,220))
                if arrow_render.get_width() < 5:
                    raise Exception('Arrow too small')
            except Exception:
                arrow_render = self.font.render('>', True, (0,70,220))
            menu_x = self.panel_rect.right - menu_render.get_width() - arrow_render.get_width() - pad
            menu_y = self.panel_rect.bottom - menu_render.get_height() - pad
            surf.blit(menu_render, (menu_x, menu_y))
            surf.blit(arrow_render, (menu_x + menu_render.get_width() + 2, menu_y))
            # Bottom left: warning(s) if present
            # Compose warnings: ERRO (red light), BATERIA (low battery)
            warnings_to_show = []
            if self.player:
                # ERRO: red light
                if hasattr(self.player, 'lights') and len(self.player.lights) > 0 and self.player.lights[0]:
                    warnings_to_show.append(('ERRO', 'red'))
                # BATERIA: battery low (<20%)
                if hasattr(self.player, 'battery_level'):
                    try:
                        if float(self.player.battery_level) < 0.2:
                            warnings_to_show.append(('BATERIA', 'battery'))
                    except Exception:
                        pass
            # If warning argument is set, override and show only that
            if warning:
                warnings_to_show = [(warning, 'custom')]
            aviso_pad = pad
            for idx, (warn_text, warn_type) in enumerate(warnings_to_show):
                aviso_label = 'Aviso: '
                aviso_label_render = self.font.render(aviso_label, True, (0,70,220))
                # ERRO: blue text, no background; BATERIA: white text, blue background
                if warn_type == 'red':
                    warn_render = self.font.render(warn_text, True, (0,70,220))
                    surf.blit(aviso_label_render, (self.panel_rect.x + aviso_pad, self.panel_rect.bottom - aviso_label_render.get_height()*(len(warnings_to_show)-idx) - pad))
                    surf.blit(warn_render, (self.panel_rect.x + aviso_pad + aviso_label_render.get_width(), self.panel_rect.bottom - warn_render.get_height()*(len(warnings_to_show)-idx) - pad))
                elif warn_type == 'battery':
                    warn_render = self.font.render(warn_text, True, (255,255,255))
                    bg_rect = warn_render.get_rect()
                    bg_rect.x = self.panel_rect.x + aviso_pad + aviso_label_render.get_width()
                    bg_rect.y = self.panel_rect.bottom - warn_render.get_height()*(len(warnings_to_show)-idx) - pad
                    bg_rect.width += 8
                    bg_rect.height += 2
                    pygame.draw.rect(surf, (0,70,220), bg_rect)
                    surf.blit(aviso_label_render, (self.panel_rect.x + aviso_pad, bg_rect.y))
                    surf.blit(warn_render, (bg_rect.x + 4, bg_rect.y))
                else:
                    # custom: blue text (for ERRO)
                    warn_render = self.font.render(warn_text, True, (0,70,220))
                    surf.blit(aviso_label_render, (self.panel_rect.x + aviso_pad, self.panel_rect.bottom - aviso_label_render.get_height()*(len(warnings_to_show)-idx) - pad))
                    surf.blit(warn_render, (self.panel_rect.x + aviso_pad + aviso_label_render.get_width(), self.panel_rect.bottom - warn_render.get_height()*(len(warnings_to_show)-idx) - pad))
        else:
            # Default: draw title and options horizontally
            t = self.font.render(title, True, (0, 0, 0))
            surf.blit(t, (self.panel_rect.x + 8, self.panel_rect.y + 8))
            oy = self.panel_rect.y + 8 + t.get_height() + 8
            x = self.panel_rect.x + 8
            pad_x = 12
            for idx, (label, _) in enumerate(self._opts()):
                txt_color = (255, 255, 255) if idx == self.selected else (0, 70, 220)
                bg_color = (0, 70, 220) if idx == self.selected else None
                txt = self.font.render(label, True, txt_color)
                item_w = txt.get_width() + 12
                if bg_color:
                    pygame.draw.rect(surf, bg_color, (x - 6, oy - 2, item_w + 6, self.font.get_height() + 4))
                    surf.blit(txt, (x + 6, oy))
                else:
                    surf.blit(txt, (x + 6, oy))
                x += item_w + pad_x

    # compatibility wrappers
    def process_key_event(self, key):
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

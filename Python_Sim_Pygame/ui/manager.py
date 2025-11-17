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
        # By default screens are navigable by left/right. Pass title=='Menu_01' or
        # options with a special marker to make non-navigable screens.
        self.screens.append({'title': title, 'options': list(options), 'navigable': True})

    def next_screen(self):
        if not self.screens:
            return
        # advance to next navigable screen
        n = len(self.screens)
        if n == 0:
            return
        i = self.current
        for _ in range(n):
            i = (i + 1) % n
            if self.screens[i].get('navigable', True):
                self.current = i
                self.selected = 0
                return

    def prev_screen(self):
        if not self.screens:
            return
        n = len(self.screens)
        if n == 0:
            return
        i = self.current
        for _ in range(n):
            i = (i - 1) % n
            if self.screens[i].get('navigable', True):
                self.current = i
                self.selected = 0
                return

    def select_next(self):
        # Custom handling for Main screen interactive items (Menu + ERRO if exists)
        try:
            title = self.screens[self.current].get('title', '')
        except Exception:
            title = ''
        if title == 'Main':
            error_present = False
            try:
                if self.player and hasattr(self.player, 'lights') and len(self.player.lights) > 0 and self.player.lights[0]:
                    error_present = True
            except Exception:
                error_present = False
            max_index = 1 if error_present else 0  # 0=Menu, 1=ERRO
            self.selected = (self.selected + 1) % (max_index + 1)
            return
        opts = self._opts()
        if not opts:
            return
        self.selected = min(self.selected + 1, len(opts) - 1)

    def select_prev(self):
        try:
            title = self.screens[self.current].get('title', '')
        except Exception:
            title = ''
        if title == 'Main':
            error_present = False
            try:
                if self.player and hasattr(self.player, 'lights') and len(self.player.lights) > 0 and self.player.lights[0]:
                    error_present = True
            except Exception:
                error_present = False
            max_index = 1 if error_present else 0
            self.selected = (self.selected - 1) % (max_index + 1)
            return
        opts = self._opts()
        if not opts:
            return
        self.selected = max(self.selected - 1, 0)

    def activate(self):
        opts = self._opts()
        if not opts:
            return
        # Special-case: if we're on Main and selected==0 (Menu), go to Menu_01 screen
        try:
            current_title = self.screens[self.current].get('title', '')
        except Exception:
            current_title = ''
        if current_title == 'Main' and self.selected == 0:
            # try to find Menu_01 screen and switch to it
            for i, s in enumerate(self.screens):
                if s.get('title') == 'Menu_01':
                    self.current = i
                    self.selected = 0
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

            # Build warnings BEFORE drawing selectable ERRO so we can know if exists
            warnings_to_show = []
            if self.player:
                try:
                    if hasattr(self.player, 'lights') and len(self.player.lights) > 0 and self.player.lights[0]:
                        warnings_to_show.append(('ERRO', 'red'))
                except Exception:
                    pass
                if hasattr(self.player, 'battery_level'):
                    try:
                        if float(self.player.battery_level) < 0.2:
                            warnings_to_show.append(('BATERIA', 'battery'))
                    except Exception:
                        pass
            if warning:
                warnings_to_show = [(warning, 'custom')]
            # Bottom row: right side selectable 'Menu' and arrow
            menu_str = 'Menu'
            menu_selected = (self.selected == 0)
            menu_render = self.font.render(menu_str, True, (255,255,255) if menu_selected else (0,70,220))
            menu_bg_rect = menu_render.get_rect()
            menu_bg_rect.x = self.panel_rect.right - menu_render.get_width() - 24 - pad
            menu_bg_rect.y = self.panel_rect.bottom - menu_render.get_height() - pad
            menu_bg_rect.width += 8
            menu_bg_rect.height += 2
            if menu_selected:
                pygame.draw.rect(surf, (0,70,220), menu_bg_rect)
            surf.blit(menu_render, (menu_bg_rect.x + 4, menu_bg_rect.y))
            # Arrow
            arrow_str = '\u2192'  # Unicode right arrow
            try:
                arrow_render = self.font.render(arrow_str, True, (255,255,255) if menu_selected else (0,70,220))
                if arrow_render.get_width() < 10:
                    raise Exception('Arrow too small')
                use_arrow_img = True
            except Exception:
                use_arrow_img = False
            ax = menu_bg_rect.x + menu_render.get_width() + 14
            ay = menu_bg_rect.y + menu_render.get_height()//2
            if use_arrow_img:
                surf.blit(arrow_render, (menu_bg_rect.x + menu_render.get_width() + 8, menu_bg_rect.y))
            else:
                arrow_color = (255,255,255) if menu_selected else (0,70,220)
                pygame.draw.polygon(surf, arrow_color, [
                    (ax, ay-6), (ax+10, ay), (ax, ay+6)
                ])

            # Draw warnings (ERRO selectable if present)
            aviso_pad = pad
            for idx, (warn_text, warn_type) in enumerate(warnings_to_show):
                aviso_label = 'Aviso: '
                aviso_label_render = self.font.render(aviso_label, True, (0,70,220))
                is_erro = (warn_text == 'ERRO')
                erro_selected = (self.selected == 1 and is_erro)
                if warn_type == 'battery':
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
                    # ERRO or custom
                    warn_color = (255,255,255) if erro_selected else (0,70,220)
                    warn_render = self.font.render(warn_text, True, warn_color)
                    y_pos_label = self.panel_rect.bottom - aviso_label_render.get_height()*(len(warnings_to_show)-idx) - pad
                    x_base = self.panel_rect.x + aviso_pad
                    if erro_selected:
                        # background for ERRO selection
                        bg_rect = warn_render.get_rect()
                        bg_rect.x = x_base + aviso_label_render.get_width()
                        bg_rect.y = y_pos_label
                        bg_rect.width += 8
                        bg_rect.height += 2
                        pygame.draw.rect(surf, (0,70,220), bg_rect)
                        surf.blit(aviso_label_render, (x_base, y_pos_label))
                        surf.blit(warn_render, (bg_rect.x + 4, bg_rect.y))
                    else:
                        surf.blit(aviso_label_render, (x_base, y_pos_label))
                        surf.blit(warn_render, (x_base + aviso_label_render.get_width(), y_pos_label))
        elif title == 'Menu_01':
            # Render a centered title 'MENU' at the top of the panel
            title_text = 'MENU'
            # slightly larger font for the menu header
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 8
            surf.blit(header_render, (hx, hy))
            # draw options (if any) below
            oy = hy + header_render.get_height() + 8
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
            return
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
        # Only Tab cycles screens; arrow keys do not change screens here
        if key == pygame.K_TAB:
            self.next_screen()
        elif key == pygame.K_UP:
            self.select_prev()
        elif key == pygame.K_DOWN:
            self.select_next()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.activate()

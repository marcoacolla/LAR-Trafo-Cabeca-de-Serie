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
        # history stack of previously visited screen indices (for back navigation)
        self.history = []
        self.player = player
        # sensor mock values (displayed on Sensores screen)
        self.sensor_altura = 12
        self.inclin_x = 13
        self.inclin_y = 14
        if panel_rect is None:
            sw, sh = screen.get_width(), screen.get_height()
            self.panel_rect = pygame.Rect(8, 100, 260, 70)
            print(f"[UIManager] Panel position: {self.panel_rect}")
        else:
            self.panel_rect = pygame.Rect(panel_rect)
        # second-page sensor vars
        self.anq_est = 7
        self.velocidade = 0.5

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
                    # push current screen onto history so we can return to it
                    try:
                        self.history.append(self.current)
                    except Exception:
                        pass
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
            # Draw background only for menu text, not for the arrow
            if menu_selected:
                bg_rect = pygame.Rect(menu_bg_rect.x, menu_bg_rect.y, menu_bg_rect.width, menu_bg_rect.height)
                pygame.draw.rect(surf, (0,70,220), bg_rect)
            surf.blit(menu_render, (menu_bg_rect.x + 4, menu_bg_rect.y))
            # Arrow (draw a clear triangular button to the right of Menu)
            try:
                # build a rectangular area for the arrow button
                arrow_w = 18
                arrow_h = max(menu_bg_rect.height, 18)
                arrow_x = menu_bg_rect.right + 6
                arrow_y = menu_bg_rect.y + (menu_bg_rect.height - arrow_h) // 2
                arrow_rect = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                # arrow has a fixed white background and blue triangle (do not invert with selection)
                pygame.draw.rect(surf, (255,255,255), arrow_rect)
                tri_color = (0,70,220)
                # draw right-pointing triangle centered in arrow_rect
                cx = arrow_rect.x + arrow_rect.width // 2
                cy = arrow_rect.y + arrow_rect.height // 2
                pts = [(cx-4, cy-6), (cx+6, cy), (cx-4, cy+6)]
                pygame.draw.polygon(surf, tri_color, pts)
                # store click rect (slightly larger for easier clicking)
                try:
                    self._menu_arrow_rect = arrow_rect.inflate(6, 6)
                except Exception:
                    self._menu_arrow_rect = arrow_rect
            except Exception:
                self._menu_arrow_rect = None

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
            # Render header title (keep title at top)
            title_text = 'MENU'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # draw a back-arrow button at the top-left of the panel to indicate "volta"
            try:
                # button rectangle for the back arrow
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                # background: white
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                # left-pointing triangle inside the button
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                # store a slightly larger rect for easier clicking
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # Custom Menu_01 layout: top option (index 0) then two bottom options side-by-side.
            opts = self._opts()
            pad = 8
            # top button area, placed below header
            top_y = hy + header_render.get_height() + 6
            top_h = self.font.get_height() + 8
            if len(opts) > 0:
                label0 = opts[0][0]
                selected0 = (self.selected == 0)
                txt0 = self.font.render(label0, True, (255,255,255) if selected0 else (0,70,220))
                txt_w0 = txt0.get_width()
                btn_w = min(self.panel_rect.width - 24, txt_w0 + 24)
                btn_x = self.panel_rect.x + (self.panel_rect.width - btn_w) // 2
                btn_y = top_y
                # Draw white background for unselected, blue for selected
                if selected0:
                    pygame.draw.rect(surf, (0,70,220), (btn_x, btn_y, btn_w, top_h + 4))
                else:
                    pygame.draw.rect(surf, (255,255,255), (btn_x, btn_y, btn_w, top_h + 4))
                surf.blit(txt0, (btn_x + (btn_w - txt_w0)//2, btn_y + 4))

            # bottom row options
            bottom_opts = opts[1:]
            if bottom_opts:
                gap = 12
                texts = [self.font.render(o[0], True, (0,70,220)) for o in bottom_opts]
                txt_widths = [t.get_width() for t in texts]
                total_text_w = sum(txt_widths)
                btn_w_available = self.panel_rect.width - 24 - gap * (len(bottom_opts)-1)
                btn_ws = []
                for w in txt_widths:
                    allocated = max(w + 16, int(btn_w_available * (w / total_text_w)) if total_text_w > 0 else btn_w_available // len(bottom_opts))
                    btn_ws.append(allocated)
                total_btns_w = sum(btn_ws) + gap * (len(bottom_opts)-1)
                start_x = self.panel_rect.x + (self.panel_rect.width - total_btns_w)//2
                oy = self.panel_rect.bottom - (self.font.get_height() + 12)
                x = start_x
                for i, (label, _) in enumerate(bottom_opts, start=1):
                    sel = (self.selected == i)
                    w = btn_ws[i-1]
                    h = self.font.get_height() + 8
                    # white background and blue text when unselected; blue bg and white text when selected
                    if sel:
                        pygame.draw.rect(surf, (0,70,220), (x, oy, w, h))
                        txt = self.font.render(label, True, (255,255,255))
                    else:
                        pygame.draw.rect(surf, (255,255,255), (x, oy, w, h))
                        txt = self.font.render(label, True, (0,70,220))
                    surf.blit(txt, (x + (w - txt.get_width())//2, oy + 4))
                    x += w + gap
            return
        elif title == 'FS_MENU':
            # FS_MENU: Title 'Funções' and two stacked options (Funções Basicas, Funções Avançadas)
            title_text = 'Funções'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left (same place as Menu_01)
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # draw stacked options centered below header
            opts = self._opts()
            start_y = hy + header_render.get_height() + 8
            spacing = self.font.get_height() + 10
            for idx, (label, _) in enumerate(opts):
                sel = (self.selected == idx)
                txt = self.font.render(label, True, (255,255,255) if sel else (0,70,220))
                w = txt.get_width() + 20
                h = self.font.get_height() + 8
                x = self.panel_rect.x + (self.panel_rect.width - w)//2
                y = start_y + idx * spacing
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, y, w, h))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, y, w, h))
                surf.blit(txt, (x + (w - txt.get_width())//2, y + 4))
            return
        elif title == 'FS_ADVANCED':
            # FS_ADVANCED: Title 'Funções Avançadas' and two stacked options
            title_text = 'Funções Avançadas'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left (same as other submenus)
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # draw stacked options centered below header
            opts = self._opts()
            start_y = hy + header_render.get_height() + 8
            spacing = self.font.get_height() + 10
            rects = []
            for idx, (label, _) in enumerate(opts):
                sel = (self.selected == idx)
                txt = self.font.render(label, True, (255,255,255) if sel else (0,70,220))
                w = txt.get_width() + 20
                h = self.font.get_height() + 8
                x = self.panel_rect.x + (self.panel_rect.width - w)//2
                y = start_y + idx * spacing
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, y, w, h))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, y, w, h))
                surf.blit(txt, (x + (w - txt.get_width())//2, y + 4))
                rects.append(pygame.Rect(x, y, w, h))
            try:
                self._fs_adv_option_rects = rects
            except Exception:
                self._fs_adv_option_rects = None
            return
        elif title == 'FS_OPMODE':
            # FS_OPMODE: Title 'Modo operação' and two stacked options: Malha aberta / Malha fechada
            title_text = 'Modo operação'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # draw stacked options centered below header
            opts = self._opts()
            start_y = hy + header_render.get_height() + 8
            spacing = self.font.get_height() + 10
            rects = []
            for idx, (label, _) in enumerate(opts):
                sel = (self.selected == idx)
                txt = self.font.render(label, True, (255,255,255) if sel else (0,70,220))
                w = txt.get_width() + 20
                h = self.font.get_height() + 8
                x = self.panel_rect.x + (self.panel_rect.width - w)//2
                y = start_y + idx * spacing
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, y, w, h))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, y, w, h))
                surf.blit(txt, (x + (w - txt.get_width())//2, y + 4))
                rects.append(pygame.Rect(x, y, w, h))
            try:
                self._fs_opmode_option_rects = rects
            except Exception:
                self._fs_opmode_option_rects = None
            return
        elif title == 'FS_LIGHTS':
            # FS_LIGHTS: Title 'Luz sinalizadora' and two side-by-side options Habilitar/Desabilitar
            title_text = 'Luz sinalizadora'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # two side-by-side options centered
            opts = self._opts()
            opt_labels = [o[0] for o in opts[:2]]
            gap = 16
            texts = [self.font.render(l, True, (0,70,220)) for l in opt_labels]
            txt_widths = [t.get_width() for t in texts]
            btn_ws = [w + 24 for w in txt_widths]
            total_w = sum(btn_ws) + gap * (len(btn_ws)-1)
            start_x = self.panel_rect.x + (self.panel_rect.width - total_w)//2
            oy = hy + header_render.get_height() + 12
            x = start_x
            rects = []
            for i, label in enumerate(opt_labels):
                sel = (self.selected == i)
                w = btn_ws[i]
                h = self.font.get_height() + 8
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, oy, w, h))
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, oy, w, h))
                    txt = self.font.render(label, True, (0,70,220))
                surf.blit(txt, (x + (w - txt.get_width())//2, oy + 4))
                rects.append(pygame.Rect(x, oy, w, h))
                x += w + gap
            try:
                self._fs_lights_option_rects = rects
            except Exception:
                self._fs_lights_option_rects = None
            return
        elif title == 'Sensores':
            # Sensores screen: title and arrows both sides, two layers of info
            title_text = 'Sensores'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # left back arrow
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            # right arrow (placeholder action)
            try:
                tr_w = 20
                tr_h = max(header_render.get_height(), 18)
                tr_x = self.panel_rect.right - tr_w - 8
                tr_y = hy + (header_render.get_height() - tr_h) // 2
                tr_btn = pygame.Rect(tr_x, tr_y, tr_w, tr_h)
                pygame.draw.rect(surf, (255,255,255), tr_btn)
                cx = tr_btn.x + tr_btn.width // 2
                cy = tr_btn.y + tr_btn.height // 2
                pts = [(cx-6, cy-6), (cx+6, cy), (cx-6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._sensores_topright_rect = tr_btn.inflate(6, 6)
            except Exception:
                self._sensores_topright_rect = None
            surf.blit(header_render, (hx, hy))

            # hint arrow: right arrow key should go to second sensores page
            hint = self.font.render('→', True, (0,70,220))
            try:
                surf.blit(hint, (self.panel_rect.right - 26, hy))
            except Exception:
                pass

            # First layer: Altura
            try:
                altura_label = f'Altura: {int(self.sensor_altura)} cm'
            except Exception:
                altura_label = f'Altura: {self.sensor_altura} cm'
            txt0 = self.font.render(altura_label, True, (0,70,220))
            content_w = self.panel_rect.width - 24
            h0 = self.font.get_height() + 8
            x0 = self.panel_rect.x + 12
            y0 = hy + header_render.get_height() + 8
            pygame.draw.rect(surf, (255,255,255), (x0, y0, content_w, h0))
            surf.blit(txt0, (x0 + 8, y0 + 4))

            # Second layer: Inclin X / Y
            inclin_label = f'Inclin: X: {int(self.inclin_x)}     Y: {int(self.inclin_y)}'
            txt1 = self.font.render(inclin_label, True, (0,70,220))
            content_w = self.panel_rect.width - 24
            h1 = self.font.get_height() + 8
            x1 = self.panel_rect.x + 12
            y1 = y0 + h0 + 8
            pygame.draw.rect(surf, (255,255,255), (x1, y1, content_w, h1))
            surf.blit(txt1, (x1 + 8, y1 + 4))
            return
        elif title == 'Sensores_2':
            # Second Sensores page: same header, show Anq. esterçamento and Velocidade
            title_text = 'Sensores'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # Anq. esterçamento
            try:
                anq_label = f'Anq. esterçamento: {int(self.anq_est)}'
            except Exception:
                anq_label = f'Anq. esterçamento: {self.anq_est}'
            txt0 = self.font.render(anq_label, True, (0,70,220))
            content_w = self.panel_rect.width - 24
            h0 = self.font.get_height() + 8
            x0 = self.panel_rect.x + 12
            y0 = hy + header_render.get_height() + 8
            pygame.draw.rect(surf, (255,255,255), (x0, y0, content_w, h0))
            surf.blit(txt0, (x0 + 8, y0 + 4))

            # Velocidade
            try:
                vel_label = f'Velocidade : {float(self.velocidade):.2f} m/s'
            except Exception:
                vel_label = f'Velocidade : {self.velocidade} m/s'
            txt1 = self.font.render(vel_label, True, (0,70,220))
            h1 = self.font.get_height() + 8
            x1 = self.panel_rect.x + 12
            y1 = y0 + h0 + 8
            pygame.draw.rect(surf, (255,255,255), (x1, y1, content_w, h1))
            surf.blit(txt1, (x1 + 8, y1 + 4))
            return
        elif title == 'FS_BASIC':
            # FS_BASIC: Title 'Funções Básicas' and two side-by-side centered options
            title_text = 'Funções Básicas'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left (same place as other submenus)
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # two side-by-side options centered
            opts = self._opts()
            # Render only first two options if present
            opt_labels = [o[0] for o in opts[:2]]
            gap = 16
            texts = [self.font.render(l, True, (0,70,220)) for l in opt_labels]
            txt_widths = [t.get_width() for t in texts]
            btn_ws = [w + 24 for w in txt_widths]
            total_w = sum(btn_ws) + gap * (len(btn_ws)-1)
            start_x = self.panel_rect.x + (self.panel_rect.width - total_w)//2
            oy = hy + header_render.get_height() + 12
            x = start_x
            rects = []
            for i, label in enumerate(opt_labels):
                sel = (self.selected == i)
                w = btn_ws[i]
                h = self.font.get_height() + 8
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, oy, w, h))
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, oy, w, h))
                    txt = self.font.render(label, True, (0,70,220))
                surf.blit(txt, (x + (w - txt.get_width())//2, oy + 4))
                rects.append(pygame.Rect(x, oy, w, h))
                x += w + gap
            # store rects for click handling
            try:
                self._fs_basic_option_rects = rects
            except Exception:
                self._fs_basic_option_rects = None
            # Draw a top-right arrow button (white bg + blue right-pointing triangle)
            try:
                tr_w = 20
                tr_h = max(header_render.get_height(), 18)
                tr_x = self.panel_rect.right - tr_w - 8
                tr_y = hy + (header_render.get_height() - tr_h) // 2
                tr_btn = pygame.Rect(tr_x, tr_y, tr_w, tr_h)
                pygame.draw.rect(surf, (255,255,255), tr_btn)
                cx = tr_btn.x + tr_btn.width // 2
                cy = tr_btn.y + tr_btn.height // 2
                # right-pointing triangle
                pts = [(cx-6, cy-6), (cx+6, cy), (cx-6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._fs_basic_topright_rect = tr_btn.inflate(6, 6)
            except Exception:
                self._fs_basic_topright_rect = None
            return
        elif title == 'FS_AUTONIVEL':
            # Autonivelamento screen with two side-by-side options: Habilitar / Desabilitar
            title_text = 'Autonivelamento'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # two side-by-side options centered
            opts = self._opts()
            opt_labels = [o[0] for o in opts[:2]]
            gap = 16
            texts = [self.font.render(l, True, (0,70,220)) for l in opt_labels]
            txt_widths = [t.get_width() for t in texts]
            btn_ws = [w + 24 for w in txt_widths]
            total_w = sum(btn_ws) + gap * (len(btn_ws)-1)
            start_x = self.panel_rect.x + (self.panel_rect.width - total_w)//2
            oy = hy + header_render.get_height() + 12
            x = start_x
            rects = []
            for i, label in enumerate(opt_labels):
                sel = (self.selected == i)
                w = btn_ws[i]
                h = self.font.get_height() + 8
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, oy, w, h))
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, oy, w, h))
                    txt = self.font.render(label, True, (0,70,220))
                surf.blit(txt, (x + (w - txt.get_width())//2, oy + 4))
                rects.append(pygame.Rect(x, oy, w, h))
                x += w + gap
            try:
                self._fs_autonivel_option_rects = rects
            except Exception:
                self._fs_autonivel_option_rects = None
            return
        elif title == 'FS_FREIO':
            # Freio screen with two side-by-side options: Habilitar / Desabilitar
            title_text = 'Freio'
            try:
                header_font = pygame.font.SysFont(None, int(self.font.get_height() * 1.2))
            except Exception:
                header_font = self.font
            header_render = header_font.render(title_text, True, (0,70,220))
            hx = self.panel_rect.x + (self.panel_rect.width - header_render.get_width()) // 2
            hy = self.panel_rect.y + 6
            # back arrow at top-left
            try:
                arrow_w = 20
                arrow_h = max(header_render.get_height(), 18)
                arrow_x = self.panel_rect.x + 8
                arrow_y = hy + (header_render.get_height() - arrow_h) // 2
                arrow_btn = pygame.Rect(arrow_x, arrow_y, arrow_w, arrow_h)
                pygame.draw.rect(surf, (255,255,255), arrow_btn)
                cx = arrow_btn.x + arrow_btn.width // 2
                cy = arrow_btn.y + arrow_btn.height // 2
                pts = [(cx+6, cy-6), (cx-6, cy), (cx+6, cy+6)]
                pygame.draw.polygon(surf, (0,70,220), pts)
                self._back_arrow_rect = arrow_btn.inflate(6, 6)
            except Exception:
                self._back_arrow_rect = None
            surf.blit(header_render, (hx, hy))

            # two side-by-side options centered
            opts = self._opts()
            opt_labels = [o[0] for o in opts[:2]]
            gap = 16
            texts = [self.font.render(l, True, (0,70,220)) for l in opt_labels]
            txt_widths = [t.get_width() for t in texts]
            btn_ws = [w + 24 for w in txt_widths]
            total_w = sum(btn_ws) + gap * (len(btn_ws)-1)
            start_x = self.panel_rect.x + (self.panel_rect.width - total_w)//2
            oy = hy + header_render.get_height() + 12
            x = start_x
            rects = []
            for i, label in enumerate(opt_labels):
                sel = (self.selected == i)
                w = btn_ws[i]
                h = self.font.get_height() + 8
                if sel:
                    pygame.draw.rect(surf, (0,70,220), (x, oy, w, h))
                    txt = self.font.render(label, True, (255,255,255))
                else:
                    pygame.draw.rect(surf, (255,255,255), (x, oy, w, h))
                    txt = self.font.render(label, True, (0,70,220))
                surf.blit(txt, (x + (w - txt.get_width())//2, oy + 4))
                rects.append(pygame.Rect(x, oy, w, h))
                x += w + gap
            try:
                self._fs_freio_option_rects = rects
            except Exception:
                self._fs_freio_option_rects = None
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
        elif key == pygame.K_LEFT:
            # left arrow should go back to the previous screen in history
            self.go_back()
        elif key == pygame.K_RIGHT:
            # If on Sensores, treat right arrow as 'next sensores page' (Sensores_2)
            try:
                title = self.screens[self.current].get('title', '')
            except Exception:
                title = ''
            if title == 'Sensores':
                try:
                    for i, s in enumerate(self.screens):
                        if s.get('title') == 'Sensores_2':
                            try:
                                self.history.append(self.current)
                            except Exception:
                                pass
                            self.current = i
                            self.selected = 0
                            return
                except Exception:
                    pass
        elif key == pygame.K_UP:
            self.select_prev()
        elif key == pygame.K_DOWN:
            self.select_next()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.activate()

    def process_mouse_event(self, event):
        # handle mouse clicks for UI panel interactive elements
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # prioritize back-arrow (Menu_01/other submenus)
                title = self.screens[self.current].get('title', '') if self.screens else ''
                if title in ('Menu_01', 'FS_MENU', 'Sensores') and getattr(self, '_back_arrow_rect', None) and self._back_arrow_rect.collidepoint(pos):
                    # clicked back arrow on a submenu: go back in history
                    try:
                        self.go_back()
                    except Exception:
                        self.prev_screen()
                    return True
                # if on Main, clicking the right-arrow should open the Menu (activate)
                if title == 'Main' and getattr(self, '_menu_arrow_rect', None) and self._menu_arrow_rect.collidepoint(pos):
                    try:
                        # ensure Menu is selected and activate
                        self.selected = 0
                        self.activate()
                    except Exception:
                        pass
                    return True
                # FS_BASIC: option click handling
                if title == 'FS_BASIC' and getattr(self, '_fs_basic_option_rects', None):
                    for idx, r in enumerate(self._fs_basic_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # top-right arrow on FS_BASIC
                if title == 'FS_BASIC' and getattr(self, '_fs_basic_topright_rect', None) and self._fs_basic_topright_rect.collidepoint(pos):
                    try:
                        print('FS_BASIC: top-right arrow clicked')
                        # placeholder action: no-op or extendable
                    except Exception:
                        pass
                    return True
                # FS_AUTONIVEL option clicks
                if title == 'FS_AUTONIVEL' and getattr(self, '_fs_autonivel_option_rects', None):
                    for idx, r in enumerate(self._fs_autonivel_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # FS_FREIO option clicks
                if title == 'FS_FREIO' and getattr(self, '_fs_freio_option_rects', None):
                    for idx, r in enumerate(self._fs_freio_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # FS_ADVANCED option clicks
                if title == 'FS_ADVANCED' and getattr(self, '_fs_adv_option_rects', None):
                    for idx, r in enumerate(self._fs_adv_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # FS_OPMODE option clicks
                if title == 'FS_OPMODE' and getattr(self, '_fs_opmode_option_rects', None):
                    for idx, r in enumerate(self._fs_opmode_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # FS_LIGHTS option clicks
                if title == 'FS_LIGHTS' and getattr(self, '_fs_lights_option_rects', None):
                    for idx, r in enumerate(self._fs_lights_option_rects):
                        if r.collidepoint(pos):
                            try:
                                self.selected = idx
                                self.activate()
                            except Exception:
                                pass
                            return True
                # Sensores top-right arrow click
                if title == 'Sensores' and getattr(self, '_sensores_topright_rect', None) and self._sensores_topright_rect.collidepoint(pos):
                    try:
                        # navigate to Sensores_2 screen if present
                        for i, s in enumerate(self.screens):
                            if s.get('title') == 'Sensores_2':
                                try:
                                    self.history.append(self.current)
                                except Exception:
                                    pass
                                self.current = i
                                self.selected = 0
                                break
                    except Exception:
                        pass
                    return True
        except Exception:
            pass
        return False

    def go_back(self):
        """Navigate back to the last screen in history if available; otherwise fall back to prev_screen()."""
        try:
            if getattr(self, 'history', None) and len(self.history) > 0:
                prev = self.history.pop()
                # sanity check index
                if 0 <= prev < len(self.screens):
                    self.current = prev
                    self.selected = 0
                    return True
        except Exception:
            pass
        # fallback
        try:
            self.prev_screen()
        except Exception:
            pass
        return False

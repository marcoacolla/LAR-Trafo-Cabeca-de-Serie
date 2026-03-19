# -------------------------
# SidePanel: minimal, customizable right-side UI (module-level)
# -------------------------
import pygame

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

        # place content box near bottom-right inside the side panel
        surf_w, surf_h = surf.get_width(), surf.get_height()
        # raise a bit (20px) and move to the right inside the reserved side panel
        x = max(8, self.rect.right - content_w - 12)
        y = max(8, surf_h - content_h - 68)
        content_rect = pygame.Rect(x, y, content_w, content_h)
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

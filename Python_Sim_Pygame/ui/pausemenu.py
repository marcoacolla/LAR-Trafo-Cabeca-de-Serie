# -------------------------
# PauseMenu: Menu de pausa com opções de configuração
# -------------------------
import pygame


class PauseMenu:
    def __init__(self, font=None, callbacks=None):
        self.font = font or pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.is_open = False
        self.selected_option = 0
        self.current_menu = 'main'  # 'main' ou 'settings'
        self.editing_option = None
        
        # Callbacks para funções globais
        self.callbacks = callbacks or {}
        self.get_value_fn = self.callbacks.get('get_value')
        self.toggle_fn = self.callbacks.get('toggle')
        self.get_global_fn = self.callbacks.get('get_global')
        self.set_global_fn = self.callbacks.get('set_global')
        
        # Opções do menu principal
        self.main_options = [
            ('Continuar', 'continue'),
            ('Configurações', 'settings'),
            ('Voltar ao Menu', 'exit_menu'),
            ('Sair', 'exit_game'),
        ]
        
        # Configurações relevantes durante a simulação
        self.settings = []
        self._main_option_rects = []
        self._settings_option_rects = []
    
    def update_settings_references(self):
        """Atualiza as opções de configuração disponíveis no menu de pausa."""
        self.settings = [
            ('Tela Cheia', 'fullscreen'),
            ('Modo Hardcore', 'hardcore'),
            ('Joystick Leading', 'joystick_leading'),
        ]

    def _get_setting_value(self, key):
        try:
            if self.get_value_fn and callable(self.get_value_fn):
                return bool(self.get_value_fn(key))
            
            # Fallback para usar get_global_fn
            if key == 'fullscreen':
                return bool(self.get_global_fn('is_fullscreen') if self.get_global_fn else False)
            if key == 'hardcore':
                return bool(self.get_global_fn('hardcore_mode') if self.get_global_fn else False)
            if key == 'joystick_leading':
                return bool(self.get_global_fn('joystick_leading') if self.get_global_fn else True)
        except Exception:
            pass
        return False

    def _toggle_setting(self, key):
        try:
            if key == 'fullscreen':
                if self.toggle_fn and callable(self.toggle_fn):
                    self.toggle_fn('fullscreen')
            elif key == 'hardcore':
                if self.set_global_fn and callable(self.set_global_fn):
                    current = self.get_global_fn('hardcore_mode') if self.get_global_fn else False
                    self.set_global_fn('hardcore_mode', not bool(current))
            elif key == 'joystick_leading':
                if self.set_global_fn and callable(self.set_global_fn):
                    current = self.get_global_fn('joystick_leading') if self.get_global_fn else True
                    self.set_global_fn('joystick_leading', not bool(current))
                    try:
                        joystick_available = self.get_global_fn('joystick_available') if self.get_global_fn else False
                        new_mode = 'joystick' if (not bool(current)) and joystick_available else 'keyboard'
                        self.set_global_fn('control_mode', new_mode)
                    except Exception:
                        pass
        except Exception:
            pass
    
    def open(self):
        self.is_open = True
        self.selected_option = 0
        self.current_menu = 'main'
        self.editing_option = None
    
    def close(self):
        self.is_open = False
    
    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()
    
    def handle_input(self, keys, prev_keys):
        """Processa entrada do teclado"""
        if not self.is_open:
            return None
        
        # Detecta pressionamento de teclas (edge detection)
        if self.current_menu == 'main':
            if keys[pygame.K_UP] and not prev_keys[pygame.K_UP]:
                self.selected_option = (self.selected_option - 1) % len(self.main_options)
            elif keys[pygame.K_DOWN] and not prev_keys[pygame.K_DOWN]:
                self.selected_option = (self.selected_option + 1) % len(self.main_options)
            elif keys[pygame.K_RETURN] and not prev_keys[pygame.K_RETURN]:
                action = self.main_options[self.selected_option][1]
                if action == 'continue':
                    self.close()
                    return 'continue'
                elif action == 'settings':
                    self.current_menu = 'settings'
                    self.selected_option = 0
                    self.editing_option = None
                elif action == 'exit_menu':
                    return 'exit_menu'
                elif action == 'exit_game':
                    return 'exit_game'
        
        elif self.current_menu == 'settings':
            if keys[pygame.K_ESCAPE] and not prev_keys[pygame.K_ESCAPE]:
                self.current_menu = 'main'
                self.selected_option = 0
                self.editing_option = None
            else:
                if keys[pygame.K_UP] and not prev_keys[pygame.K_UP]:
                    self.selected_option = (self.selected_option - 1) % len(self.settings)
                elif keys[pygame.K_DOWN] and not prev_keys[pygame.K_DOWN]:
                    self.selected_option = (self.selected_option + 1) % len(self.settings)
                elif ((keys[pygame.K_RETURN] and not prev_keys[pygame.K_RETURN]) or
                      (keys[pygame.K_LEFT] and not prev_keys[pygame.K_LEFT]) or
                      (keys[pygame.K_RIGHT] and not prev_keys[pygame.K_RIGHT])):
                    _, setting_key = self.settings[self.selected_option]
                    self._toggle_setting(setting_key)
        
        return None

    def handle_mouse_event(self, event):
        """Processa clique do mouse. Retorna (handled, action)."""
        if not self.is_open:
            return False, None
        try:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                return False, None
            pos = event.pos

            if self.current_menu == 'main':
                for idx, rect in enumerate(getattr(self, '_main_option_rects', [])):
                    if rect.collidepoint(pos):
                        self.selected_option = idx
                        action = self.main_options[idx][1]
                        if action == 'continue':
                            self.close()
                            return True, 'continue'
                        if action == 'settings':
                            self.current_menu = 'settings'
                            self.selected_option = 0
                            self.editing_option = None
                            return True, None
                        if action == 'exit_menu':
                            return True, 'exit_menu'
                        if action == 'exit_game':
                            return True, 'exit_game'
                        return True, None

            elif self.current_menu == 'settings':
                for idx, rect in enumerate(getattr(self, '_settings_option_rects', [])):
                    if rect.collidepoint(pos):
                        self.selected_option = idx
                        _, setting_key = self.settings[idx]
                        self._toggle_setting(setting_key)
                        return True, None
        except Exception:
            return False, None

        return False, None
    
    def draw(self, surface):
        """Desenha o menu de pausa"""
        if not self.is_open:
            return
        
        # Desenha fundo semi-transparente
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Dimensões do menu
        menu_width = 400
        menu_height = 300 if self.current_menu == 'main' else 260
        menu_x = (surface.get_width() - menu_width) // 2
        menu_y = (surface.get_height() - menu_height) // 2
        
        # Desenha caixa do menu
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, (40, 40, 40), menu_rect)
        pygame.draw.rect(surface, (255, 255, 255), menu_rect, 3)
        
        # Título
        if self.current_menu == 'main':
            title = self.font.render('PAUSA', True, (255, 255, 255))
            title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 20))
            surface.blit(title, title_rect)
            
            # Opções do menu principal
            self._main_option_rects = []
            option_y = menu_y + 70
            for idx, (label, _) in enumerate(self.main_options):
                option_rect = pygame.Rect(menu_x + 10, option_y - 5, menu_width - 20, 30)
                self._main_option_rects.append(option_rect)
                if idx == self.selected_option:
                    pygame.draw.rect(surface, (100, 150, 255), option_rect)
                    txt = self.font.render(label, True, (255, 255, 255))
                else:
                    txt = self.font.render(label, True, (200, 200, 200))
                surface.blit(txt, (menu_x + 30, option_y))
                option_y += 50
            
            # Instrução
            hint = self.small_font.render('ENTER: Selecionar | ESC: Continuar', True, (150, 150, 150))
            surface.blit(hint, (menu_x + 10, menu_y + menu_height - 30))
        
        elif self.current_menu == 'settings':
            title = self.font.render('CONFIGURAÇÕES', True, (255, 255, 255))
            title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 15))
            surface.blit(title, title_rect)
            
            # Configurações
            self._settings_option_rects = []
            option_y = menu_y + 55
            for idx, (label, setting_key) in enumerate(self.settings):
                current_val = self._get_setting_value(setting_key)
                value_text = 'ON' if current_val else 'OFF'
                option_rect = pygame.Rect(menu_x + 10, option_y - 3, menu_width - 20, 28)
                self._settings_option_rects.append(option_rect)
                
                if idx == self.selected_option:
                    pygame.draw.rect(surface, (100, 150, 255), option_rect)
                    txt = self.small_font.render(f'{label}: {value_text}', True, (255, 255, 255))
                else:
                    txt = self.small_font.render(f'{label}: {value_text}', True, (200, 200, 200))
                
                surface.blit(txt, (menu_x + 20, option_y))
                option_y += 40
            
            # Instruções
            hint = self.small_font.render('ENTER/←/→: Alternar | ESC: Voltar', True, (150, 150, 150))
            surface.blit(hint, (menu_x + 10, menu_y + menu_height - 25))


def create_pause_menu(toggle_fullscreen_fn, get_global_fn, set_global_fn):
    """
    Factory function para criar um PauseMenu com os callbacks necessários.
    
    Args:
        toggle_fullscreen_fn: Função que alterna entre tela cheia e janela
        get_global_fn: Função que retorna o valor de uma variável global
        set_global_fn: Função que define o valor de uma variável global
    
    Returns:
        PauseMenu: Instância do menu de pausa configurado com os callbacks
    """
    def _get_value(key):
        """Callback para obter valor de uma configuração."""
        if key == 'fullscreen':
            return get_global_fn('is_fullscreen')
        elif key == 'hardcore':
            return get_global_fn('hardcore_mode')
        elif key == 'joystick_leading':
            return get_global_fn('joystick_leading')
        return False
    
    def _toggle(key):
        """Callback para alternar uma configuração."""
        if key == 'fullscreen':
            toggle_fullscreen_fn()
    
    return PauseMenu(callbacks={
        'get_value': _get_value,
        'toggle': _toggle,
        'get_global': get_global_fn,
        'set_global': set_global_fn,
    })

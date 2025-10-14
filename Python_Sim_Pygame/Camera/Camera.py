import pygame

class Camera:
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0
        self.camera_offset = [self.offset_x, self.offset_y]
        # scale: multiplicative zoom factor (1.0 = 100%)
        self.scale = 1.5

    def update(self, player):
        # Centraliza o player na tela independente da escala.
        # world_to_screen: sx = (x - offset_x) * Sscale
        # queremos sx == width/2  => offset_x = x - (width/2)/scale
        s = self.scale if hasattr(self, 'scale') and self.scale != 0 else 1.0
        self.offset_x = player.x - (self.width / 2.0) / s
        self.offset_y = player.y - (self.height / 2.0) / s
        self.camera_offset = [self.offset_x, self.offset_y]

    def apply(self, rect):
        # Aplica o deslocamento da câmera a um retângulo
        # aplica offset e escala (mantendo centro da tela)
        moved = rect.move(-self.offset_x, -self.offset_y)
        # escala do rect não é trivial; caller deve usar world_to_screen para
        # projetar pontos; aqui apenas aplica offset
        return moved

    def world_to_screen(self, point):
        """Converte um ponto (x,y) em coordenadas do mundo para coordenadas de tela,
        aplicando offset e escala (retorna tupla (sx, sy))."""
        x, y = point
        sx = (x - self.offset_x) * self.scale
        sy = (y - self.offset_y) * self.scale
        return (sx, sy)

    def screen_to_world(self, point):
        """Converte um ponto de tela para coordenadas do mundo (inverte world_to_screen)."""
        sx, sy = point
        x = sx / self.scale + self.offset_x
        y = sy / self.scale + self.offset_y
        return (x, y)
    
    def death_screen(self, screen, player, reset_callback):
        fonte = pygame.font.SysFont(None, 60)
        texto = fonte.render('Você morreu! Pressione R para reiniciar', True, (255, 0, 0))
        while player.is_dead():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    reset_callback()
            screen.blit(texto, (screen.get_width()//2 - texto.get_width()//2, screen.get_height()//2 - texto.get_height()//2))
            pygame.display.flip()
            pygame.time.Clock().tick(60)

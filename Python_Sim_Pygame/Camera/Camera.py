import pygame

class Camera:
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
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0

    def update(self, player):
        # Centraliza o player na tela
        self.offset_x = player.x - self.width // 2 + player.size // 2
        self.offset_y = player.y - self.height // 2 + player.size // 2

    def apply(self, rect):
        # Aplica o deslocamento da câmera a um retângulo
        return rect.move(-self.offset_x, -self.offset_y)

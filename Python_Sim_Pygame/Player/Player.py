import pygame

# Configurações do player
PLAYER_SIZE = 40
PLAYER_COLOR = (0, 0, 0)  # preto

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.color = PLAYER_COLOR
        self.state = 'vivo'  # estados: 'vivo', 'morto'

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.size, self.size))

    def move(self, keys, speed=5):
        if self.state != 'vivo':
            return
        if keys[pygame.K_a]:  # esquerda
            self.x -= speed
        if keys[pygame.K_d]:  # direita
            self.x += speed
        if keys[pygame.K_w]:  # cima
            self.y -= speed
        if keys[pygame.K_s]:  # baixo
            self.y += speed

    def set_dead(self):
        self.state = 'morto'

    def set_alive(self, x=None, y=None):
        self.state = 'vivo'
        if x is not None and y is not None:
            self.x = x
            self.y = y

    def is_dead(self):
        return self.state == 'morto'

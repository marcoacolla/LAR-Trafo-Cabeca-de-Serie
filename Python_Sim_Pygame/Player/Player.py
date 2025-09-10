import pygame
from Player.Wheels import Wheel

# Configurações do player
ROBOT_LENGTH   = 130 # Comprimento do robô ...... 350 cm
ROBOT_WIDTH   = 60 # Comprimento do robô ...... 125 cm
PLAYER_COLOR = (255, 220, 0)  # preto

class Player:
    
    

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lenght = ROBOT_LENGTH
        self.width = ROBOT_WIDTH
        self.color = PLAYER_COLOR
        self.state = 'vivo'  # estados: 'vivo', 'morto'

        # Offsets das rodas (relativo ao centro do veículo)
        half_w = self.width / 2
        half_l = self.lenght / 2

        self.wheels = [
            Wheel(self, "front_left",  -half_w, -half_l),
            Wheel(self, "front_right",  half_w, -half_l),
            Wheel(self, "rear_left",   -half_w,  half_l),
            Wheel(self, "rear_right",   half_w,  half_l),
        ]

    def getName(self):
        return "player"
    def getPosition(self):
        return (self.x, self.y)

    def getHeading(self):
        return 0  # Se quiser, pode adicionar rotação do player

    def draw(self, surface, camera_offset=(0,0)):
        # Desenha corpo
        rect = pygame.Rect(
            self.x - self.width // 2 - camera_offset[0],
            self.y - self.lenght // 2 - camera_offset[1],
            self.width,
            self.lenght
        )
        pygame.draw.rect(surface, self.color, rect, 6)

        # Desenha rodas
        for wheel in self.wheels:
            wheel.draw(surface, camera_offset)


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

        # Atualiza posição de todas as rodas
        for wheel in self.wheels:
            wheel.setPosition((self.x, self.y))
            wheel.setHeading(90)

    def set_dead(self):
        self.state = 'morto'

    def set_alive(self, x=None, y=None):
        self.state = 'vivo'
        if x is not None and y is not None:
            self.x = x
            self.y = y

    def is_dead(self):
        return self.state == 'morto'
    
    def get_hitbox(self):
        """
        Retorna o retângulo da hitbox do player.
        """

        hitbox = pygame.Rect(
            self.x - self.width // 2, 
            self.y - self.lenght // 2, 
            self.width, self.lenght)
        
        
        return hitbox

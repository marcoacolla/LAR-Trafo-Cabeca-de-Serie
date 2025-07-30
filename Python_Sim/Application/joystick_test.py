import pygame
import turtle
import GVL
# Inicializa o pygame e o módulo de joystick

class Joystick:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        # Detecta o primeiro joystick conectado
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    def update_joystick(self):
        pygame.event.pump()

        self.eixo_esquerdo_x = self.joystick.get_axis(0)  # Eixo X do analógico esquerdo
        self.eixo_esquerdo_y = self.joystick.get_axis(1)  # Eixo Y do analógico esquerdo

        self.eixo_direito_x = self.joystick.get_axis(2)  # Eixo X do analógico direito
        self.eixo_direito_y = self.joystick.get_axis(3)  # Eixo Y do analógico direito (em alguns modelos é o 5)
        # Aqui você pode mover seu robô, por exemplo:
        # turtle.setheading(eixo_x * 180)
        # turtle.forward(eixo_y * 5)

        # Agenda a próxima leitura
        turtle.ontimer(self.update_joystick, GVL.CONTROLLER_TICK)  # chama de novo em 100 ms

        return
    
    def getJoystickValues(self):
        return self.eixo_esquerdo_x, self.eixo_esquerdo_y, self.eixo_direito_x, self.eixo_direito_y

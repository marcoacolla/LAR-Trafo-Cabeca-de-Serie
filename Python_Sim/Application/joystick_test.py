import pygame
import turtle
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

        eixo_esquerdo_x = self.joystick.get_axis(0)  # Eixo X do analógico esquerdo
        eixo_esquerdo_y = self.joystick.get_axis(1)  # Eixo Y do analógico esquerdo

        eixo_direito_x = self.joystick.get_axis(2)  # Eixo X do analógico direito
        eixo_direito_y = self.joystick.get_axis(5)  # Eixo Y do analógico direito (em alguns modelos é o 5)

        print(eixo_esquerdo_x)
        # Aqui você pode mover seu robô, por exemplo:
        # turtle.setheading(eixo_x * 180)
        # turtle.forward(eixo_y * 5)

        # Agenda a próxima leitura
        turtle.ontimer(self.update_joystick, 100)  # chama de novo em 100 ms

        return eixo_esquerdo_x, eixo_esquerdo_y, eixo_direito_x, eixo_direito_y

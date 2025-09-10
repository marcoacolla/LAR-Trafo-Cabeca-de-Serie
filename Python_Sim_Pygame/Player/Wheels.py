import pygame
import math
import Player.GLV as GVL
from Player.Pathing.Axes import Axes  # adaptado para pygame

WHEEL_RADIUS = GVL.WHEEL_RADIUS
TIRE_THICKNESS = GVL.TIRE_THICKNESS

class Wheel:
    def __init__(self, parent, name, x_offset, y_offset, color=(100, 100, 100), width=2*WHEEL_RADIUS, length=TIRE_THICKNESS):
        self.parent = parent
        self.name = f"{self.parent.getName()}_{name}_wheel"
        self.width = width
        self.length = length
        self.relative_position = (x_offset, y_offset)

        self.current_steering_angle = None
        self.should_reverse = False
        self.last_desired_angle = None
        self.angular_limits = 130

        # Surface base da roda
        self.base_surface = pygame.Surface((self.width, self.length), 1)
        self.base_surface.fill(color)

        # Posição absoluta e heading
        self.pos = (0, 0)
        self.heading = 0

        # Eixos da roda
        self.fixed_axes = Axes(self, "fixed", x_axis_color=(255, 0, 0), y_axis_color=(255, 0, 0), fixed=True)
        self.moving_axes = Axes(self, "moving", x_axis_color=(0, 0, 0), y_axis_color=(0, 0, 0), fixed=False)

        # Inicializa posição e orientação
        self.setPosition(self.parent.getPosition())
        self.setHeading(self.parent.getHeading())

    ''' Métodos getters e setters '''

    def getName(self):
        return self.name

    def getPosition(self):
        return self.pos

    def getHeading(self):
        return self.heading

    def getOrientation(self):
        return [self.getPosition(), self.getHeading()]

    def setPosition(self, new_position):
        # Calcula posição relativa ao veículo
        angle = math.radians(self.parent.getHeading())
        relative_x, relative_y = self.relative_position

        rotated_x = relative_x * math.cos(angle) - relative_y * math.sin(angle)
        rotated_y = relative_x * math.sin(angle) + relative_y * math.cos(angle)

        parent_x, parent_y = self.parent.getPosition()
        self.pos = (parent_x + rotated_x, parent_y + rotated_y)

        # Atualiza eixos
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()

    def setHeading(self, new_heading):
        self.heading = new_heading
        self.fixed_axes.updateOrientation()
        self.moving_axes.updateOrientation()

    def draw(self, surface, camera_offset=(0, 0)):
        # Rotaciona e desenha a roda

        screen_x = self.pos[0] - camera_offset[0]
        screen_y = self.pos[1] - camera_offset[1]


        rotated_surface = pygame.transform.rotate(self.base_surface, -self.heading)
        rect = rotated_surface.get_rect(center=(screen_x, screen_y))
        surface.blit(rotated_surface, rect)

        # Atualiza e desenha eixos na tela (com offset da câmera)
        self.fixed_axes.draw(surface, camera_offset)
        self.moving_axes.draw(surface, camera_offset)

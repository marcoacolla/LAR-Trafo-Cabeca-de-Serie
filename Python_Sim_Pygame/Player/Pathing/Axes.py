import pygame
import math

class Axes:
    def __init__(self, parent, name, x_axis_color=(255, 0, 0), y_axis_color=(0, 255, 0), fixed=False, length=40):
        self.parent = parent
        self.name = f"{self.parent.getName()}_{name}_axes"
        self.x_axis_color = x_axis_color
        self.y_axis_color = y_axis_color
        self.fixed = fixed      # Se True, eixo não gira com a roda
        self.length = length    # Tamanho da linha desenhada
        self.lines = []         # Guarda os pontos das linhas (x_axis, y_axis)

        self.updateOrientation()

    def updateOrientation(self):
        px, py = self.parent.getPosition()
        heading = self.parent.getHeading()

        # Se o eixo é fixo, não acompanha rotação da roda
        angle_x = math.radians(0 if self.fixed else heading)
        angle_y = math.radians(90 if self.fixed else heading + 90)

        # Ponto final do eixo X
        x_end = (px + self.length * math.cos(angle_x),
                 py - self.length * math.sin(angle_x))

        # Ponto final do eixo Y
        y_end = (px + self.length * math.cos(angle_y),
                 py - self.length * math.sin(angle_y))

        self.lines = [
            ((px, py), x_end, self.x_axis_color),  # eixo X
            ((px, py), y_end, self.y_axis_color)   # eixo Y
        ]

    def draw(self, surface, camera_offset=(0,0)):
        for start, end, color in self.lines:
            start_screen = (start[0]-camera_offset[0], start[1]-camera_offset[1])
            end_screen = (end[0]-camera_offset[0], end[1]-camera_offset[1])
            pygame.draw.line(surface, color, start_screen, end_screen, 1)


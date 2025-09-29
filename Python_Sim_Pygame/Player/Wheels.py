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

        # Store a base surface in world units (unscaled). We'll scale it at draw time
        self.base_surface = pygame.Surface((max(1, int(self.width)), max(1, int(self.length))), pygame.SRCALPHA)
        self.base_surface.fill((0, 0, 0, 0))  # fundo transparente

        # desenha o retângulo da roda in world-px units; color may be overridden
        pygame.draw.rect(
            self.base_surface,
            color,
            (0, 0, int(self.width), int(self.length))
        )

        # Posição absoluta e heading
        self.pos = (0, 0)
        self.heading = 0

        # Eixos da roda
        self.fixed_axes = Axes(self, "fixed", x_axis_color=(255, 255, 0), y_axis_color=(255, 0, 0), fixed=True)
        self.moving_axes = Axes(self, "moving", x_axis_color=(0, 0, 0), y_axis_color=(0, 0, 0), fixed=False)

        # Inicializa posição e orientação
        self.setPosition(self.parent.getPosition())
        self.setHeading(self.parent.getHeading())

    ''' Métodos getters e setters '''

    def getName(self):
        return self.name
    def getPosition(self):
        return self.pos
    
    def getCameraRelativePosition(self, cam=None):
        # Backwards-compatible: if parent.camera has world_to_screen use it
        cam = self.parent.camera
        if hasattr(cam, 'world_to_screen'):
            return cam.world_to_screen(self.pos)
        return (self.pos[0] - cam.camera_offset[0], self.pos[1] - cam.camera_offset[1])

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

    def draw(self, surface, camera_or_offset=(0, 0)):
        # Rotaciona e desenha a roda

        if hasattr(camera_or_offset, 'world_to_screen'):
            screen_x, screen_y = camera_or_offset.world_to_screen(self.pos)
        else:
            screen_x = self.pos[0] - camera_or_offset[0]
            screen_y = self.pos[1] - camera_or_offset[1]

        # Scale base_surface from world pixels to screen pixels according to camera.scale
        cam = camera_or_offset if hasattr(camera_or_offset, 'world_to_screen') else None
        if cam is not None and hasattr(cam, 'scale'):
            scale = cam.scale
            sw = max(1, int(round(self.base_surface.get_width() * scale)))
            sh = max(1, int(round(self.base_surface.get_height() * scale)))
            scaled = pygame.transform.smoothscale(self.base_surface, (sw, sh))
        else:
            scaled = self.base_surface

        rotated_surface = pygame.transform.rotate(scaled, -self.heading)
        rect = rotated_surface.get_rect(center=(screen_x, screen_y))
        surface.blit(rotated_surface, rect)

        # Atualiza e desenha eixos na tela (com offset da câmera)
        self.fixed_axes.draw(surface, camera_or_offset)
        self.moving_axes.draw(surface, camera_or_offset)

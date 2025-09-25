import pygame
# Configurações do mundo
WIDTH, HEIGHT = 800, 600
BG_COLOR = (220, 230, 255)  # branco azulado
GRID_COLOR = (180, 180, 180)  # cinza
GRID_SIZE = 40

class World:

    def __init__(self, surface):
        self.surface = surface
        self.create_world_surface()
        
            
    def draw_grid(self, offset_x=0, offset_y=0):
        # O grid é desenhado considerando o deslocamento da câmera
        start_x = -offset_x % GRID_SIZE
        start_y = -offset_y % GRID_SIZE
        for x in range(start_x, WIDTH, GRID_SIZE):
            pygame.draw.line(self.surface, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(start_y, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.surface, GRID_COLOR, (0, y), (WIDTH, y))

    def create_world_surface(self, offset_x=0, offset_y=0):
        self.surface.fill(BG_COLOR)
        self.draw_grid(offset_x, offset_y)

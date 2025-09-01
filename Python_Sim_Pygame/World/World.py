import pygame
# Configurações do mundo
WIDTH, HEIGHT = 800, 600
BG_COLOR = (220, 230, 255)  # branco azulado
GRID_COLOR = (180, 180, 180)  # cinza
GRID_SIZE = 40

class World:
    @staticmethod
    def find_spawnpoint(map_image, player_size=40):
        # Aceita qualquer tom de verde (G > 200, R < 100, B < 100)
        min_x, min_y, max_x, max_y = None, None, None, None
        for y in range(map_image.get_height()):
            for x in range(map_image.get_width()):
                r, g, b = map_image.get_at((x, y))[:3]
                if g > 200 and r < 100 and b < 100:
                    if min_x is None or x < min_x:
                        min_x = x
                    if max_x is None or x > max_x:
                        max_x = x
                    if min_y is None or y < min_y:
                        min_y = y
                    if max_y is None or y > max_y:
                        max_y = y
        if min_x is not None and min_y is not None and max_x is not None and max_y is not None:
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            return center_x - player_size // 2, center_y - player_size // 2
        return 150, 150  # fallback

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

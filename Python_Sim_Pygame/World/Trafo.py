import pygame


class Trafo:
    """Small square object that can be picked up by the Player when fully contained
    inside the player's hitbox. Stores a carrier reference when picked.
    Coordinates are in world units (same as player)."""

    def __init__(self, x, y, size=60, color=(150, 80, 10)):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.picked = False
        self.carrier = None

    def get_rect(self):
        half = self.size / 2
        return pygame.Rect(self.x - half, self.y - half, self.size, self.size)

    def update(self, dt=0):
        # If carried, follow carrier
        if self.picked and self.carrier is not None:
            # keep at carrier center for now (could add offset)
            self.x, self.y = self.carrier.getPosition()

    def draw(self, surface, camera_or_offset=(0, 0)):
        # draw square in world coordinates; camera_or_offset may be Camera or (x,y)
        if hasattr(camera_or_offset, 'world_to_screen'):
            sx, sy = camera_or_offset.world_to_screen((self.x, self.y))
        else:
            camx, camy = camera_or_offset
            sx, sy = (self.x - camx, self.y - camy)

        half = max(1, int(round(self.size / 2)))
        rect = pygame.Rect(int(sx - half), int(sy - half), half * 2, half * 2)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, (0,0,0), rect, 1)

    def pick(self, player):
        self.picked = True
        self.carrier = player

    def drop(self):
        self.picked = False
        self.carrier = None

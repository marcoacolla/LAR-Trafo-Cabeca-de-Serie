import pygame
import math
import os


class Trafo:
    """Small square object that can be picked up by the Player when fully contained
    inside the player's hitbox. Stores a carrier reference when picked.
    Coordinates are in world units (same as player)."""

    def __init__(self, x, y, size=60, color=(150, 80, 10), image_path=None, image_scale=2):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.picked = False
        self.carrier = None
        # collision_shrink is the fraction to reduce the visible size when
        # computing collisions. 0.0 means collision rect == visual rect.
        # A small positive value (e.g. 0.2) makes the hitbox smaller than the
        # drawn square so collisions feel tighter and match the sprite.
        self.collision_shrink = 0.2
        
        # image_scale: multiplicador para o tamanho da imagem (1.0 = tamanho original, 1.5 = 50% maior, etc)
        self.image_scale = image_scale
        
        # Load image if provided
        self.image = None
        self.image_scaled = None
        if image_path:
            self._load_image(image_path)
    
    def _load_image(self, image_path):
        """Load and scale the PNG image for the trafo."""
        try:
            # If relative path, make it relative to the World folder
            if not os.path.isabs(image_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                image_path = os.path.join(current_dir, image_path)
            
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path).convert_alpha()
                self._scale_image()
            else:
                print(f"Warning: Image file not found: {image_path}")
        except Exception as e:
            print(f"Error loading image: {e}")

    def _scale_image(self):
        """Scale the image to match the size attribute multiplied by image_scale."""
        if self.image:
            scaled_size = int(self.size * self.image_scale)
            self.image_scaled = pygame.transform.scale(self.image, (scaled_size, scaled_size))

    def get_rect(self):
        half = self.size / 2
        return pygame.Rect(self.x - half, self.y - half, self.size, self.size)

    def get_collision_rect(self):
        """Return a pygame.Rect used for collision tests. This rect is slightly
        smaller than the visual rect by applying `collision_shrink` as a
        proportion of the size (shrink applies equally on both axes)."""
        frac = max(0.0, min(0.9, float(self.collision_shrink)))
        coll_size = self.size * (1.0 - frac)
        half = coll_size / 2.0
        return pygame.Rect(self.x - half, self.y - half, coll_size, coll_size)

    def update(self, dt=0):
        # If carried, follow carrier
        if self.picked and self.carrier is not None:
            # follow carrier but keep the attachment offset (in carrier-local coords)
            try:
                px, py = self.carrier.getPosition()
                # attachment offset stored in local coordinates when picked
                if hasattr(self, 'attach_offset_local') and self.attach_offset_local is not None:
                    lx, ly = self.attach_offset_local
                    theta = getattr(self.carrier, 'getHeading', lambda: 0)()
                    th = math.radians(theta)
                    cos_t = math.cos(th)
                    sin_t = math.sin(th)
                    # rotate local offset back to world and add to carrier position
                    wx = px + (lx * cos_t - ly * sin_t)
                    wy = py + (lx * sin_t + ly * cos_t)
                    self.x, self.y = wx, wy
                else:
                    self.x, self.y = px, py
            except Exception:
                try:
                    self.x, self.y = self.carrier.getPosition()
                except Exception:
                    pass

    def draw(self, surface, camera_or_offset=(0, 0)):
        # draw image or square in world coordinates; camera_or_offset may be Camera or (x,y)
        if hasattr(camera_or_offset, 'world_to_screen'):
            sx, sy = camera_or_offset.world_to_screen((self.x, self.y))
        else:
            camx, camy = camera_or_offset
            sx, sy = (self.x - camx, self.y - camy)

        half = max(1, int(round(self.size / 2)))
        
        if self.image_scaled:
            # Draw the scaled image centered at the position
            rect = self.image_scaled.get_rect(center=(int(sx), int(sy)))
            surface.blit(self.image_scaled, rect)
        else:
            # Fallback to drawing a square if no image is loaded
            rect = pygame.Rect(int(sx - half), int(sy - half), half * 2, half * 2)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, (0,0,0), rect, 1)

    def pick(self, player):
        self.picked = True
        self.carrier = player
        # compute attachment offset in player's local coordinates so the trafo
        # preserves its relative placement even if the player rotates.
        try:
            px, py = player.getPosition()
            dx = self.x - px
            dy = self.y - py
            theta = getattr(player, 'getHeading', lambda: 0)()
            th = math.radians(theta)
            # local = R(-theta) * (dx,dy)
            lx = dx * math.cos(th) + dy * math.sin(th)
            ly = -dx * math.sin(th) + dy * math.cos(th)
            self.attach_offset_local = (lx, ly)
        except Exception:
            self.attach_offset_local = (0.0, 0.0)

    def drop(self):
        self.picked = False
        self.carrier = None
        try:
            if hasattr(self, 'attach_offset_local'):
                del self.attach_offset_local
        except Exception:
            pass

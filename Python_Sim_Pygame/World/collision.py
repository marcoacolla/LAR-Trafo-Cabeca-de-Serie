"""
Collision module - Handles all collision detection logic.
Separates collision algorithms from main game loop for better maintainability.
"""

import math
import pygame


def find_green_center(img, thresh=200):
    """
    Lightweight: find a green pixel (centroid of green area) to use as spawn 
    and to ignore in collisions.
    """
    w, h = img.get_width(), img.get_height()
    totx = toty = count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            if g >= thresh and r < 100 and b < 100:
                totx += x; toty += y; count += 1
    if count == 0:
        return None
    return (totx / count, toty / count)


def find_blue_center(img):
    """
    Find centroid of a blue marker by testing if B is significantly
    larger than R and G (robust to different blue intensities).
    Returns (x,y) in image/world coordinates or None if not found.
    """
    w, h = img.get_width(), img.get_height()
    totx = toty = count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            # blue if b is notably higher than r and g and has decent intensity
            if b > max(r, g) + 30 and b > 80:
                totx += x; toty += y; count += 1
    if count == 0:
        return None
    return (totx / count, toty / count)


def build_collision_grid(img):
    """
    Build a virtual collision map once: a grid (bytearray per row) where 
    1 means occupied. Only BLACK pixels cause collision/death.
    Everything else (green spawn, white, gray path, blue marker) is safe.
    """
    w, h = img.get_width(), img.get_height()
    grid = [bytearray(w) for _ in range(h)]
    occupied = 0
    for y in range(h):
        row = grid[y]
        for x in range(w):
            r, g, b, *rest = img.get_at((x, y))
            # Only treat BLACK as collision/death
            if r < 50 and g < 50 and b < 50:  # Black pixels cause death
                row[x] = 1
                occupied += 1
    return grid, occupied


def point_in_poly(x, y, poly):
    """Ray-casting algorithm to check if a point is inside a polygon."""
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def seg_intersect(a1, a2, b1, b2):
    """Check if two line segments intersect."""
    (x1, y1), (x2, y2) = a1, a2
    (x3, y3), (x4, y4) = b1, b2
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if abs(denom) < 1e-9:
        return False
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    return 0.0 <= ua <= 1.0 and 0.0 <= ub <= 1.0


def poly_rect_collision(poly, rect):
    """Check collision between a polygon and a rectangle."""
    # 1) any polygon vertex inside rect
    for (px, py) in poly:
        if rect.collidepoint(px, py):
            return True
    # 2) any rect corner inside polygon
    corners = [(rect.left, rect.top), (rect.right, rect.top), 
               (rect.right, rect.bottom), (rect.left, rect.bottom)]
    for (cx, cy) in corners:
        if point_in_poly(cx + 0.0, cy + 0.0, poly):
            return True
    # 3) any segment of poly intersects any rect edge
    rect_edges = [
        ((rect.left, rect.top), (rect.right, rect.top)),
        ((rect.right, rect.top), (rect.right, rect.bottom)),
        ((rect.right, rect.bottom), (rect.left, rect.bottom)),
        ((rect.left, rect.bottom), (rect.left, rect.top)),
    ]
    for i in range(len(poly)):
        a1 = poly[i]
        a2 = poly[(i + 1) % len(poly)]
        for b1, b2 in rect_edges:
            if seg_intersect(a1, a2, b1, b2):
                return True
    return False


def line_rect_collision(p1, p2, rect):
    """Check collision between a line segment and a rectangle."""
    # 1) either endpoint inside rect
    if rect.collidepoint(p1) or rect.collidepoint(p2):
        return True
    # 2) intersects rect edges
    rect_edges = [
        ((rect.left, rect.top), (rect.right, rect.top)),
        ((rect.right, rect.top), (rect.right, rect.bottom)),
        ((rect.right, rect.bottom), (rect.left, rect.bottom)),
        ((rect.left, rect.bottom), (rect.left, rect.top)),
    ]
    for b1, b2 in rect_edges:
        if seg_intersect(p1, p2, b1, b2):
            return True
    return False


def check_poly_collision(poly, collision_grid, map_image):
    """Check if a polygon collides with the collision grid (black pixels)."""
    # compute integer bounding box of polygon to limit work
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    minx = max(int(math.floor(min(xs))), 0)
    maxx = min(int(math.ceil(max(xs))), map_image.get_width() - 1)
    miny = max(int(math.floor(min(ys))), 0)
    maxy = min(int(math.ceil(max(ys))), map_image.get_height() - 1)

    for px in range(minx, maxx + 1):
        for py in range(miny, maxy + 1):
            world_x = px + 0.5
            world_y = py + 0.5
            if point_in_poly(world_x, world_y, poly):
                map_x = int(world_x)
                map_y = int(world_y)
                if not (0 <= map_x < map_image.get_width() and 0 <= map_y < map_image.get_height()):
                    continue
                try:
                    if collision_grid[map_y][map_x]:
                        return True
                except Exception:
                    continue
    return False


def check_line_collision(p1, p2, collision_grid, map_image):
    """Check if a line segment collides with the collision grid (black pixels)."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        # degenerate: treat single point
        ix, iy = int(round(x1)), int(round(y1))
        if 0 <= ix < map_image.get_width() and 0 <= iy < map_image.get_height():
            try:
                return bool(collision_grid[iy][ix])
            except Exception:
                return False
        return False

    steps = int(math.ceil(length))
    for i in range(steps + 1):
        t = float(i) / float(steps)
        wx = x1 + dx * t
        wy = y1 + dy * t
        ix = int(wx)
        iy = int(wy)
        if not (0 <= ix < map_image.get_width() and 0 <= iy < map_image.get_height()):
            continue
        try:
            if collision_grid[iy][ix]:
                return True
        except Exception:
            continue
    return False


def check_player_collision_with_map(player, collision_grid, map_image):
    """
    Check all parts of the player hitbox against the collision grid.
    Returns True if collision detected.
    """
    collided = False
    parts = player.get_rotated_hitbox()
    
    for kind, data in parts:
        if collided:
            break
        try:
            if kind == 'wheel':
                # data is poly (list of points)
                if check_poly_collision(data, collision_grid, map_image):
                    collided = True
                    break
            elif kind in ('edge', 'line', 'side'):
                p1, p2 = data
                if check_line_collision(p1, p2, collision_grid, map_image):
                    collided = True
                    break
            else:
                # unknown part: if it's a polygon-like sequence assume polygon
                if isinstance(data, (list, tuple)) and len(data) >= 3:
                    if check_poly_collision(data, collision_grid, map_image):
                        collided = True
                        break
        except Exception:
            # safe fallback: ignore this part on error
            continue
    
    return collided

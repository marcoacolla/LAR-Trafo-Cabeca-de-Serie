import os
import pygame

from game.tutorial_progress import get_tutorial_map_states


def _list_map_files():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    obstacles = os.path.join(base, 'World', 'Obstacles')
    if not os.path.isdir(obstacles):
        return [], obstacles
    exts = ('.png', '.jpg', '.jpeg')
    files = [f for f in os.listdir(obstacles) if f.lower().endswith(exts)]
    files.sort()
    paths = [os.path.join(obstacles, f) for f in files]
    return paths, obstacles


def run_map_select_menu(screen):
    """Display a simple selectable list of map image files.
    Returns the selected full path or None if canceled/backed out.
    """
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small = pygame.font.SysFont(None, 24)

    files, obstacles_dir = _list_map_files()
    if not files:
        # nothing to choose from
        return None

    selected = 0
    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected = (selected - 1) % len(files)
                elif ev.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(files)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return files[selected]
                elif ev.key == pygame.K_ESCAPE:
                    return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                sw, sh = screen.get_size()
                btn_w = 600
                btn_h = 48
                center_x = sw // 2
                base_y = sh // 4
                for i, path in enumerate(files):
                    bx = center_x - btn_w // 2
                    by = base_y + i * (btn_h + 8)
                    r = pygame.Rect(bx, by, btn_w, btn_h)
                    if r.collidepoint((mx, my)):
                        return path

        # draw
        screen.fill((18, 20, 24))
        title = font.render('Escolher Mapa', True, (220, 220, 255))
        sw, sh = screen.get_size()
        screen.blit(title, ((sw - title.get_width()) // 2, sh // 8))

        btn_w = 600
        btn_h = 48
        center_x = sw // 2
        base_y = sh // 4
        for i, path in enumerate(files):
            label = os.path.splitext(os.path.basename(path))[0]
            bx = center_x - btn_w // 2
            by = base_y + i * (btn_h + 8)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            if i == selected:
                pygame.draw.rect(screen, (0, 70, 220), rect)
                txt = small.render(label, True, (255, 255, 255))
            else:
                pygame.draw.rect(screen, (255, 255, 255), rect)
                txt = small.render(label, True, (0, 70, 220))
            screen.blit(txt, (bx + (btn_w - txt.get_width()) // 2, by + (btn_h - txt.get_height()) // 2))

        hint = small.render('Enter: selecionar  Esc: voltar', True, (180, 180, 180))
        screen.blit(hint, ((sw - hint.get_width()) // 2, base_y + len(files) * (btn_h + 8) + 12))

        pygame.display.flip()


def run_tutorial_select_menu(screen, project_root):
    """Display all tutorial maps; only unlocked phases are selectable."""
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small = pygame.font.SysFont(None, 24)

    entries = get_tutorial_map_states(project_root)
    if not entries:
        return None

    selected = 0
    while True:
        clock.tick(60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected = (selected - 1) % len(entries)
                elif ev.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(entries)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if bool(entries[selected].get('unlocked', False)):
                        return str(entries[selected].get('path', ''))
                elif ev.key == pygame.K_ESCAPE:
                    return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                sw, sh = screen.get_size()
                btn_w = 720
                btn_h = 52
                center_x = sw // 2
                base_y = sh // 4
                for i, entry in enumerate(entries):
                    bx = center_x - btn_w // 2
                    by = base_y + i * (btn_h + 8)
                    rect = pygame.Rect(bx, by, btn_w, btn_h)
                    if rect.collidepoint((mx, my)) and bool(entry.get('unlocked', False)):
                        return str(entry.get('path', ''))

        screen.fill((18, 20, 24))
        title = font.render('Tutorial - Escolher Fase', True, (220, 220, 255))
        sw, sh = screen.get_size()
        screen.blit(title, ((sw - title.get_width()) // 2, sh // 10))

        btn_w = 720
        btn_h = 52
        center_x = sw // 2
        base_y = sh // 4

        for i, entry in enumerate(entries):
            raw_name = os.path.splitext(os.path.basename(str(entry.get('name', ''))))[0]
            is_unlocked = bool(entry.get('unlocked', False))
            is_completed = bool(entry.get('completed', False))

            if is_completed:
                status = ' [CONCLUIDA]'
            elif is_unlocked:
                status = ' [DISPONIVEL]'
            else:
                status = ' [BLOQUEADA]'

            label = f'{i + 1}. {raw_name}{status}'
            bx = center_x - btn_w // 2
            by = base_y + i * (btn_h + 8)
            rect = pygame.Rect(bx, by, btn_w, btn_h)

            if not is_unlocked:
                bg = (70, 70, 70)
                fg = (190, 190, 190)
            elif is_completed:
                bg = (24, 120, 60) if i == selected else (250, 250, 250)
                fg = (255, 255, 255) if i == selected else (24, 120, 60)
            else:
                bg = (0, 70, 220) if i == selected else (255, 255, 255)
                fg = (255, 255, 255) if i == selected else (0, 70, 220)

            pygame.draw.rect(screen, bg, rect)
            txt = small.render(label, True, fg)
            screen.blit(txt, (bx + 14, by + (btn_h - txt.get_height()) // 2))

        hint = small.render('Enter/Clique: selecionar fase disponivel  Esc: voltar', True, (180, 180, 180))
        screen.blit(hint, ((sw - hint.get_width()) // 2, base_y + len(entries) * (btn_h + 8) + 14))

        pygame.display.flip()

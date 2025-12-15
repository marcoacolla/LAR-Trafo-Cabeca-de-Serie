import pygame

def run_options_menu(screen, initial_config=None):
    """Simple options menu returning updated config dict.
    initial_config: dict with keys 'hardcore' (bool) and 'fullscreen' (bool)
    """
    cfg = {'hardcore': False, 'fullscreen': False}
    if initial_config:
        cfg.update(initial_config)

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    running = True
    selected = 0
    options = ['Modo Hardcore', 'Tela Cheia', 'Voltar']
    while running:
        dt = clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return cfg
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN) and selected == 2:
                    return cfg
                if ev.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                if ev.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if selected == 0:
                        cfg['hardcore'] = not cfg['hardcore']
                    elif selected == 1:
                        cfg['fullscreen'] = not cfg['fullscreen']
                    elif selected == 2:
                        return cfg
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # simple hit test: calculate button rects
                sw, sh = screen.get_size()
                btn_w = 400
                btn_h = 56
                center_x = sw // 2
                base_y = sh // 2 - (len(options)//2) * (btn_h + 12)
                for i, _ in enumerate(options):
                    bx = center_x - btn_w//2
                    by = base_y + i * (btn_h + 12)
                    r = pygame.Rect(bx, by, btn_w, btn_h)
                    if r.collidepoint((mx, my)):
                        if i == 0:
                            cfg['hardcore'] = not cfg['hardcore']
                        elif i == 1:
                            cfg['fullscreen'] = not cfg['fullscreen']
                        elif i == 2:
                            return cfg

        # draw
        screen.fill((24, 24, 24))
        title = font.render('Opções', True, (200, 200, 255))
        sw, sh = screen.get_size()
        screen.blit(title, ((sw - title.get_width())//2, sh//4))

        btn_w = 400
        btn_h = 56
        center_x = sw // 2
        base_y = sh // 2 - (len(options)//2) * (btn_h + 12)
        small = pygame.font.SysFont(None, 28)
        for i, label in enumerate(options):
            bx = center_x - btn_w//2
            by = base_y + i * (btn_h + 12)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            sel = (i == selected)
            color = (0, 70, 220) if sel else (200,200,200)
            pygame.draw.rect(screen, (255,255,255), rect)
            if i == 0:
                text = f"{label}: {'ON' if cfg['hardcore'] else 'OFF'}"
            elif i == 1:
                text = f"{label}: {'ON' if cfg['fullscreen'] else 'OFF'}"
            else:
                text = label
            txt = small.render(text, True, (0,70,220))
            screen.blit(txt, (bx + (btn_w - txt.get_width())//2, by + (btn_h - txt.get_height())//2))

        pygame.display.flip()

    return cfg

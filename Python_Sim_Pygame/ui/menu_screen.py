# Minimal start menu for the simulator. Shows Jogar / Opções / Sair and
# returns a dict with selected options.
import pygame
from .screens.options_screen import run_options_menu


def run_start_menu(screen, initial_config=None):
	cfg = {'hardcore': False, 'fullscreen': False}
	if initial_config:
		cfg.update(initial_config)

	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 48)
	small = pygame.font.SysFont(None, 28)

	options = ['Jogar', 'Opções', 'Sair']
	selected = 0
	while True:
		dt = clock.tick(60)
		for ev in pygame.event.get():
			if ev.type == pygame.QUIT:
				return cfg, 'exit'
			if ev.type == pygame.KEYDOWN:
				if ev.key == pygame.K_UP:
					selected = (selected - 1) % len(options)
				elif ev.key == pygame.K_DOWN:
					selected = (selected + 1) % len(options)
				elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
					if selected == 0:
								return cfg, 'map_select'
					elif selected == 1:
						# open options menu
						new_cfg = run_options_menu(screen, cfg)
						if new_cfg:
							cfg.update(new_cfg)
					elif selected == 2:
						return cfg, 'exit'
			if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
				mx, my = ev.pos
				sw, sh = screen.get_size()
				btn_w = 400
				btn_h = 64
				center_x = sw // 2
				base_y = sh // 2 - (len(options)//2) * (btn_h + 16)
				for i, _ in enumerate(options):
					bx = center_x - btn_w//2
					by = base_y + i * (btn_h + 16)
					r = pygame.Rect(bx, by, btn_w, btn_h)
					if r.collidepoint((mx, my)):
						if i == 0:
									return cfg, 'map_select'
						elif i == 1:
							new_cfg = run_options_menu(screen, cfg)
							if new_cfg:
								cfg.update(new_cfg)
						elif i == 2:
							return cfg, 'exit'

		# draw
		screen.fill((16, 18, 22))
		title = font.render('Trafo Simulator', True, (220, 220, 255))
		sw, sh = screen.get_size()
		screen.blit(title, ((sw - title.get_width())//2, sh//4))

		btn_w = 400
		btn_h = 64
		center_x = sw // 2
		base_y = sh // 2 - (len(options)//2) * (btn_h + 16)
		for i, label in enumerate(options):
			bx = center_x - btn_w//2
			by = base_y + i * (btn_h + 16)
			rect = pygame.Rect(bx, by, btn_w, btn_h)
			if i == selected:
				pygame.draw.rect(screen, (0,70,220), rect)
				txt = small.render(label, True, (255,255,255))
			else:
				pygame.draw.rect(screen, (255,255,255), rect)
				txt = small.render(label, True, (0,70,220))
			screen.blit(txt, (bx + (btn_w - txt.get_width())//2, by + (btn_h - txt.get_height())//2))

		# hint of current options
		hint = small.render(f"Hardcore: {'ON' if cfg.get('hardcore') else 'OFF'}  |  Fullscreen: {'ON' if cfg.get('fullscreen') else 'OFF'}", True, (180,180,180))
		screen.blit(hint, ((sw - hint.get_width())//2, base_y + len(options)*(btn_h+16) + 8))

		pygame.display.flip()



# Minimal start menu for the simulator. Shows Jogar / Opções / Sair and
# returns a dict with selected options.
import pygame
from .screens.options_screen import run_options_menu


def run_start_menu(screen, initial_config=None, from_pause=False):
	cfg = {'hardcore': False, 'fullscreen': False}
	if initial_config:
		cfg.update(initial_config)

	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 64)
	title_sub = pygame.font.SysFont(None, 30)
	small = pygame.font.SysFont(None, 28)

	base_options = ['Começar', 'Tutorial', 'Controle', 'Opções', 'Sair']
	if from_pause:
		options = ['Continuar'] + base_options
	else:
		options = list(base_options)
	selected = 0

	def action_from_index(idx):
		if from_pause:
			if idx == 0:
				return 'resume'
			idx -= 1

		if idx == 0:
			return 'map_select'
		if idx == 1:
			return 'tutorial'
		if idx == 2:
			return 'control'
		if idx == 3:
			return 'options'
		if idx == 4:
			return 'exit'
		return None

	def execute_action(action):
		if action == 'options':
			new_cfg = run_options_menu(screen, cfg)
			if new_cfg:
				cfg.update(new_cfg)
			return None
		return action

	def get_layout(sw, sh):
		btn_w = 400
		btn_h = 64
		center_x = sw // 2
		# Push buttons a bit down to give room for title/subtitle.
		base_y = sh // 2 - (len(options)//2) * (btn_h + 16) + 52
		return btn_w, btn_h, center_x, base_y

	while True:
		clock.tick(60)
		for ev in pygame.event.get():
			if ev.type == pygame.QUIT:
				return cfg, 'exit'
			if ev.type == pygame.KEYDOWN:
				if ev.key == pygame.K_UP:
					selected = (selected - 1) % len(options)
				elif ev.key == pygame.K_DOWN:
					selected = (selected + 1) % len(options)
				elif ev.key == pygame.K_ESCAPE:
					# ESC behaves as "back" inside menu navigation.
					selected = (selected - 1) % len(options)
				elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
					action = execute_action(action_from_index(selected))
					if action:
						return cfg, action
			if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
				mx, my = ev.pos
				sw, sh = screen.get_size()
				btn_w, btn_h, center_x, base_y = get_layout(sw, sh)
				for i, _ in enumerate(options):
					bx = center_x - btn_w//2
					by = base_y + i * (btn_h + 16)
					r = pygame.Rect(bx, by, btn_w, btn_h)
					if r.collidepoint((mx, my)):
						action = execute_action(action_from_index(i))
						if action:
							return cfg, action

		# draw
		screen.fill((16, 18, 22))
		sw, sh = screen.get_size()
		title = font.render('TRAFO SIMULATOR', True, (235, 241, 255))
		title_shadow = font.render('TRAFO SIMULATOR', True, (12, 15, 28))
		subtitle = title_sub.render('Cabeca de Serie', True, (143, 185, 255))
		title_y = max(34, sh // 8)
		title_x = (sw - title.get_width()) // 2
		screen.blit(title_shadow, (title_x + 3, title_y + 3))
		screen.blit(title, (title_x, title_y))
		sub_x = (sw - subtitle.get_width()) // 2
		sub_y = title_y + title.get_height() - 6
		screen.blit(subtitle, (sub_x, sub_y))
		pygame.draw.line(screen, (61, 97, 170), (sw // 2 - 215, sub_y + subtitle.get_height() + 8), (sw // 2 + 215, sub_y + subtitle.get_height() + 8), 2)

		btn_w, btn_h, center_x, base_y = get_layout(sw, sh)
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
		hint = small.render(f"Hardcore: {'ON' if cfg.get('hardcore') else 'OFF'}  |  TTC Control: {'ON' if cfg.get('ttc_control', False) else 'OFF'}", True, (180,180,180))
		screen.blit(hint, ((sw - hint.get_width())//2, base_y + len(options)*(btn_h+16) + 8))

		pygame.display.flip()



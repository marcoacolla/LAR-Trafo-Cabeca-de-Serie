# Minimal start menu for the simulator. Shows Jogar / Opções / Sair and
# returns a dict with selected options.
import pygame
from .screens.options_screen import run_options_menu


def run_start_menu(screen, initial_config=None, from_pause=False):
	cfg = {'hardcore': False, 'fullscreen': False}
	if initial_config:
		cfg.update(initial_config)

	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 48)
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
				btn_w = 400
				btn_h = 64
				center_x = sw // 2
				base_y = sh // 2 - (len(options)//2) * (btn_h + 16)
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
		hint = small.render(f"Hardcore: {'ON' if cfg.get('hardcore') else 'OFF'}  |  Joystick Leading: {'ON' if cfg.get('joystick_leading', True) else 'OFF'}", True, (180,180,180))
		screen.blit(hint, ((sw - hint.get_width())//2, base_y + len(options)*(btn_h+16) + 8))

		pygame.display.flip()



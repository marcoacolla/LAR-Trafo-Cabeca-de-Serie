# Control screen with image display and back button
import pygame


def run_control_screen(screen):
	"""Display control screen with back button in bottom-right corner."""
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 28)
	
	btn_w = 120
	btn_h = 48
	
	while True:
		dt = clock.tick(60)
		for ev in pygame.event.get():
			if ev.type == pygame.QUIT:
				return 'exit'
			if ev.type == pygame.KEYDOWN:
				if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
					return 'back'
				elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
					return 'back'
			if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
				mx, my = ev.pos
				sw, sh = screen.get_size()
				# Back button in bottom-right corner
				bx = sw - btn_w - 16
				by = sh - btn_h - 16
				r = pygame.Rect(bx, by, btn_w, btn_h)
				if r.collidepoint((mx, my)):
					return 'back'

		# Draw
		screen.fill((16, 18, 22))
		
		# Title
		title = font.render('Controle', True, (220, 220, 255))
		sw, sh = screen.get_size()
		screen.blit(title, (16, 16))
		
		# Back button (bottom-right)
		bx = sw - btn_w - 16
		by = sh - btn_h - 16
		btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
		pygame.draw.rect(screen, (255, 255, 255), btn_rect)
		btn_txt = font.render('Voltar', True, (0, 70, 220))
		screen.blit(btn_txt, (bx + (btn_w - btn_txt.get_width())//2, by + (btn_h - btn_txt.get_height())//2))
		
		pygame.display.flip()

import math
import os
from typing import Dict, Optional, Sequence, Tuple

import pygame


class DialogueManager:
	COLOR_DIALOG_1 = (255, 0, 0)
	COLOR_DIALOG_2 = (255, 255, 0)
	COLOR_DIALOG_3 = (255, 0, 255)

	DIALOG_TEXTS_BY_PHASE: Dict[str, Dict[int, str]] = {
		"t_inclometro": {
			1: "Esta fase auxiliará você a entender o inclinômetro e os alertas importantes para a operação segura do robô. Quanto mais avermelhado é o piso, mais inclinado é o plano",
			2: "Inclinação de alerta: O inclinômetro detecta quando o robô atinge uma inclinação perigosa.",
			3: "Inclinação crítica: Se a inclinação continuar aumentando, o robô pode tombar. Mantenha o controle para evitar danos.",
		},
		"t_inclinometro": {
			1: "Bem vindo ao Trafo Simulator! Esta fase auxiliará você a entender o funcionamento do inclinômetro os alertas importantes para a operação segura do robô.",
			2: "Inclinação de alerta: O inclinômetro detecta quando o robô atinge uma inclinação perigosa.",
			3: "Inclinação crítica: Se a inclinação continuar aumentando, o robô pode tombar. Mantenha o controle para evitar danos.",
		},
		"fase_2": {
			1: "[Fase 2] Diálogo 1: Iniciando novo objetivo.",
			2: "[Fase 2] Diálogo 2: Verifique o alinhamento do robô.",
			3: "[Fase 2] Diálogo 3: Priorize segurança e estabilidade.",
		},
		"fase_3": {
			1: "[Fase 3] Diálogo 1: Área operacional avançada.",
			2: "[Fase 3] Diálogo 2: Mantendo controle de trajetória.",
			3: "[Fase 3] Diálogo 3: Finalize a manobra com precisão.",
		},
	}

	def __init__(
		self,
		project_root: str,
		obstacle_map_path: str,
		obstacle_map_size: Tuple[int, int],
		phase: str = "t_inclometro",
	):
		self.project_root = project_root
		self.obstacle_map_path = obstacle_map_path
		self.phase = phase
		self.event_map_image: Optional[pygame.Surface] = self._load_event_map(obstacle_map_size)
		self.last_dialog_id: int = 0
		self.active_dialog_id: int = 0
		self.active_dialog_text: str = ""

	@property
	def enabled(self) -> bool:
		return self.event_map_image is not None

	def set_phase(self, phase: str) -> None:
		self.phase = phase

	def get_dialog_text(self, dialog_id: int, phase: Optional[str] = None) -> str:
		phase_key = phase or self.phase
		phase_dialogs = self.DIALOG_TEXTS_BY_PHASE.get(phase_key, {})
		return phase_dialogs.get(dialog_id, f"[Sem texto] diálogo {dialog_id} ({phase_key})")

	def process_player_polygon(self, polygon: Sequence[Tuple[float, float]], auto_print: bool = False) -> int:
		current_dialog_id = self.detect_dialog_from_polygon(polygon)

		if current_dialog_id != self.last_dialog_id:
			if current_dialog_id in (1, 2, 3):
				self.active_dialog_id = current_dialog_id
				self.active_dialog_text = self.get_dialog_text(current_dialog_id)
			else:
				self.active_dialog_id = 0
				self.active_dialog_text = ""
			self.last_dialog_id = current_dialog_id

		if auto_print and self.active_dialog_text:
			print(self.active_dialog_text)

		return current_dialog_id

	def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> Sequence[str]:
		words = text.split()
		if not words:
			return []

		lines = []
		current = words[0]
		for word in words[1:]:
			test = f"{current} {word}"
			if font.size(test)[0] <= max_width:
				current = test
			else:
				lines.append(current)
				current = word
		lines.append(current)
		return lines

	def draw_dialog_box(self, screen: pygame.Surface) -> None:
		if not self.active_dialog_text:
			return

		sw, sh = screen.get_size()
		box_w = min(900, max(520, int(sw * 0.72)))
		pad_x = 18
		pad_y = 12
		text_font = pygame.font.SysFont(None, 28)

		text_lines = self._wrap_text(self.active_dialog_text, text_font, box_w - (pad_x * 2))
		line_h = text_font.get_height() + 4
		content_h = len(text_lines) * line_h
		box_h = content_h + (pad_y * 2)

		box_x = (sw - box_w) // 2
		box_y = sh - box_h - 16

		bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
		bg.fill((10, 14, 24, 220))
		screen.blit(bg, (box_x, box_y))
		pygame.draw.rect(screen, (220, 220, 230), pygame.Rect(box_x, box_y, box_w, box_h), 2)

		y = box_y + pad_y
		for line in text_lines:
			line_surf = text_font.render(line, True, (245, 245, 245))
			screen.blit(line_surf, (box_x + pad_x, y))
			y += line_h

	def _load_event_map(self, obstacle_map_size: Tuple[int, int]) -> Optional[pygame.Surface]:
		try:
			event_map_candidate = os.path.join(
				self.project_root,
				"World",
				"EventMap",
				os.path.basename(self.obstacle_map_path),
			)
			if not os.path.isfile(event_map_candidate):
				return None

			event_map = pygame.image.load(event_map_candidate).convert()
			if event_map.get_size() != obstacle_map_size:
				event_map = pygame.transform.scale(event_map, obstacle_map_size)
			return event_map
		except Exception:
			return None

	def _classify_dialog_color(self, color) -> int:
		try:
			red = int(color[0])
			green = int(color[1])
			blue = int(color[2])
		except Exception:
			return 0

		if red >= 250 and green <= 10 and blue <= 10:
			return 1
		if red >= 250 and green >= 250 and blue <= 10:
			return 2
		if red >= 250 and green <= 10 and blue >= 250:
			return 3
		return 0

	def _point_in_polygon(self, x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
		inside = False
		j = len(polygon) - 1
		for i in range(len(polygon)):
			xi, yi = polygon[i]
			xj, yj = polygon[j]
			intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
			if intersect:
				inside = not inside
			j = i
		return inside

	def detect_dialog_from_polygon(self, polygon: Sequence[Tuple[float, float]]) -> int:
		if self.event_map_image is None or not polygon:
			return 0

		width = self.event_map_image.get_width()
		height = self.event_map_image.get_height()
		xs = [p[0] for p in polygon]
		ys = [p[1] for p in polygon]
		min_x = max(int(math.floor(min(xs))), 0)
		max_x = min(int(math.ceil(max(xs))), width - 1)
		min_y = max(int(math.floor(min(ys))), 0)
		max_y = min(int(math.ceil(max(ys))), height - 1)

		for px in range(min_x, max_x + 1):
			for py in range(min_y, max_y + 1):
				world_x = px + 0.5
				world_y = py + 0.5
				if not self._point_in_polygon(world_x, world_y, polygon):
					continue

				try:
					dialog_id = self._classify_dialog_color(self.event_map_image.get_at((px, py)))
					if dialog_id != 0:
						return dialog_id
				except Exception:
					continue

		return 0


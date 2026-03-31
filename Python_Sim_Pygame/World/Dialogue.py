import math
import os
from typing import Dict, Optional, Sequence, Tuple

import pygame


class DialogueManager:
	COLOR_DIALOG_1 = (255, 0, 0)
	COLOR_DIALOG_2 = (255, 255, 0)
	COLOR_DIALOG_3 = (255, 0, 255)
	COLOR_TOLERANCE = 24

	DIALOG_COLORS_BY_PHASE: Dict[str, Dict[int, Tuple[int, int, int]]] = {
		"Mapa Tutorial Alertas de Inclinação": {
			1: (255, 0, 0),
			2: (255, 255, 0),
			3: (255, 0, 255),
		},
		"Mapa Tutorial Alertas dos Sensores": {
			1: (255, 255, 0),   # amarelo
			2: (255, 108, 0),   # laranja
			3: (0, 255, 255),   # ciano
			4: (0, 0, 255),     # azul
			5: (144, 0, 255),   # roxo
			6: (255, 0, 255),   # rosa
			7: (150, 255, 0),    
		},
	}

	DIALOG_TEXTS_BY_PHASE: Dict[str, Dict[int, str]] = {
		"Mapa Tutorial Alertas de Inclinação": {
			1: "Esta fase auxiliará você a entender o inclinômetro e os alertas importantes para a operação segura do robô. Quanto mais avermelhado é o piso, mais inclinado é o plano",
			2: "Inclinação de alerta: O inclinômetro detecta quando o robô atinge uma inclinação perigosa.",
			3: "Inclinação crítica: Se a inclinação continuar aumentando, o robô pode tombar. Mantenha o controle para evitar danos.",
		},
		"Mapa Tutorial Alertas dos Sensores": {
			1: "Alerta de temperatura, atenção as luzes do Trafo. Verifique o sistema de resfriamento.",
			2: "Alerta crítico de temperatura, atenção as luzes do Trafo. Verifique o sistema de resfriamento imediatamente.",
			3: "Alerta de bateria fraca, atenção as luzes do Trafo. Recarregue a bateria em breve.",
			4: "Alerta de bateria crítica, atenção as luzes do Trafo. Recarregue a bateria imediatamente.",
			5: "Alerta de pressao, atenção as luzes do Trafo. Verifique os sensores de pressão e o sistema hidráulico.",
			6: "Alerta de pressão crítica, atenção as luzes do Trafo. Verifique os sensores de pressão e o sistema hidráulico imediatamente.",
			7: "Alerta de baixo óleo, atenção as luzes do Trafo. Verifique os níveis de óleo e o sistema de lubrificação.",
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
		phase: str = "Mapa Tutorial Alertas de Inclinação",
	):
		self.project_root = project_root
		self.obstacle_map_path = obstacle_map_path
		self.phase = phase
		self.event_map_image: Optional[pygame.Surface] = self._load_event_map(obstacle_map_size)
		self.last_dialog_id: int = 0
		self.active_dialog_id: int = 0
		self.active_dialog_text: str = ""
		
		# Grid-based spatial hashing para detecção de eventos
		self.grid_cell_size: int = 32  # tamanho de cada célula em pixels
		self.event_grid: Dict[Tuple[int, int], int] = {}  # (grid_x, grid_y) -> dialog_id
		self._build_event_grid()

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
		# Usa grid-based detection para máxima performance
		current_dialog_id = self._detect_dialog_from_grid(polygon)
		phase_dialogs = self.DIALOG_TEXTS_BY_PHASE.get(self.phase, {})

		if current_dialog_id != self.last_dialog_id:
			if current_dialog_id in phase_dialogs:
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

	def draw_dialog_box(self, screen: pygame.Surface, reserved_right: int = 0, reserved_bottom: int = 0) -> None:
		if not self.active_dialog_text:
			return

		sw, sh = screen.get_size()
		avail_w = max(260, int(sw - max(0, reserved_right) - 24))
		bar_h = int(max(0, reserved_bottom))
		pad_x = 14
		pad_y = 8
		text_font = pygame.font.SysFont(None, 22)

		box_w = min(avail_w, max(320, int(avail_w * 0.96)))
		wrap_w = max(80, box_w - (pad_x * 2))
		text_lines = list(self._wrap_text(self.active_dialog_text, text_font, wrap_w))
		line_h = text_font.get_height() + 2

		if bar_h > 0:
			max_h = max(24, bar_h - 12)
			max_lines = max(1, int((max_h - (pad_y * 2)) / max(1, line_h)))
			if len(text_lines) > max_lines:
				text_lines = text_lines[:max_lines]
				if text_lines:
					last = text_lines[-1]
					ellipsis = '...'
					while last and text_font.size(last + ellipsis)[0] > wrap_w:
						last = last[:-1]
					text_lines[-1] = (last + ellipsis) if last else ellipsis

		content_h = len(text_lines) * line_h
		box_h = content_h + (pad_y * 2)

		if bar_h > 0:
			box_x = 12
			box_y = sh - bar_h + max(4, (bar_h - box_h) // 2)
		else:
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

	def _build_event_grid(self) -> None:
		"""Pré-processa o EventMap em uma grid espacial para detecção O(1).
		Divide o mapa em células e armazena o dialog_id encontrado em cada célula.
		"""
		if self.event_map_image is None:
			return

		try:
			width = self.event_map_image.get_width()
			height = self.event_map_image.get_height()
			cell_size = self.grid_cell_size

			# Itera sobre cada célula da grid
			for grid_y in range(0, height, cell_size):
				for grid_x in range(0, width, cell_size):
					# Amostra 4 pontos estratégicos da célula
					sample_points = [
						(grid_x + cell_size // 4, grid_y + cell_size // 4),
						(grid_x + 3 * cell_size // 4, grid_y + cell_size // 4),
						(grid_x + cell_size // 4, grid_y + 3 * cell_size // 4),
						(grid_x + 3 * cell_size // 4, grid_y + 3 * cell_size // 4),
					]

					dialog_id = 0
					for px, py in sample_points:
						if 0 <= px < width and 0 <= py < height:
							try:
								color = self.event_map_image.get_at((int(px), int(py)))
								dialog_id = self._classify_dialog_color(color)
								if dialog_id != 0:
									break
							except Exception:
								pass

					if dialog_id != 0:
						grid_key = (grid_x // cell_size, grid_y // cell_size)
						self.event_grid[grid_key] = dialog_id
		except Exception:
			pass

	def _detect_dialog_from_grid(self, polygon: Sequence[Tuple[float, float]]) -> int:
		"""Detecta diálogo usando grid espacial. Muito mais rápido que varredura pixel-a-pixel."""
		if not self.event_grid or not polygon:
			return 0

		try:
			# Calcula bounding box do polígono
			xs = [p[0] for p in polygon]
			ys = [p[1] for p in polygon]
			min_x = int(math.floor(min(xs)))
			max_x = int(math.ceil(max(xs)))
			min_y = int(math.floor(min(ys)))
			max_y = int(math.ceil(max(ys)))

			cell_size = self.grid_cell_size

			# Converte para coordenadas de grid
			min_grid_x = min_x // cell_size
			max_grid_x = max_x // cell_size
			min_grid_y = min_y // cell_size
			max_grid_y = max_y // cell_size

			# Verifica células ocupadas pelo polígono
			for grid_y in range(min_grid_y, max_grid_y + 1):
				for grid_x in range(min_grid_x, max_grid_x + 1):
					grid_key = (grid_x, grid_y)
					if grid_key in self.event_grid:
						# Encontrou uma célula com evento; valida com pixel-checking
						# Verifica alguns pontos reais para confirmar
						cell_min_x = grid_x * cell_size
						cell_max_x = (grid_x + 1) * cell_size
						cell_min_y = grid_y * cell_size
						cell_max_y = (grid_y + 1) * cell_size

						# Amostra pontos estratégicos na célula
						for py in range(cell_min_y, cell_max_y, max(1, cell_size // 4)):
							for px in range(cell_min_x, cell_max_x, max(1, cell_size // 4)):
								if self._point_in_polygon(float(px) + 0.5, float(py) + 0.5, polygon):
									try:
										if 0 <= px < self.event_map_image.get_width() and 0 <= py < self.event_map_image.get_height():
											color = self.event_map_image.get_at((int(px), int(py)))
											found_id = self._classify_dialog_color(color)
											if found_id != 0:
												return found_id
									except Exception:
										pass

			return 0
		except Exception:
			return 0



	def _classify_dialog_color(self, color) -> int:
		try:
			red = int(color[0])
			green = int(color[1])
			blue = int(color[2])
		except Exception:
			return 0

		phase_colors = self.DIALOG_COLORS_BY_PHASE.get(self.phase)
		if not phase_colors:
			return 0

		for dialog_id, (target_r, target_g, target_b) in phase_colors.items():
			if (
				abs(red - target_r) <= self.COLOR_TOLERANCE
				and abs(green - target_g) <= self.COLOR_TOLERANCE
				and abs(blue - target_b) <= self.COLOR_TOLERANCE
			):
				return dialog_id
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

	def get_available_dialog_ids(self) -> Sequence[int]:
		"""Return sorted dialog IDs actually present in this phase EventMap."""
		try:
			if not self.event_grid:
				return []
			return sorted({int(dialog_id) for dialog_id in self.event_grid.values() if int(dialog_id) > 0})
		except Exception:
			return []


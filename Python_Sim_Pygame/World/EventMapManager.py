"""
EventMapManager - Responsável pela lógica do mapa.
Carrega metadados do EventMap (JSON) e fornece informações sobre spawn points,
colisões e outras configurações específicas do mapa.
"""

import os
import json
import pygame
from typing import Dict, Optional, Tuple, List


class EventMapManager:
    """
    Gerencia todos os aspectos lógicos e físicos de um mapa de eventos.
    
    O EventMap é responsável por:
    - Definir spawn points (player e trafo)
    - Gerenciar colisões
    - Fornecer metadados do mapa
    
    Estrutura:
    - World/EventMap/MapName.json (metadados e configurações)
    - World/EventMap/MapName.png (imagem visual do mapa de eventos)
    - World/Obstacles/MapName.png (imagem visual apenas)
    """
    
    def __init__(self, map_path: str, event_map_dir: str = None):
        """
        Inicializa o EventMapManager para um mapa específico.
        
        Args:
            map_path: Caminho completo da imagem do mapa (ex: World/Obstacles/Map1.png)
            event_map_dir: Diretório do EventMap (default: World/EventMap)
        """
        self.map_path = map_path
        
        # Determinar diretório do EventMap
        if event_map_dir is None:
            project_root = os.path.dirname(os.path.dirname(__file__))
            event_map_dir = os.path.join(project_root, 'World', 'EventMap')
        
        self.event_map_dir = event_map_dir
        
        # Extrair nome do mapa
        self.map_name = os.path.splitext(os.path.basename(map_path))[0]
        
        # Caminhos dos arquivos
        self.json_path = os.path.join(event_map_dir, f'{self.map_name}.json')
        self.event_map_image_path = os.path.join(event_map_dir, f'{self.map_name}.png')
        
        # Dados carregados
        self._metadata: Dict = {}
        self._event_map_image: Optional[pygame.Surface] = None
        self._loaded = False
        
        # Configurações padrão
        self.DEFAULT_PLAYER_SPAWN = (100, 100)
        self.DEFAULT_TRAFO_SPAWN = (200, 100)
        
        # Carregar dados
        self._load()
    
    def _find_green_center(self, img) -> Optional[Tuple[float, float]]:
        """
        Encontra o centróide de pixels verdes (spawn do player).
        Verde é definido como: g >= 200, r < 100, b < 100
        """
        try:
            w, h = img.get_width(), img.get_height()
            totx = toty = count = 0
            for y in range(h):
                for x in range(w):
                    r, g, b, *rest = img.get_at((x, y))
                    if g >= 200 and r < 100 and b < 100:
                        totx += x
                        toty += y
                        count += 1
            if count == 0:
                return None
            return (totx / count, toty / count)
        except Exception:
            return None
    
    def _find_blue_center(self, img) -> Optional[Tuple[float, float]]:
        """
        Encontra o centróide de pixels azuis (spawn do trafo).
        Azul é definido como: b > max(r,g) + 30 and b > 80
        """
        try:
            w, h = img.get_width(), img.get_height()
            totx = toty = count = 0
            for y in range(h):
                for x in range(w):
                    r, g, b, *rest = img.get_at((x, y))
                    if b > max(r, g) + 30 and b > 80:
                        totx += x
                        toty += y
                        count += 1
            if count == 0:
                return None
            return (totx / count, toty / count)
        except Exception:
            return None

    def _find_yellow_completion_zone(self, img) -> Optional[Dict[str, int]]:
        """
        Encontra a área amarela usada como zona de conclusão da fase.

        A zona é detectada pelos pixels amarelos mais fortes do EventMap.
        Se houver um retângulo amarelo desenhado no mapa, isso devolve a caixa
        delimitadora dele para uso como área de conclusão.
        """
        try:
            w, h = img.get_width(), img.get_height()
            min_x = w
            min_y = h
            max_x = -1
            max_y = -1
            count = 0

            for y in range(h):
                for x in range(w):
                    r, g, b, *rest = img.get_at((x, y))
                    if r >= 220 and g >= 200 and b <= 120 and abs(int(r) - int(g)) <= 80:
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                        count += 1

            if count == 0 or max_x < min_x or max_y < min_y:
                return None

            return {
                'x': int(min_x),
                'y': int(min_y),
                'width': int(max_x - min_x + 1),
                'height': int(max_y - min_y + 1),
            }
        except Exception:
            return None
    
    def _auto_discover_spawns(self) -> Dict:
        """
        Automaticamente descobre spawn points lendo a imagem do EventMap.
        Se a imagem não existe, usa defaults.
        
        Returns:
            Dicionário com spawn points descobertos
        """
        player_spawn = None
        trafo_spawn = None
        completion_zone = None
        
        # Tentar carregar imagem do EventMap para descobrir spawns
        try:
            if os.path.exists(self.event_map_image_path):
                # Garantir que pygame.display está inicializado
                if pygame.display.get_surface() is None:
                    try:
                        pygame.display.set_mode((1, 1))
                    except Exception:
                        pass
                
                img = pygame.image.load(self.event_map_image_path).convert()
                
                green = self._find_green_center(img)
                blue = self._find_blue_center(img)
                
                if green:
                    player_spawn = list(green)
                if blue:
                    trafo_spawn = list(blue)
                completion_zone = self._find_yellow_completion_zone(img)
                
                # Log para debug
                msg = f"[EventMapManager] Auto-descoberto para '{self.map_name}': "
                if green:
                    msg += f"player_spawn={green} "
                if blue:
                    msg += f"trafo_spawn={blue}"
                if completion_zone:
                    msg += f" completion_zone={completion_zone}"
                if green or blue or completion_zone:
                    print(msg)
        except Exception as e:
            print(f"[EventMapManager] Erro ao auto-descobrir spawns: {e}")
        
        # Usar defaults se não descobriu
        if not player_spawn:
            player_spawn = list(self.DEFAULT_PLAYER_SPAWN)
        if not trafo_spawn:
            trafo_spawn = list(self.DEFAULT_TRAFO_SPAWN)
        
        return {
            'map_name': self.map_name,
            'player_spawn': player_spawn,
            'trafo_spawn': trafo_spawn,
            'metadata': {'auto_generated': True},
            'completion_zone': completion_zone,
            'phase_config': {
                'spawn_trafo': True,
                'force_hardcore_mode': False,
                'is_tutorial': False,
                'available_robot_modes': ['straight', 'curve', 'pivotal', 'diagonal'],
                'difficulty': 'medium'
            }
        }

    def _ensure_completion_zone(self) -> bool:
        """
        Garante que a completion_zone exista quando o EventMap tiver a área amarela.

        Returns:
            True se o metadata foi alterado, False caso contrário.
        """
        if self._metadata.get('completion_zone'):
            return False

        try:
            if not os.path.exists(self.event_map_image_path):
                return False

            if pygame.display.get_surface() is None:
                try:
                    pygame.display.set_mode((1, 1))
                except Exception:
                    pass

            img = pygame.image.load(self.event_map_image_path).convert()
            completion_zone = self._find_yellow_completion_zone(img)
            if completion_zone:
                self._metadata['completion_zone'] = completion_zone
                print(f"[EventMapManager] Zona de conclusão descoberta para '{self.map_name}': {completion_zone}")
                return True
        except Exception as e:
            print(f"[EventMapManager] Erro ao descobrir completion_zone: {e}")

        return False
    
    def _load(self) -> None:
        """
        Carrega os metadados do EventMap (JSON).
        Se não existir JSON, tenta auto-descobrir spawns da imagem do EventMap
        e cria o JSON automaticamente.
        """
        try:
            if os.path.exists(self.json_path):
                # JSON existe, carregar normalmente
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                self._loaded = True
                print(f"[EventMapManager] Carregado JSON: {self.json_path}")
                if self._ensure_completion_zone():
                    self.save_metadata()
            else:
                # JSON não existe, tentar auto-descobrir spawns
                print(f"[EventMapManager] JSON não encontrado para '{self.map_name}', auto-descobrindo...")
                self._metadata = self._auto_discover_spawns()
                
                # Salvar JSON auto-gerado para próximas execuções
                try:
                    self.save_metadata()
                    self._loaded = True
                    print(f"[EventMapManager] JSON auto-gerado e salvo: {self.json_path}")
                except Exception as e:
                    print(f"[EventMapManager] Erro ao salvar JSON auto-gerado: {e}")
                    self._loaded = False
        except Exception as e:
            print(f"[EventMapManager] Erro ao carregar JSON do map '{self.map_name}': {e}")
            # Fallback: usar defaults
            self._metadata = {
                'map_name': self.map_name,
                'player_spawn': list(self.DEFAULT_PLAYER_SPAWN),
                'trafo_spawn': list(self.DEFAULT_TRAFO_SPAWN),
                'metadata': {'fallback': True}
            }
    
    def get_player_spawn(self) -> Tuple[float, float]:
        """
        Retorna a posição de spawn do player.
        
        Returns:
            (x, y) coordenadas do spawn point
        """
        spawn = self._metadata.get('player_spawn')
        if spawn and isinstance(spawn, (list, tuple)) and len(spawn) >= 2:
            return (float(spawn[0]), float(spawn[1]))
        return self.DEFAULT_PLAYER_SPAWN
    
    def get_trafo_spawn(self) -> Tuple[float, float]:
        """
        Retorna a posição de spawn do trafo.
        
        Returns:
            (x, y) coordenadas do spawn point
        """
        spawn = self._metadata.get('trafo_spawn')
        if spawn and isinstance(spawn, (list, tuple)) and len(spawn) >= 2:
            return (float(spawn[0]), float(spawn[1]))
        return self.DEFAULT_TRAFO_SPAWN
    
    def load_event_map_image(self) -> Optional[pygame.Surface]:
        """
        Carrega a imagem visual do EventMap (usada para lógica visual/diagnóstico).
        
        Returns:
            pygame.Surface da imagem do EventMap ou None se não existir
        """
        if self._event_map_image is not None:
            return self._event_map_image
        
        try:
            if os.path.exists(self.event_map_image_path):
                self._event_map_image = pygame.image.load(self.event_map_image_path).convert()
                return self._event_map_image
        except Exception as e:
            print(f"[EventMapManager] Erro ao carregar imagem do EventMap: {e}")
        
        return None
    
    def get_metadata(self) -> Dict:
        """
        Retorna todos os metadados do EventMap.
        
        Returns:
            Dicionário com metadados específicos do mapa
        """
        return self._metadata.get('metadata', {})
    
    def has_trafo_spawn(self) -> bool:
        """
        Retorna se o trafo deve ser spawned neste mapa.
        
        Returns:
            True se deve spawnar trafo, False caso contrário
        """
        config = self._metadata.get('phase_config', {})
        return config.get('spawn_trafo', True)  # Default: True (sempre tinha trafo)
    
    def is_hardcore_mode_forced(self) -> bool:
        """
        Retorna se o modo hardcore é forçado (não pode mudar durante o jogo).
        
        Returns:
            True se o modo hardcore é forçado
        """
        config = self._metadata.get('phase_config', {})
        return config.get('force_hardcore_mode', False)  # Default: False (pode escolher)
    
    def is_tutorial_mode(self) -> bool:
        """
        Retorna se este mapa é um tutorial.
        
        Returns:
            True se é um tutorial, False caso contrário
        """
        config = self._metadata.get('phase_config', {})
        return config.get('is_tutorial', False)  # Default: False
    
    def get_available_robot_modes(self) -> list:
        """
        Retorna quais modos de operação do robô estão disponíveis nesta fase.
        
        Modos disponíveis: 'straight', 'curve', 'pivotal', 'diagonal'
        
        Returns:
            Lista de modos de operação disponíveis
        """
        config = self._metadata.get('phase_config', {})
        # Default: todos os modos disponíveis
        return config.get('available_robot_modes', ['straight', 'curve', 'pivotal', 'diagonal'])
    
    def get_phase_config(self) -> Dict:
        """
        Retorna toda a configuração específica da fase.
        
        Inclui:
        - spawn_trafo: bool (se deve spawnar trafo)
        - force_hardcore_mode: bool (se modo hardcore é obrigatório)
        - is_tutorial: bool (se é um tutorial)
        - available_robot_modes: list (modos de operação do robô disponíveis)
        - difficulty: str (dificuldade)
        - description: str (descrição)
        
        Returns:
            Dicionário com configurações da fase
        """
        return self._metadata.get('phase_config', {})

    def get_completion_zone(self) -> Optional[pygame.Rect]:
        """
        Retorna a zona retangular de conclusão da fase, se existir.

        A área é descrita no JSON como um retângulo detectado na cor amarela.
        """
        zone = self._metadata.get('completion_zone')
        if not zone:
            return None

        try:
            if isinstance(zone, dict):
                x = int(zone.get('x', 0))
                y = int(zone.get('y', 0))
                width = int(zone.get('width', 0))
                height = int(zone.get('height', 0))
                if width > 0 and height > 0:
                    return pygame.Rect(x, y, width, height)
            elif isinstance(zone, (list, tuple)) and len(zone) >= 4:
                x, y, width, height = zone[:4]
                width = int(width)
                height = int(height)
                if width > 0 and height > 0:
                    return pygame.Rect(int(x), int(y), width, height)
        except Exception:
            return None

        return None

    def has_completion_zone(self) -> bool:
        """Retorna se o EventMap tem uma área de conclusão definida."""
        return self.get_completion_zone() is not None
    
    def set_player_spawn(self, x: float, y: float) -> None:
        """
        Define a posição de spawn do player.
        
        Args:
            x, y: Coordenadas do novo spawn point
        """
        self._metadata['player_spawn'] = [float(x), float(y)]
    
    def set_trafo_spawn(self, x: float, y: float) -> None:
        """
        Define a posição de spawn do trafo.
        
        Args:
            x, y: Coordenadas do novo spawn point
        """
        self._metadata['trafo_spawn'] = [float(x), float(y)]
    
    def save_metadata(self) -> bool:
        """
        Salva os metadados atuais em JSON.
        
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            os.makedirs(self.event_map_dir, exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[EventMapManager] Erro ao salvar JSON: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Verifica se o EventMap foi carregado a partir de um arquivo JSON."""
        return self._loaded
    
    def __repr__(self) -> str:
        return (f"<EventMapManager map='{self.map_name}' "
                f"player_spawn={self.get_player_spawn()} "
                f"trafo_spawn={self.get_trafo_spawn()}>")

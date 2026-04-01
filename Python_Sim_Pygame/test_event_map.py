"""
Script de teste do EventMapManager
"""

from World.EventMapManager import EventMapManager
import os

# Testar com um dos mapas tutoriais
event_map_dir = os.path.join(os.getcwd(), 'World', 'EventMap')
map_name = "Mapa Tutorial Alertas de Inclinação"

# Criar um caminho de mapa fake para o EventMapManager
fake_map_path = os.path.join(os.getcwd(), 'World', 'Obstacles', f'{map_name}.png')

event_map = EventMapManager(fake_map_path, event_map_dir)

print(f"EventMap carregado: {event_map}")
print(f"Player spawn: {event_map.get_player_spawn()}")
print(f"Trafo spawn: {event_map.get_trafo_spawn()}")
print(f"É um JSON carregado? {event_map.is_loaded()}")
print(f"Metadados: {event_map.get_metadata()}")
print("\n✓ EventMapManager funcionando corretamente!")

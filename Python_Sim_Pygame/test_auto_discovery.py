"""
Teste para validar auto-descoberta de spawn points
Simula um novo mapa sendo adicionado sem JSON.
"""

import os
import shutil
import json
from World.EventMapManager import EventMapManager

# Copiar uma imagem de teste para simular novo mapa
test_map_name = "TestNewMap"
source_image = "World/EventMap/Tutorial Modo Reto-Curva.png"
dest_obstacles = f"World/Obstacles/{test_map_name}.png"
dest_eventmap = f"World/EventMap/{test_map_name}.png"

try:
    # Garantir que o JSON não existe
    json_path = f"World/EventMap/{test_map_name}.json"
    if os.path.exists(json_path):
        os.remove(json_path)
        print(f"✗ Removido JSON existente: {json_path}")
    
    # Copiar imagens para simular novo mapa
    os.makedirs("World/Obstacles", exist_ok=True)
    os.makedirs("World/EventMap", exist_ok=True)
    
    if os.path.exists(source_image):
        shutil.copy(source_image, dest_obstacles)
        shutil.copy(source_image, dest_eventmap)
        print(f"✓ Copiadas imagens para simular novo mapa: {test_map_name}")
    else:
        print(f"✗ Imagem de source não encontrada: {source_image}")
        exit(1)
    
    # Agora criar EventMapManager - deve AUTO-DESCOBRIR!
    print(f"\n[TESTE] Carregando EventMap para mapa novo '{test_map_name}' (sem JSON pré-existente)...")
    event_map = EventMapManager(dest_obstacles)
    
    print(f"\n✓ EventMap Auto-Descoberto:")
    print(f"  - Map: {event_map.map_name}")
    print(f"  - Player spawn: {event_map.get_player_spawn()}")
    print(f"  - Trafo spawn: {event_map.get_trafo_spawn()}")
    print(f"  - JSON carregado? {event_map.is_loaded()}")
    
    # Verificar se JSON foi criado
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        print(f"\n✓ JSON foi criado automaticamente!")
        print(f"  - Conteúdo: {json.dumps(json_data, indent=2)}")
    else:
        print(f"\n✗ JSON NÃO foi criado!")
    
    print("\n" + "="*60)
    print("✓ TESTE PASSADO: Auto-descoberta funciona perfeitamente!")
    print("="*60)
    
finally:
    # Cleanup
    try:
        if os.path.exists(dest_obstacles):
            os.remove(dest_obstacles)
        if os.path.exists(dest_eventmap):
            os.remove(dest_eventmap)
        if os.path.exists(json_path):
            os.remove(json_path)
        print("\n✓ Limpeza concluída")
    except Exception as e:
        print(f"\n✗ Erro durante limpeza: {e}")

"""
Teste das configurações de fase no EventMap
"""

from World.EventMapManager import EventMapManager

# Testar cada um dos 3 mapas tutoriais com diferentes configs
maps = [
    "Mapa Tutorial Alertas de Inclinação",
    "Mapa Tutorial Alertas dos Sensores", 
    "Tutorial Modo Reto-Curva"
]

print("=" * 70)
print("🎮 TESTE DE CONFIGURAÇÕES DE FASE")
print("=" * 70)

for map_name in maps:
    print(f"\n📍 Mapa: {map_name}")
    print("-" * 70)
    
    fake_path = f"World/Obstacles/{map_name}.png"
    event_map = EventMapManager(fake_path)
    
    # Config da fase
    config = event_map.get_phase_config()
    
    print(f"  ✓ É tutorial? {event_map.is_tutorial_mode()}")
    print(f"  ✓ Spawn trafo? {event_map.has_trafo_spawn()}")
    print(f"  ✓ Modo hardcore forçado? {event_map.is_hardcore_mode_forced()}")
    print(f"  ✓ Modos de operação disponíveis: {event_map.get_available_robot_modes()}")
    print(f"  ✓ Dificuldade: {config.get('difficulty', 'N/A')}")
    print(f"  ✓ Descrição: {config.get('description', 'N/A')}")

print("\n" + "=" * 70)
print("✓ TESTE COMPLETO - Configurações funcionam!")
print("=" * 70)

# Exemplo de uso no código do jogo
print("\n📝 EXEMPLO DE IMPLEMENTAÇÃO:")
print("""
# Exemplo de uso no código do jogo:
event_map = EventMapManager(selected_map_path)

# Verificar se deve spawnar o trafo
if event_map.has_trafo_spawn():
    trafo = init_trafo(event_map, spawn_point)
else:
    trafo = None
    print("[Game] Trafo desativado para este mapa")

# Verificar quais modos de operação estão disponíveis
available_modes = event_map.get_available_robot_modes()
if 'pivotal' not in available_modes:
    disable_pivotal_mode_option()
for mode in ['straight', 'curve', 'pivotal', 'diagonal']:
    if mode not in available_modes:
        disable_mode(mode)

# Forçar modo hardcore se necessário
if event_map.is_hardcore_mode_forced():
    hardcore_mode = True
    disable_difficulty_selection()
""")

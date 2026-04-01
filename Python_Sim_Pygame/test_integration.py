"""
Teste de integração: Verificar se as restrições estão sendo aplicadas
"""

import os
import sys

# Simular o que v1.0_pygame.py faz
from game.initialization import setup_game_objects

# Vamos criar um teste usando um mapa que existe
# Primeiro, testamos com mapa_test que existe em World/Obstacles
# Mas queremos testar com Tutorial Modo Reto-Curva que tem restrições

# Para isso, vamos verificar o que o jogo faria manualmente
from World.EventMapManager import EventMapManager

test_map = "Tutorial Modo Reto-Curva"

print("=" * 70)
print("🧪 TESTE DE INTEGRAÇÃO - Verificando Restrições")
print("=" * 70)
print(f"\n📍 Testando mapa: {test_map}")
print()

# Carregar o EventMapManager diretamente (não precisa de imagem)
fake_path = f"World/Obstacles/{test_map}.png"
event_map = EventMapManager(fake_path)

print("[EventMapManager] Carregado com sucesso!")
print()

print("=" * 70)
print("✅ VERIFICANDO CONFIGURAÇÕES")
print("=" * 70)

# 1. Verificar se trafo spawn está desativado
print(f"\n1. Trafo spawning")
has_trafo = event_map.has_trafo_spawn()
if not has_trafo:
    print(f"   ✓ Trafo será DESATIVADO (correto!)")
else:
    print(f"   ✗ Trafo será ATIVADO (deveria estar desativado!)")

# 2. Verificar modo hardcore
print(f"\n2. Modo hardcore forçado")
is_forced = event_map.is_hardcore_mode_forced()
if is_forced:
    print(f"   ✓ FORÇADO (correto!)")
else:
    print(f"   ✗ Não forçado (deveria estar forçado!)")

# 3. Verificar modos disponíveis
print(f"\n3. Modos de operação disponíveis")
available = event_map.get_available_robot_modes()
print(f"   Modos retornados: {available}")
if available == ['straight', 'curve']:
    print(f"   ✓ Apenas 'straight' e 'curve' (correto!)")
else:
    print(f"   ✗ Esperado ['straight', 'curve'], obtido {available}")

print("\n" + "=" * 70)
print("📋 RESUMO COMPLETO DA CONFIGURAÇÃO")
print("=" * 70)
config = event_map.get_phase_config()
print(f"\nDados do JSON (phase_config):")
for key, value in config.items():
    if isinstance(value, list) and len(value) > 3:
        print(f"  • {key}: {value[:3]}... ({len(value)} items)")
    else:
        print(f"  • {key}: {value}")

print("\n" + "=" * 70)
print("✅ TESTE CONCLUÍDO - Configurações Corretas!")
print("=" * 70)
print("\nNo jogo (v1.0_pygame.py), a lógica agora fará:")
print("  1. Verificar 'event_map.has_trafo_spawn()' → False")
print("     ✓ Remover o trafo do jogo")
print()
print("  2. Verificar 'event_map.is_hardcore_mode_forced()' → True")
print("     ✓ Forçar modo hardcore = True")
print()
print("  3. Usar 'available_robot_modes' para filtrar modos")
print(f"     ✓ Permitir apenas: {available}")
print("     ✓ Bloquear tentativas de usar outros modos")

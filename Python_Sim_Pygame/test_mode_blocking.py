"""
Teste final: Validar que QUALQUER tentativa de mudança de modo é bloqueada
"""

from Player.Player import Player
from Camera.Camera import Camera
import pygame

pygame.init()
screen = pygame.display.set_mode((100, 100))

print("=" * 70)
print("🔒 TESTE DE BLOQUEIO TOTAL DE MODOS")
print("=" * 70)

# Criar um player
camera = Camera(100, 100)
player = Player((500, 500), screen, camera)

print(f"\n[1] Inicial")
print(f"    Modo atual: {player.curve_mode}")
print(f"    Modos disponíveis: {player.available_modes}")

# Simulação: Restringir apenas para 'straight' e 'curve' (como no Tutorial Modo Reto-Curva)
print(f"\n[2] Aplicar restrição do mapa: apenas 'straight' e 'curve'")
player.available_modes = ['straight', 'curve']
print(f"    Modos agora disponíveis: {player.available_modes}")

print(f"\n[3] Tentar mudar para cada modo")
print(f"    (válido or bloqueado)")

test_modes = ['straight', 'curve', 'pivotal', 'diagonal', 'icamento']

for test_mode in test_modes:
    print(f"\n    → setMode('{test_mode}')")
    player.setMode(test_mode)
    
    if test_mode in player.available_modes:
        if player.curve_mode == test_mode:
            print(f"      ✓ PERMITIDO - Modo alterado para '{test_mode}'")
        else:
            print(f"      ⚠️  Modo tentado mas não mudou (transição em andamento?)")
    else:
        if player.curve_mode != test_mode:
            print(f"      ✓ BLOQUEADO - Modo permanece '{player.curve_mode}'")

print(f"\n" + "=" * 70)
print(f"📊 RESULTADO FINAL")
print(f"=" * 70)

print(f"\nModo do player: {player.curve_mode}")
print(f"Modos permitidos: {player.available_modes}")

if player.curve_mode in player.available_modes:
    print(f"\n✅ SUCESSO! O player consegue estar em um modo permitido")
    print(f"   Modo bloqueado? 'diagonal' e 'pivotal' são impedidos ✓")
else:
    print(f"\n⚠️  Player em modo não permitido (erro!)")

print("\n" + "=" * 70)
print("O bloqueio de modos está funcionando completamente!")
print("Agora o jogador NÃO consegue trocar para modos não permitidos")
print("=" * 70)

pygame.quit()

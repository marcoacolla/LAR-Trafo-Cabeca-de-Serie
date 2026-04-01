"""
Script auxiliar para descobrir spawn points automaticamente das imagens do EventMap.
Lê as cores verdes e azuis das imagens e atualiza os JSONs correspondentes.

Uso:
    python discover_event_map_spawns.py
"""

import os
import json
import pygame
from typing import Tuple, Optional


def find_green_center(img) -> Optional[Tuple[float, float]]:
    """
    Finds the centroid of green pixels (player spawn point).
    Green is defined as: g >= 200, r < 100, b < 100
    """
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


def find_blue_center(img) -> Optional[Tuple[float, float]]:
    """
    Finds the centroid of blue pixels (trafo spawn point).
    Blue is defined as: b > max(r,g) + 30 and b > 80
    """
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


def discover_and_update_event_maps():
    """Descobre spawn points em todas as imagens do EventMap e atualiza os JSONs."""
    
    # Inicializar pygame com display small
    pygame.init()
    pygame.display.set_mode((1, 1))  # Pequena tela para permitir .convert()
    
    # Caminho para o diretório EventMap
    script_dir = os.path.dirname(__file__)
    event_map_dir = os.path.join(script_dir, 'World', 'EventMap')
    
    if not os.path.exists(event_map_dir):
        print(f"Diretório EventMap não encontrado: {event_map_dir}")
        return
    
    # Iterar sobre todos os PNGs no EventMap
    for filename in os.listdir(event_map_dir):
        if not filename.endswith('.png'):
            continue
        
        image_path = os.path.join(event_map_dir, filename)
        json_name = os.path.splitext(filename)[0] + '.json'
        json_path = os.path.join(event_map_dir, json_name)
        
        print(f"\nProcessando: {filename}")
        
        try:
            # Carregar imagem
            img = pygame.image.load(image_path).convert()
            
            # Descobrir spawn points
            green = find_green_center(img)
            blue = find_blue_center(img)
            
            # Criar/atualizar JSON
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    'map_name': os.path.splitext(filename)[0],
                    'metadata': {'description': '', 'tutorial': True}
                }
            
            # Atualizar spawn points
            if green:
                data['player_spawn'] = [float(green[0]), float(green[1])]
                print(f"  ✓ Player spawn encontrado: {green}")
            else:
                print(f"  ✗ Sem pixel verde (player spawn)")
            
            if blue:
                data['trafo_spawn'] = [float(blue[0]), float(blue[1])]
                print(f"  ✓ Trafo spawn encontrado: {blue}")
            else:
                print(f"  ✗ Sem pixel azul (trafo spawn)")
            
            # Salvar JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  → Salvo em: {json_name}")
        
        except Exception as e:
            print(f"  ✗ Erro: {e}")
    
    print("\n✓ Processamento concluído!")


if __name__ == '__main__':
    discover_and_update_event_maps()

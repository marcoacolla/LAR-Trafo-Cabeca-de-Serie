"""
Accelerometer module - Handles accelerometer simulation based on red areas on the map.
Simulates inclinometer readings for safety alerts.
"""

import pygame
from .config import (
    ACCELEROMETER_MAX_VALUE,
    ACCELEROMETER_RED_MIN_DIFF,
    ACCELEROMETER_GB_MAX_DIFF,
    ACCELEROMETER_SAMPLES,
    ICAMENTO_MAX_MM,
    ICAMENTO_ALERTA_THRESHOLD_MM,
    ICAMENTO_CRITICO_THRESHOLD_MM,
)


def calculate_accelerometer_value(player, map_image):
    """
    Calcula o valor do acelerômetro baseado na intensidade de vermelho puro
    na posição do robô. Detecta especificamente tons avermelhados (R >> G, B)
    e não branco ou outras cores. Retorna um valor de 0 a ACCELEROMETER_MAX_VALUE.
    """
    try:
        px, py = player.getPosition()
        map_x = int(px)
        map_y = int(py)
        
        # Verifica limites do mapa
        if (map_x < 0 or map_x >= map_image.get_width() or 
            map_y < 0 or map_y >= map_image.get_height()):
            return 0
        
        # Amostra a cor central e em alguns pontos ao redor
        sample_points = [
            (map_x, map_y),  # centro
            (map_x + 15, map_y),  # direita
            (map_x - 15, map_y),  # esquerda
            (map_x, map_y + 15),  # frente
            (map_x, map_y - 15),  # trás
        ]
        
        # Coleta valores de "avermelhamento" de todas as amostras
        red_intensities = []
        for sx, sy in sample_points:
            if 0 <= sx < map_image.get_width() and 0 <= sy < map_image.get_height():
                try:
                    color = map_image.get_at((sx, sy))
                    r, g, b = color[0], color[1], color[2]
                    
                    # Detecta vermelho: R deve ser muito maior que G e B
                    # G e B devem ser aproximadamente iguais (para evitar cores misturadas)
                    max_gb = max(g, b)
                    diff_gb = abs(g - b)
                    
                    # Calcula quanto de "puro vermelho" existe
                    # Quanto maior R - max(G,B), mais vermelho puro é
                    red_diff = r - max_gb
                    
                    # Só conta como vermelho se atender aos critérios
                    if red_diff >= ACCELEROMETER_RED_MIN_DIFF and diff_gb <= ACCELEROMETER_GB_MAX_DIFF:
                        red_intensities.append(red_diff)
                    else:
                        red_intensities.append(0)
                except Exception:
                    pass
        
        if not red_intensities or all(x == 0 for x in red_intensities):
            return 0
        
        # Usa a média dos valores de "avermelhamento"
        avg_red_intensity = sum(red_intensities) / len(red_intensities)
        
        # Mapeia de [0, 255] para [0, ACCELEROMETER_MAX_VALUE]
        # A intensidade máxima é quando R=255 e G=B=0, dando red_diff=255
        normalized = min(1.0, avg_red_intensity / 255.0)
        accel_value = int(normalized * ACCELEROMETER_MAX_VALUE)
        
        return min(ACCELEROMETER_MAX_VALUE, max(0, accel_value))
    except Exception:
        return 0


def get_alert_mode_from_accelerometer(accelerometer_value):
    """
    Determine alert mode (alerta/critico) based on accelerometer reading.
    Returns (mode, hz, level) where level is 0=none, 1=alerta, 2=critico.
    """
    if accelerometer_value > 25:
        return ('critico', 0.5, 2)
    elif accelerometer_value > 15:
        return ('alerta', 0.5, 1)
    return (None, 0.0, 0)


def get_icamento_mm(player):
    """
    Get the current icamento (lifting) value in millimeters (0-500).
    """
    try:
        icamento_mm = int(max(0.0, min(1.0, float(getattr(player, 'icamento_cursor', 0.0)))) * ICAMENTO_MAX_MM)
        return icamento_mm
    except Exception:
        return 0


def get_alert_mode_from_icamento(icamento_mm):
    """
    Determine alert mode based on icamento (lifting) value.
    Returns (mode, hz, level) where level is 0=none, 1=alerta, 2=critico.
    """
    if icamento_mm > ICAMENTO_CRITICO_THRESHOLD_MM:
        return ('critico', 4.0, 2)
    elif icamento_mm > ICAMENTO_ALERTA_THRESHOLD_MM:
        return ('alerta', 4.0, 1)
    return (None, 0.0, 0)


def can_pickup_trafo(player):
    """
    Check if player is in conditions to pickup the trafo.
    Only allow pickup when in 'icamento' mode and cursor >= 250 mm.
    """
    try:
        icamento_mm = get_icamento_mm(player)
        if getattr(player, 'curve_mode', None) == 'icamento' and icamento_mm >= 250:
            return True
    except Exception:
        pass
    return False


def determine_light_mode(accelerometer_value, icamento_mm, dialogue_manager):
    """
    Determine which light mode to use based on all active rules.
    Criticality: critico > alerta. In case of tie, use higher Hz.
    
    Returns:
        tuple: (chosen_mode, chosen_hz, chosen_level, fixed_light_mode)
        where fixed_light_mode is None | 'alerta' | 'critico'
    """
    chosen_mode = None
    chosen_hz = 0.0
    chosen_level = 0  # 0=none, 1=alerta, 2=critico
    fixed_light_mode = None

    # Regra 1: inclinação
    accel_mode, accel_hz, accel_level = get_alert_mode_from_accelerometer(accelerometer_value)
    if accel_level > 0:
        chosen_mode = accel_mode
        chosen_hz = accel_hz
        chosen_level = accel_level

    # Regra 2: içamento em mm
    ic_mode, ic_hz, ic_level = get_alert_mode_from_icamento(icamento_mm)
    if (ic_level > chosen_level) or (ic_level == chosen_level and ic_hz > chosen_hz):
        chosen_mode = ic_mode
        chosen_hz = ic_hz
        chosen_level = ic_level

    # Regra 3 (fase de sensores): alertas guiados pelo diálogo ativo
    # 1: amarelo 1Hz | 2: vermelho 1Hz | 3: amarelo 6Hz | 4: vermelho 6Hz
    # 5: amarelo 2Hz | 6: vermelho 2Hz | 7: amarelo fixo | 8: vermelho fixo
    try:
        current_phase = str(getattr(dialogue_manager, 'phase', ''))
        is_sensor_phase = (current_phase == 'Mapa Tutorial Alertas dos Sensores')
        active_dialog_id = int(getattr(dialogue_manager, 'active_dialog_id', 0))

        if is_sensor_phase:
            if active_dialog_id == 1:
                chosen_mode, chosen_hz, chosen_level = 'alerta', 1.0, 1
            elif active_dialog_id == 2:
                chosen_mode, chosen_hz, chosen_level = 'critico', 1.0, 2
            elif active_dialog_id == 3:
                chosen_mode, chosen_hz, chosen_level = 'alerta', 6.0, 1
            elif active_dialog_id == 4:
                chosen_mode, chosen_hz, chosen_level = 'critico', 6.0, 2
            elif active_dialog_id == 5:
                chosen_mode, chosen_hz, chosen_level = 'alerta', 2.0, 1
            elif active_dialog_id == 6:
                chosen_mode, chosen_hz, chosen_level = 'critico', 2.0, 2
            elif active_dialog_id == 7:
                fixed_light_mode = 'alerta'
            elif active_dialog_id == 8:
                fixed_light_mode = 'critico'
    except Exception:
        pass

    return chosen_mode, chosen_hz, chosen_level, fixed_light_mode

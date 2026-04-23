"""
Configuration module - Central place for all constants and settings.
Increases maintainability by having all magic numbers and settings in one place.
"""

# Display configuration
PANEL_WIDTH = 300  # largura padrão do painel lateral (personalizável)
BOTTOM_BAR_HEIGHT = 92  # barra inferior
BASE_SCREEN_W = 800
BASE_SCREEN_H = 600
SCREEN_W = BASE_SCREEN_W + PANEL_WIDTH
SCREEN_H = BASE_SCREEN_H

# Game settings
DEFAULT_HARDCORE_MODE = False
DEFAULT_FULLSCREEN_MODE = False
DEFAULT_TTC_CONTROL = False

# Player settings
DEFAULT_SPAWN_POINT = (200, 200)

# Camera settings
MIN_CAMERA_SCALE = 0.25
MAX_CAMERA_SCALE = 4.0
ZOOM_SPEED = 0.04
DEFAULT_CAMERA_SCALE = 1.0

# Trafo settings
TRAFO_SIZE = 60
TRAFO_PICKUP_DISPLAY_MS = 1500
TRAFO_DEATH_LOCK_MS = 500

# Accelerometer settings (simulates inclination based on red areas on map)
ACCELEROMETER_MAX_VALUE = 30  # máximo valor do acelerômetro (simula 90 graus)
ACCELEROMETER_RED_MIN_DIFF = 80  # diferença mínima entre R e max(G,B) para detectar vermelho
ACCELEROMETER_GB_MAX_DIFF = 30   # diferença máxima entre G e B (para G e B serem "iguais")
ACCELEROMETER_SAMPLES = 4  # número de pontos ao redor do robô para amostrar

# Icamento (lifting) settings
ICAMENTO_MAX_MM = 500
ICAMENTO_PICKUP_THRESHOLD_MM = 250
ICAMENTO_ALERTA_THRESHOLD_MM = 200
ICAMENTO_CRITICO_THRESHOLD_MM = 400

# Game loop settings
TARGET_FPS = 60

# UI Colors
COLOR_BG_LIGHT = (236, 243, 252)
COLOR_BORDER = (190, 206, 225)
COLOR_BORDER_DARK = (150, 168, 192)
COLOR_SHADOW = (70, 78, 92)
COLOR_SHADOW_ALPHA = 72
COLOR_SKY_BLUE = (220, 230, 255)

# Movement settings
CAN_MOVEMENT_NEUTRAL = 30000  # neutral position for CAN movement (0-60000)
CAN_MOVEMENT_MAX = 60000
CAN_MOVEMENT_MIN = 0

# Control modes
CONTROL_MODE_KEYBOARD = 'keyboard'
CONTROL_MODE_JOYSTICK = 'joystick'

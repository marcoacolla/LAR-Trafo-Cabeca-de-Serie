# ⚙️ Configurações de Fase (phase_config)

## O que são Configurações de Fase?

A seção `phase_config` no JSON de cada mapa define características específicas daquela fase/nível:

- Se vai spawnar o trafo ou não
- Se o modo hardcore é forçado (e não pode mudar)
- Quais modos de operação do robô estão disponíveis (straight, curve, pivotal, diagonal)
- Dificuldade e descrição

## Estrutura Completa

```json
{
  "map_name": "Nome do Mapa",
  "player_spawn": [x, y],
  "trafo_spawn": [x, y],
  "metadata": {
    "description": "Descrição geral"
  },
  "phase_config": {
    "is_tutorial": boolean,
    "spawn_trafo": boolean,
    "force_hardcore_mode": boolean,
    "available_robot_modes": ["straight", "curve", "pivotal", "diagonal"],
    "difficulty": "easy|medium|hard",
    "description": "Descrição específica da fase"
  }
}
```

## Campos Explicados

### `is_tutorial` (boolean, default: false)
```json
"is_tutorial": true
```
- Marca o mapa como tutorial
- Pode desabilitar certos elementos da UI
- Exemplo: Tutorial introdutório

### `spawn_trafo` (boolean, default: true)
```json
"spawn_trafo": false
```
- **true**: Trafo aparece no mapa
- **false**: SEM trafo (ex: tutorial focado em controles)
- Exemplo: Fase de aprendizado de sensores sem distração

### `force_hardcore_mode` (boolean, default: false)
```json
"force_hardcore_mode": true
```
- **true**: Modo hardcore OBRIGATÓRIO, não pode mudar
- **false**: Jogador escolhe a dificuldade
- Exemplo: Screenshot/demo que precisa de um modo específico

### `available_robot_modes` (array, default: ["straight", "curve", "pivotal", "diagonal"])
```json
"available_robot_modes": ["straight", "curve"]
```
- Lista de modos de operação do robô disponíveis nesta fase
- O robô pode operar em 4 modos diferentes:
  - **straight**: Movimento reto apenas
  - **curve**: Movimento em curvas
  - **pivotal**: Rotação sobre o próprio eixo
  - **diagonal**: Movimento diagonal
- Exemplo: Tutorial que ensina APENAS reto e curva

### `difficulty` (string, default: "medium")
```json
"difficulty": "hard"
```
- Nível de dificuldade recomendado
- Valores: `"easy"`, `"medium"`, `"hard"`
- Informativo/referência

### `description` (string)
```json
"description": "Tutorial focado em modos reto e curva"
```
- Descrição específica desta fase
- Pode ser exibida na UI

## Exemplos Práticos

### Tutorial Simples (Sem Trafo, Modos Básicos)
```json
{
  "map_name": "Tutorial Básico",
  "player_spawn": [100, 100],
  "trafo_spawn": [200, 100],
  "phase_config": {
    "is_tutorial": true,
    "spawn_trafo": false,
    "force_hardcore_mode": false,
    "available_robot_modes": ["straight", "curve"],
    "difficulty": "easy",
    "description": "Aprenda movimento reto e em curva"
  }
}
```

### Nível Desafiador (Trafo, Todos os Modos, Hardcore)
```json
{
  "map_name": "Arena Desafiadora",
  "player_spawn": [300, 300],
  "trafo_spawn": [600, 300],
  "phase_config": {
    "is_tutorial": false,
    "spawn_trafo": true,
    "force_hardcore_mode": true,
    "available_robot_modes": ["straight", "curve", "pivotal", "diagonal"],
    "difficulty": "hard",
    "description": "Desafio extremo: todos os modos de operação, modo hardcore forçado"
  }
}
```

### Fase Equilibrada (Normal)
```json
{
  "map_name": "Level 1",
  "player_spawn": [100, 100],
  "trafo_spawn": [400, 50],
  "phase_config": {
    "is_tutorial": false,
    "spawn_trafo": true,
    "force_hardcore_mode": false,
    "available_robot_modes": ["straight", "curve", "pivotal", "diagonal"],
    "difficulty": "medium",
    "description": "Primeira fase do jogo. Todos os modos disponíveis."
  }
}
```

## Usando no Código

### Exemplo 1: Decidir se spawna trafo
```python
event_map = EventMapManager(map_path)

if event_map.has_trafo_spawn():
    trafo = init_trafo(event_map, spawn_point)
else:
    trafo = None
    print("[Game] Trafo desativado para este mapa")
```

### Exemplo 2: Restringir modos de operação
```python
available_modes = event_map.get_available_robot_modes()

# Desabilitar modos na UI se não disponíveis
if 'pivotal' not in available_modes:
    ui_manager.disable_pivotal_mode_button()

if 'diagonal' not in available_modes:
    ui_manager.disable_diagonal_mode_button()

# Se apenas um modo disponível, usar direto
if len(available_modes) == 1:
    selected_mode = available_modes[0]
```

### Exemplo 3: Forçar modo hardcore
```python
if event_map.is_hardcore_mode_forced():
    game_state['hardcore_mode'] = True
    ui_manager.disable_difficulty_selection()
    show_notification("⚠️ Modo Hardcore Ativado!")
```

### Exemplo 4: Adaptar UI para tutoriais
```python
if event_map.is_tutorial_mode():
    # Mostrar dicas extras
    activate_tutorial_hints()
    
    # Permitir mudar dificuldade mesmo em tutorial
    allow_difficulty_change = not event_map.is_hardcore_mode_forced()
```

### Exemplo 5: Acessar toda configuração
```python
config = event_map.get_phase_config()

print(f"Dificuldade: {config['difficulty']}")
print(f"Descrição: {config['description']}")
print(f"Trafo: {'Sim' if config['spawn_trafo'] else 'Não'}")
print(f"Modos do robô: {', '.join(config['available_robot_modes'])}")
```

## Valores Default (Se Não Especificados)

Se você não incluir `phase_config` no JSON, o sistema usa estes defaults:

```python
{
    "is_tutorial": False,
    "spawn_trafo": True,           # Spawna trafo por padrão
    "force_hardcore_mode": False,  # Permite escolher dificuldade
    "available_robot_modes": ["straight", "curve", "pivotal", "diagonal"],  # Todos modos disponíveis
    "difficulty": "medium"
}
```

Isso significa que mapas **SEM** `phase_config` funcionam normalmente (comportamento padrão).

## Exemplos Reais (Mapas Tutoriais)

### Tutorial 1: Alertas de Inclinação
```json
"phase_config": {
  "is_tutorial": true,
  "spawn_trafo": true,                    ← Tem trafo
  "force_hardcore_mode": false,           ← Pode escolher dificuldade
  "available_robot_modes": ["straight", "curve", "pivotal", "diagonal"],  ← Todos os modos
  "difficulty": "easy"
}
```

### Tutorial 2: Alertas dos Sensores
```json
"phase_config": {
  "is_tutorial": true,
  "spawn_trafo": false,                   ← SEM trafo para focar
  "force_hardcore_mode": false,
  "available_robot_modes": ["straight", "curve"],  ← Apenas básicos
  "difficulty": "easy"
}
```

### Tutorial 3: Modo Reto-Curva
```json
"phase_config": {
  "is_tutorial": true,
  "spawn_trafo": false,
  "force_hardcore_mode": true,            ← FORÇADO fácil
  "available_robot_modes": ["straight", "curve"],  ← Apenas reto e curva
  "difficulty": "easy"
}
```

## Checklist para Criar Nova Fase

- ✅ Decidir se terá trafo (`spawn_trafo`)
- ✅ Decidir se modo hardcore é livre ou forçado (`force_hardcore_mode`)
- ✅ Decidir quais modos de operação estão disponíveis (`available_robot_modes`)
- ✅ Definir dificuldade (`difficulty`)
- ✅ Descrever a fase (`description`)
- ✅ Marcar se é tutorial (`is_tutorial`)

## Integração com v1.0_pygame.py

No futuro, o código de inicialização pode usar:

```python
# Na função setup_game_objects:
event_map = EventMapManager(map_path)

# Verificar configurações específicas da fase
if not event_map.has_trafo_spawn():
    trafo = None  # Não spawnar

if event_map.is_hardcore_mode_forced():
    hardcore_mode = True  # Forçar

robot_modes = event_map.get_available_robot_modes()
# ...usar para restringir UI dos modos de operação
```

---

**Sistema totalmente configurável via JSON = Fácil de ajustar sem alterar código!** ✨

---

**Última atualização:** 2026-03-31
No futuro, o código de inicialização pode usar:

```python
# Na função setup_game_objects:
event_map = EventMapManager(map_path)

# Verificar configurações específicas da fase
if not event_map.has_trafo_spawn():
    trafo = None  # Não spawnar

if event_map.is_hardcore_mode_forced():
    hardcore_mode = True  # Forçar

robot_modes = event_map.get_available_robot_modes()
# ...usar para restringir UI dos modos de operação
```

---

**Sistema totalmente configurável via JSON = Fácil de ajustar sem alterar código!** ✨

---

**Última atualização:** 2026-03-31

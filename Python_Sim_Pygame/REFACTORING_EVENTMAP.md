# 🔄 Refatoração: EventMap Manager System

## Resumo das Mudanças

O sistema foi refatorado para que o **EventMap seja responsável por toda a lógica do mapa** (spawn points, colisões, metadados), enquanto a **imagem visual é apenas para renderização**.

## Antes da Refatoração ❌

```
┌─────────────────────────────────────┐
│  Imagem do Mapa (PNG)              │
│                                     │
│  - Pixels verdes = spawn player    │
│  - Pixels azuis = spawn trafo      │
│  - Pixels pretos = colisões        │
│  - Renderização visual             │
│                                     │
│  💥 Múltiplas responsabilidades!  │
└─────────────────────────────────────┘
```

### Fluxo antigo:
1. Carregar imagem do mapa
2. Procurar cor verde → spawn player
3. Procurar cor azul → spawn trafo
4. Procurar cor preta → colisões
5. Desenhar a imagem

## Depois da Refatoração ✅

```
┌──────────────────────────┐      ┌─────────────────────────────┐
│  EventMap (JSON)        │      │  Imagem Visual (PNG)        │
│                          │      │                              │
│  - Player spawn coords   │      │  - Renderização apenas      │
│  - Trafo spawn coords    │      │  - Colisões (cores)         │
│  - Metadados do mapa     │      │                              │
│                          │      │  (Separação de senso)      │
│  📋 Lógica centralizada │      │  🎨 Apenas visual          │
└──────────────────────────┘      └─────────────────────────────┘
```

### Fluxo novo:
1. Carregar **EventMap.json** → coordinates
2. Carregar imagem visual → render
3. Spawn points vêm do JSON
4. Colisões ainda usam imagem (por enquanto)
5. Desenhar a imagem

## Arquivos Alterados

### 📦 Novos Arquivos

1. **`World/EventMapManager.py`** ⭐
   - Gerenciador centralizado do mapa
   - Carrega JSON com spawn points
   - Fornece interface consistente
   - ~160 linhas

2. **`World/EventMap/*.json`** 📋
   - Metadados de cada mapa
   - Spawn points do player e trafo
   - Criadoautomaticamente para:
     - `Mapa Tutorial Alertas de Inclinação.json`
     - `Mapa Tutorial Alertas dos Sensores.json`
     - `Tutorial Modo Reto-Curva.json`

3. **`discover_event_map_spawns.py`** 🔍
   - Script auxiliar para popular JSONs
   - Lê cores das imagens automaticamente
   - Verde → player spawn
   - Azul → trafo spawn

4. **`test_event_map.py`** 🧪
   - Teste rápido do EventMapManager
   - Verifica carregamento de JSON
   - Valida spawn points

5. **`EVENTMAP_GUIDE.md`** 📖
   - Guia completo de uso do EventMap
   - Estrutura de arquivos
   - Exemplos práticos
   - Como criar novos mapas

### 🔧 Arquivos Modificados

1. **`game/initialization.py`**
   - ✅ Import: `from World.EventMapManager import EventMapManager`
   - ✅ Função `init_trafo()` refatorada:
     ```python
     def init_trafo(event_map, spawn_point):
         trafo_spawn = event_map.get_trafo_spawn()
         trafo = Trafo(trafo_spawn[0], trafo_spawn[1], ...)
         return trafo
     ```
   - ✅ Função `setup_game_objects()`:
     - Cria `EventMapManager` após carregar mapa
     - Usa `event_map.get_player_spawn()` em vez de `find_green_center()`
     - Passa `event_map` para `init_trafo()`
     - Adiciona `event_map` ao `game_state`

### ⚠️ Sem Alterações (Por enquanto)

- **`game/collision.py`** - Colisões ainda usam cores da imagem visual
  - Pode ser migrado para usar EventMap se necessário
  - `find_green_center()` e `find_blue_center()` ainda existem (não usadas)

- **`v1.0_pygame.py`** - Apenas import (não usa funções removidas)

## Exemplos de EventMap JSON

### Mapa Tutorial Alertas de Inclinação
```json
{
  "map_name": "Mapa Tutorial Alertas de Inclinação",
  "player_spawn": [959.5, 963.0],
  "trafo_spawn": [1109.5, 963.0],
  "metadata": {
    "description": "Tutorial para aprender sobre alertas de inclinação",
    "difficulty": "easy",
    "tutorial": true
  }
}
```

## Benefícios da Refatoração 🎯

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Responsabilidades** | 1 imagem = 4 funções | 1 JSON para lógica + 1 imagem para visual |
| **Manutenção** | Difícil (cores hardcoded) | Fácil (valores em JSON) |
| **Lógica do Mapa** | Espalhada | Centralizada em `EventMapManager` |
| **Criar Novo Mapa** | Depende de cores specific + script manual | Colocar 2 imagens = 100% automático ⚡ |
| **Colisões** | Acopladas ao spawn | Independentes (pode evoluir) |
| **Testes** | Difícil | Fácil com `test_event_map.py` |
| **Automatização** | Manual (rodar script) | Transparente (primeira execução) |

## Como Usar o Novo Sistema (Totalmente Automático!)

### 1️⃣ **Criar um novo mapa (3 passos!):**

**Passo 1:** Criar imagem visual
```
World/Obstacles/MyNewMap.png
```

**Passo 2:** Criar imagem de marcadores
```
World/EventMap/MyNewMap.png
```
- Coloque um ponto **verde** aonde quer spawnar o player
- Coloque um ponto **azul** aonde quer spawnar o trafo

**Passo 3:** Nada! ✨
```python
game_state = setup_game_objects(
    screen, 
    selected_map_path='World/Obstacles/MyNewMap.png'
)
```

O sistema vai automaticamente:
- ✅ Ler a imagem do EventMap
- ✅ Descobrir as posições das cores
- ✅ Criar o JSON
- ✅ Tudo pronto!

### 2️⃣ **Como funciona nos bastidores:**

```
Primeira execução:
1. Jogo carrega: World/Obstacles/MyNewMap.png
2. Cria EventMapManager
3. Procura JSON: World/EventMap/MyNewMap.json
4. JSON não existe? Ok, vou ler a imagem!
5. Lê cores verdes/azuis de World/EventMap/MyNewMap.png
6. Cria e salva o JSON automaticamente
7. Próximas vezes: Usa o JSON (instantâneo) ⚡

Segunda execução:
1. Carrega JSON direto (muito mais rápido)
```

### 3️⃣ **Acessar no código:**
```python
event_map = game_state['event_map']
player_pos = event_map.get_player_spawn()
trafo_pos = event_map.get_trafo_spawn()
```

## Backward Compatibility ✅

- ✅ Se um mapa NÃO tiver JSON, usa posições padrão
- ✅ Código antigo que importa `find_green_center` ainda funciona
- ✅ Imagens visuais não foram alteradas
- ✅ Sistema ainda lê colisões das imagens

## Próximos Passos 🚀

1. **Migrar colisões para EventMap** (opcional)
   - Arquivo de colisão separado
   - Máscara de colisão em JSON

2. **Adicionar mais metadados:**
   - Pontos de interesse
   - Zonas de risco
   - Eventos especiais

3. **Editor visual de EventMap** (futuro)
   - GUI para editar spawn points visualmente
   - Preview ao vivo sincronizado

## Teste Rápido

```bash
# Teste básico (mapas existentes com JSON)
python test_event_map.py

# Teste de auto-descoberta (novo mapa sem JSON)
python test_auto_discovery.py
```

Resultado esperado:

**test_event_map.py:**
```
✓ EventMapManager funcionando corretamente!
✓ Player spawn: (959.5, 963.0)
✓ Trafo spawn: (1109.5, 963.0)
```

**test_auto_discovery.py:**
```
✓ JSON foi criado automaticamente!
[EventMapManager] Auto-descoberto para 'TestNewMap': player_spawn=(280.5, 777.0)
✓ TESTE PASSADO: Auto-descoberta funciona perfeitamente!
```

---

**Data da Refatoração:** 2026-03-31  
**Status:** ✅ Completo, testado e **100% Automático!**  
**Versão:** v1.2 (EventMap Auto-Discovery)

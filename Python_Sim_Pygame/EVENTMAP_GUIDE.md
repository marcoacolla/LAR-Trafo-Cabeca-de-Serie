# 📍 EventMap Manager - Sistema Automático

## Visão Geral

O **EventMapManager** é **100% automático**! Você só precisa:

1. ✅ Colocar imagem visual em `World/Obstacles/MapName.png`
2. ✅ Colocar marcadores em `World/EventMap/MapName.png` (cores especiais)
3. ✅ **Pronto!** Na primeira execução, tudo é auto-configurado

Nenhum JSON manual, nenhum script, nenhuma configuração extra.

## Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│  PRIMEIRA EXECUÇÃO COM NOVO MAPA                           │
│                                                              │
│  1. Jogo inicia com: World/Obstacles/NewMap.png             │
│  2. EventMapManager procura: World/EventMap/NewMap.json     │
│  3. JSON NÃO EXISTE? Ok, procura imagem!                    │
│  4. Lê: World/EventMap/NewMap.png                           │
│  5. Descobre cores:                                         │
│     - Verde → player_spawn                                  │
│     - Azul → trafo_spawn                                    │
│  6. Cria e salva JSON automaticamente ✨                     │
│  7. Próximas execuções usam o JSON (mais rápido)            │
└─────────────────────────────────────────────────────────────┘
```

## Estrutura de Arquivo

### Visual (renderização)
```
World/Obstacles/MyMap.png
```
- Imagem visual do mapa com tudo: obstáculos, caminhos, decoração

### EventMap (lógica automática)
```
World/EventMap/MyMap.png
```
- Imagem com **marcadores de color**:
  - Pixels **verdes**: onde spawnar o player
  - Pixels **azuis**: onde spawnar o trafo
  - Resto: transparente ou ignorado

## Cores Reconhecidas Automaticamente

| Cor | Uso | RGB |
|-----|-----|-----|
| **Verde** | Spawn do Player | g >= 200, r < 100, b < 100 |
| **Azul** | Spawn do Trafo | b > max(r,g) + 30, b > 80 |
| **Outros** | Ignorados | Qualquer outra cor |

## Criando um Novo Mapa (3 passos!)

### 1. Criar imagem visual
```
World/Obstacles/MyNewMap.png
```
Desenhe o mapa com obstáculos, caminhos, etc.

### 2. Criar imagem de marcadores
```
World/EventMap/MyNewMap.png
```
- Coloque um **ponto/área verde** aonde quer spawnar o player
- Coloque um **ponto/área azul** aonde quer spawnar o trafo
- O resto pode ser transparente ou branco

### 3. Pronto! ✨
Quando o jogo iniciar com esse mapa:
```python
game_state = setup_game_objects(
    screen, 
    selected_map_path='World/Obstacles/MyNewMap.png'
)
```

O sistema vai:
- ✅ Ler a imagem do EventMap
- ✅ Auto-descobrir os spawn points
- ✅ Criar `World/EventMap/MyNewMap.json` automaticamente
- ✅ Usar o JSON nas próximas vezes (mais rápido)

## Arquivo JSON (Auto-gerado)

O sistema cria algo assim (você **não** precisa fazer isso):

```json
{
  "map_name": "MyNewMap",
  "player_spawn": [280.5, 777.0],
  "trafo_spawn": [430.5, 777.0],
  "metadata": {
    "auto_generated": true
  }
}
```

## Usando EventMapManager no Código

```python
from World.EventMapManager import EventMapManager

# Criar instância
# (se JSON não exisitir, auto-descobre da imagem)
event_map = EventMapManager('World/Obstacles/MyMap.png')

# Obter spawn points (auto-descobertos ou do JSON)
player_spawn = event_map.get_player_spawn()   # (x, y)
trafo_spawn = event_map.get_trafo_spawn()     # (x, y)

# Log de debug
print(event_map)
# <EventMapManager map='MyMap' player_spawn=(280.5, 777.0) trafo_spawn=(430.5, 777.0)>
```

## Exemplo Real

Você tem a imagem `World/EventMap/MyMap.png` com:
- Um **ponto verde** em (300, 100)
- Um **ponto azul** em (600, 100)

Primeira execução:
```
[EventMapManager] JSON não encontrado para 'MyMap', auto-descobrindo...
[EventMapManager] Auto-descoberto para 'MyMap': player_spawn=(300.0, 100.0) trafo_spawn=(600.0, 100.0)
[EventMapManager] JSON auto-gerado e salvo
```

Segunda execução:
```
[EventMapManager] Carregado JSON
```
(Mais rápido, porque o JSON já existe!)

## FAQ

### ❓ Preciso criar o JSON manualmente?
**Não!** O sistema cria automaticamente na primeira execução.

### ❓ Preciso rodar um script?
**Não!** Tudo acontece automaticamente ao iniciar o jogo.

### ❓ O que fazer se os spawn points ficarem errados?
1. Editar a imagem `World/EventMap/MapName.png` (ajustar cores)
2. Deletar o JSON `World/EventMap/MapName.json`
3. Reexecutar o jogo (cria novo JSON com cores corretas)

### ❓ Posso editar o JSON manualmente depois?
**Sim!** Edite o arquivo JSON se quiser fazer ajustes finos.

### ❓ Performance: isso desacelera o jogo?
**Não!** A auto-descoberta acontece **apenas uma vez** (primeira execução). Depois usa o JSON que é instantâneo.

## Notas Importantes

⚠️ **Pygame Display**: Se não houver display inicializado, o sistema cria um automaticamente (1x1 transparente).

✅ **Backward Compatibility**: Mapas antigos com JSON funcionam normalmente.

📝 **Metadados Adicionais**: Você pode adicionar informações extras ao JSON depois:

```json
{
  "map_name": "MyMap",
  "player_spawn": [300, 100],
  "trafo_spawn": [600, 100],
  "metadata": {
    "difficulty": "hard",
    "description": "Mapa desafiador com obstáculos",
    "author": "Seu Nome"
  }
}
```

---

**Última atualização:** 2026-03-31  
**Sistema:** 100% Automático ✨

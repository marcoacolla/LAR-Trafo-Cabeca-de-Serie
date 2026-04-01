# 📚 Exemplo Prático: Criando um Novo Mapa do Zero

## Cenário
Você quer criar um novo mapa chamado **"Arena Desafiadora"**.

## Passo 1: Criar Imagem Visual (renderização)
```
World/Obstacles/Arena Desafiadora.png
```

**O que você desenha:**
```
┌───────────────────────────────────────────┐
│                                           │
│   ███████                                 │
│   █     █  Obstáculo grande              │
│   █     █                                 │
│   ███████                                 │
│                    ██                     │
│                    ██  Obstáculo pequeno  │
│                                           │
│                        █████████          │
│                        █       █  Parede  │
│                        █████████          │
│                                           │
└───────────────────────────────────────────┘
```

*Cores: Preto = obstáculo (colisão), Branco = caminho seguro*

## Passo 2: Criar EventMap com Marcadores (spawn points)
```
World/EventMap/Arena Desafiadora.png
```

**O que você desenha:**
```
┌───────────────────────────────────────────┐
│                                           │
│   ███████                                 │
│   █     █  [PRETO = obstáculo]           │
│   █     █                                 │
│   ███████                                 │
│                    ██                     │
│      🟢             ██  [BRANCO = caminho]│
│    PLAYER          🔵                     │
│                      TRAFO                │
│                        █████████          │
│                        █       █          │
│                        █████████          │
│                                           │
└───────────────────────────────────────────┘

🟢 = Pixel VERDE (player spawn)      RGB: (0, 255, 0)
🔵 = Pixel AZUL (trafo spawn)       RGB: (0, 0, 255)
█ = Pixel PRETO (obstáculo/colisão) RGB: (0, 0, 0)
  = Pixel BRANCO (caminho seguro)    RGB: (255, 255, 255)
```

## Passo 3: NADA! 🎉

Só isso! Na primeira execução:
```python
game_state = setup_game_objects(
    screen,
    selected_map_path='World/Obstacles/Arena Desafiadora.png'
)
```

O sistema automaticamente:
1. ✅ Lê `World/EventMap/Arena Desafiadora.png`
2. ✅ Descobre pixel verde → player_spawn
3. ✅ Descobre pixel azul → trafo_spawn
4. ✅ Cria `World/EventMap/Arena Desafiadora.json`:
   ```json
   {
     "map_name": "Arena Desafiadora",
     "player_spawn": [50.0, 100.0],
     "trafo_spawn": [200.0, 100.0],
     "metadata": {
       "auto_generated": true
     }
   }
   ```

## Logs da Primeira Execução

```
[EventMapManager] JSON não encontrado para 'Arena Desafiadora', auto-descobrindo...
[EventMapManager] Auto-descoberto para 'Arena Desafiadora': player_spawn=(50.0, 100.0) trafo_spawn=(200.0, 100.0)
[EventMapManager] JSON auto-gerado e salvo: World/EventMap/Arena Desafiadora.json

✓ Mapa 'Arena Desafiadora' pronto para jogar!
```

## Logs da Segunda Execução (mais rápida)

```
[EventMapManager] Carregado JSON: World/EventMap/Arena Desafiadora.json

✓ Mapa 'Arena Desafiadora' carregado (do cache)
```

## Se Precisar Ajustar

Se os spawn points ficarem errados:

### Opção A: Editar a imagem do EventMap
1. Abra `World/EventMap/Arena Desafiadora.png`
2. Mova o pixel verde/azul para melhor posição
3. Delete o JSON: `World/EventMap/Arena Desafiadora.json`
4. Reexecute o jogo (vai recrear o JSON com novas cores)

### Opção B: Editar o JSON direto
```json
{
  "map_name": "Arena Desafiadora",
  "player_spawn": [100.0, 150.0],  // ← Ajuste aqui
  "trafo_spawn": [300.0, 150.0],   // ← Ou aqui
  "metadata": {
    "difficulty": "hard",
    "description": "Arena com obstáculos múltiplos"
  }
}
```

## Estrutura Final

```
World/
├── Obstacles/
│   ├── Mapa Tutorial Alertas de Inclinação.png
│   ├── Mapa Tutorial Alertas dos Sensores.png
│   ├── Tutorial Modo Reto-Curva.png
│   └── Arena Desafiadora.png ← Seu novo mapa
│
├── EventMap/
│   ├── Mapa Tutorial Alertas de Inclinação.json
│   ├── Mapa Tutorial Alertas de Inclinação.png
│   ├── Mapa Tutorial Alertas dos Sensores.json
│   ├── Mapa Tutorial Alertas dos Sensores.png
│   ├── Tutorial Modo Reto-Curva.json
│   ├── Tutorial Modo Reto-Curva.png
│   ├── Arena Desafiadora.json ← Auto-gerado na 1ª execução
│   └── Arena Desafiadora.png ← Com seus marcadores verdes/azuis
```

## Checklist para Novo Mapa

- ✅ Imagem visual em `World/Obstacles/MapName.png`
- ✅ Imagem com marcadores em `World/EventMap/MapName.png`
  - ✅ Pixel verde para player spawn
  - ✅ Pixel azul para trafo spawn
- ✅ Nomes exatamente igualzinhos (exceto extensão)
- ✅ Pronto! 🎉

---

**Duração para criar novo mapa:** ~5 minutos
**Configuração manual necessária:** NENHUMA ✨

# MoveCodeBeats

Prototipo inicial de TCC para transformar movimentos corporais em parametros musicais. Nesta fase o projeto foca em capturar a mao, extrair features de movimento e produzir uma representacao sonora local, sem integrar diretamente com Strudel ainda.

## Arquitetura revisada

O projeto foi reorganizado em uma pipeline pequena (camadas), mas preparada para crescer:

1. `capture/hand_tracker.py`
   Responsavel por abrir a camera, espelhar o feed e extrair landmarks da mao com MediaPipe.
2. `processing/movement_processor.py`
   Converte landmarks em features mais estaveis: posicao suavizada, velocidade do indicador e abertura entre polegar e indicador.
3. `mapping/gesture_mapper.py`
   Traduz as features em parametros musicais coerentes: nota, frequencia, amplitude, brilho.
4. `sound/sound_engine.py`
   Mantem um fluxo continuo de audio com `sounddevice`, em vez de tocar um buffer novo a cada frame.
5. `main.py`
   Orquestra o ciclo principal, atualiza audio, renderiza feedback visual e faz cleanup de camera e janela.

## Por que esta arquitetura e melhor para o TCC

- Separa claramente captura, processamento, mapeamento e saida sonora.
- Facilita trocar o sintetizador local por uma ponte com Strudel ou Supercollider no futuro.
- Permite testar regras de mapeamento sem depender de camera ou audio.
- Torna o prototipo mais estavel para demonstracao, porque evita `sd.play()` a cada frame.

## Mapeamento atual

- Movimento horizontal (eixo x) do indicador -> escolha de nota em escala pentatonica menor.
- Movimento vertical (eixo y)  do indicador -> amplitude.
- Velocidade da mao -> brilho timbrico.
- Abertura entre polegar e indicador -> influencia adicional no brilho.

## Instalacao

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Na primeira execucao, o projeto pode baixar automaticamente o modelo `hand_landmarker.task` do MediaPipe para a pasta `models/`.

## Execucao

```powershell
.\.venv\Scripts\python.exe main.py
```

Pressione `q` ou `Esc` para sair.

## Proximas etapas sugeridas

- Captura da segunda mão e definição de quais parametros sonoros ela vai controlar

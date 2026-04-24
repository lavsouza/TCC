# MoveCodeBeats

Prototipo inicial de TCC para transformar movimentos corporais em parametros musicais. Nesta fase o projeto foca em capturar a mao, extrair features de movimento e produzir uma representacao sonora local, sem integrar diretamente com Strudel ainda.

## Arquitetura revisada

O projeto foi reorganizado em uma pipeline pequena, mas preparada para crescer:

1. `capture/hand_tracker.py`
   Responsavel por abrir a camera, espelhar o feed e extrair landmarks da mao com MediaPipe.
2. `processing/movement_processor.py`
   Converte landmarks em features mais estaveis: posicao suavizada, velocidade do indicador e abertura entre polegar e indicador.
3. `mapping/gesture_mapper.py`
   Traduz as features em parametros musicais coerentes: nota, frequencia, amplitude, brilho e um hint para futura geracao em Strudel.
4. `sound/sound_engine.py`
   Mantem um fluxo continuo de audio com `sounddevice`, em vez de tocar um buffer novo a cada frame.
5. `main.py`
   Orquestra o ciclo principal, atualiza audio, renderiza feedback visual e faz cleanup de camera e janela.

## Por que esta arquitetura e melhor para o TCC

- Separa claramente captura, processamento, mapeamento e saida sonora.
- Facilita trocar o sintetizador local por uma ponte com Strudel no futuro.
- Permite testar regras de mapeamento sem depender de camera ou audio.
- Torna o prototipo mais estavel para demonstracao, porque evita `sd.play()` a cada frame.

## Mapeamento atual

- Movimento horizontal do indicador -> escolha de nota em escala pentatonica menor.
- Movimento vertical do indicador -> amplitude.
- Velocidade da mao -> brilho timbrico.
- Abertura entre polegar e indicador -> influencia adicional no brilho.

## Execucao

```powershell
.\.venv\Scripts\python.exe main.py
```

Pressione `q` ou `Esc` para sair.

## Proximas etapas sugeridas

- Adicionar gravacao de eventos gestuais para analise experimental.
- Criar um adaptador que transforme `SoundParameters` em blocos de codigo Strudel.
- Evoluir de controle continuo para gestos discretos como pinch, sweep, hold e trigger.
- Suportar duas maos com papeis distintos, por exemplo ritmo em uma mao e timbre na outra.

# MoveCodeBeats - Relatorio De Handoff Para Outro Assistente De IA

## 1. Objetivo Deste Documento

Este documento existe para atualizar rapidamente outro assistente de IA sobre o estado real do projeto `MoveCodeBeats`, sem exigir que ele reconstrua todo o contexto a partir do historico da conversa.

Ele resume:

- o objetivo atual do projeto;
- as decisoes arquiteturais ja tomadas;
- o que foi implementado ate agora;
- como o sistema funciona hoje;
- quais estrategias foram usadas;
- o que foi abandonado;
- quais testes e validacoes existem;
- quais limitacoes e proximos passos continuam abertos.

Este documento deve ser lido em conjunto com:

- [README.md](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/README.md)
- [docs/implementation-deep-dive.md](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/docs/implementation-deep-dive.md)
- [docs/architecture.md](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/docs/architecture.md)

---

## 2. Definicao Atual Do Projeto

`MoveCodeBeats` e um prototipo de TCC focado em transformar movimento corporal, especificamente movimento de uma pessoa, em controle musical executado no ambiente `Strudel`.

O escopo atual e:

- capturar ate duas maos com webcam;
- extrair landmarks via MediaPipe;
- converter landmarks em features semanticas de movimento;
- mapear essas features para parametros musicais;
- enviar o estado musical e o preview visual para uma interface web;
- executar o som exclusivamente no navegador com `Strudel`.

### Decisao importante ja tomada

O projeto **nao vai mais seguir com SuperCollider como foco de integracao**.

A decisao atual do usuario e:

- manter a geracao sonora apenas com `Strudel`;
- usar o navegador como ambiente final de execucao sonora;
- tratar `Strudel` como motor oficial de audio/live coding do prototipo.

Consequencias praticas:

- o projeto atual e `browser-first`;
- nao existe mais sintetizador local Python;
- nao existe mais dependencia operacional de `sounddevice`;
- o backend Python hoje e responsavel por captura, processamento, mapeamento e transporte;
- o frontend/browser e responsavel por execucao sonora via Strudel.

---

## 3. Resumo Executivo Do Status

### O que ja esta pronto

- captura de webcam com MediaPipe Tasks;
- deteccao de ate duas maos simultaneas;
- extracao de landmarks para cada mao;
- processamento com suavizacao temporal;
- estrutura de dados para mao primaria e secundaria;
- mapeamento musical funcional para `Strudel`;
- interface web com preview da camera + overlay;
- publicacao do estado por `WebSocket`;
- execucao sonora no navegador via `@strudel/web`;
- fallback automatico de portas locais no Windows;
- testes unitarios para pipeline gestual e integracao Strudel.

### O que ainda nao esta pronto

- geracao de `patterns` Strudel baseados em historico temporal mais rico;
- eventos gestuais discretos como `pinch`, `hold`, `tap`, `sweep`;
- composicao multimodal mais sofisticada entre as duas maos;
- gravacao/replay de sessao;
- interface de calibracao;
- persistencia de configuracoes;
- comunicacao com motores externos;
- captura de outros movimentos do corpo como rosto e corpo todo
- extensão maior de controle da sintaxe do strudel para controle sonoros de forma mais extensa e expressiva

### Estado atual do prototipo

O sistema ja e demonstravel de ponta a ponta:

`camera -> MediaPipe -> processamento -> mapeamento -> WebSocket -> UI web -> Strudel -> audio`

Ou seja: a viabilidade central do TCC ja foi demonstrada.

---

## 4. Arquitetura Atual

## 4.1 Pipeline

```text
Webcam
-> HandTracker
-> MovementProcessor
-> GestureMapper
-> StrudelOutput
-> Browser UI
-> Strudel Runtime
-> Audio
```

## 4.2 Separacao de responsabilidades

- `capture/hand_tracker.py`
  - abre a camera;
  - espelha o frame;
  - executa inferencia do MediaPipe;
  - devolve um `HandsFrame`.

- `processing/movement_processor.py`
  - escolhe mao primaria e secundaria;
  - calcula posicao, velocidade e abertura por mao;
  - aplica suavizacao temporal;
  - devolve `MotionFeatures`.

- `mapping/gesture_mapper.py`
  - converte `MotionFeatures` em `SoundParameters`;
  - define nota, frequencia, gain, brilho e synth.

- `utils/visualizer.py`
  - desenha landmarks, indices, labels de mao e estado textual;
  - produz o overlay exibido na interface web.

- `integration/strudel/`
  - converte `SoundParameters` em estado Strudel publicavel;
  - publica preview e estado via WebSocket;
  - sobe o servidor HTTP local da interface.

- `web/strudel/`
  - recebe preview e estado;
  - atualiza a UI;
  - executa o som com `Strudel`.

- `main.py`
  - orquestra o loop inteiro.

---

## 5. Estrategia De Implementacao Ja Utilizada

O projeto foi construido por iteracoes, nao por tentativa de implementar tudo ao mesmo tempo.

### Etapa 1. Prototipo de mao unica

Primeira estrategia:

- rastrear uma mao;
- extrair posicao e movimento do indicador;
- fazer um mapeamento sonoro local simples;
- validar rapidamente a ideia central.

### Etapa 2. Refatoracao por camadas

Depois, o sistema foi reorganizado em camadas:

- captura;
- processamento;
- mapeamento;
- visualizacao;
- output.

Isso foi importante para evitar acoplamento e para tornar possivel trocar a saida sonora sem reescrever captura/processamento.

### Etapa 3. Abandono do sintetizador local

O sintetizador Python local foi removido.

Razao:

- a direcao do projeto passou a ser `Strudel` como ambiente central;
- manter audio local em paralelo complicava a arquitetura;
- a interface browser-first ficou mais alinhada ao TCC e mais demonstravel.

### Etapa 4. Integracao browser-first com Strudel

Foi criada uma estrategia de integracao em que:

- Python calcula o estado musical;
- Python publica JSON via WebSocket;
- navegador recebe esse estado;
- navegador toca esse estado com Strudel.

### Etapa 5. Expansao para duas maos

A captura foi expandida para duas maos, e depois o mapeamento tambem foi expandido:

- mao primaria: nota + gain;
- mao secundaria: brilho + synth.

Essa estrategia foi escolhida porque:

- preserva o modelo de instrumento principal na mao dominante;
- usa a segunda mao como moduladora timbrica;
- evita colapsar duas maos em uma unica media confusa;
- mantem separacao gestual clara.

---

## 6. Bibliotecas E Versoes Em Uso

Dependencias Python declaradas em [requirements.txt](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/requirements.txt):

- `mediapipe==0.10.33`
- `numpy==2.4.4`
- `opencv-contrib-python==4.13.0.92`
- `websockets==15.0.1`

Dependencia principal do frontend:

- `@strudel/web@1.0.3` via CDN em [web/strudel/index.html](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/web/strudel/index.html)

Bibliotecas nativas importantes usadas no Python:

- `asyncio`
- `threading`
- `http.server`
- `urllib.request`
- `time`
- `math`
- `dataclasses`
- `pathlib`
- `json`
- `base64`

---

## 7. Arquivos Mais Importantes E O Que Cada Um Faz

### Backend central

- [main.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/main.py)
  - loop principal;
  - start/stop da integracao Strudel;
  - captura -> processamento -> mapeamento -> overlay -> publicacao.

- [utils/config.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/utils/config.py)
  - configuracoes centrais do sistema.

- [utils/models.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/utils/models.py)
  - contratos de dados entre as camadas.

### Captura

- [capture/hand_tracker.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/capture/hand_tracker.py)
  - inicializa webcam;
  - baixa modelo se necessario;
  - usa `mp.tasks.vision.HandLandmarker`;
  - retorna `HandsFrame`.

### Processamento

- [processing/movement_processor.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/processing/movement_processor.py)
  - mantem estado temporal por mao;
  - escolhe mao primaria/secondary;
  - calcula velocidade;
  - calcula abertura;
  - aplica suavizacao.

### Mapeamento musical

- [mapping/gesture_mapper.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/mapping/gesture_mapper.py)
  - escolhe nota da escala;
  - converte y em gain;
  - converte dinamica da mao secundaria em brilho;
  - escolhe synth a partir da posicao x da mao secundaria.

### Overlay

- [utils/visualizer.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/utils/visualizer.py)
  - desenha malha das maos;
  - escreve indices dos landmarks;
  - mostra estado atual do mapeamento.

### Integracao Strudel

- [integration/strudel/models.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/models.py)
  - define `StrudelState` e `PreviewFrame`.

- [integration/strudel/publisher.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/publisher.py)
  - gera estado Strudel;
  - aplica thresholds e throttle de publicacao.

- [integration/strudel/preview_publisher.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/preview_publisher.py)
  - gera JPEG base64 do overlay.

- [integration/strudel/bridge_server.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/bridge_server.py)
  - sobe servidor WebSocket;
  - faz fallback de porta;
  - transmite payloads JSON.

- [integration/strudel/web_server.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/web_server.py)
  - sobe servidor HTTP local;
  - serve `web/strudel/`;
  - serve `config.json` com `wsUrl`.

- [integration/strudel/output.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/output.py)
  - coordena bridge, preview e servidor web.

### Frontend

- [web/strudel/index.html](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/web/strudel/index.html)
  - estrutura da UI.

- [web/strudel/app.js](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/web/strudel/app.js)
  - conecta WebSocket;
  - renderiza estado;
  - inicializa Strudel;
  - toca/paralisa audio.

- `web/strudel/style.css`
  - estilos da UI.

### Testes

- [tests/test_pipeline.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/tests/test_pipeline.py)
  - valida processamento e mapeamento gestual.

- [tests/test_strudel_integration.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/tests/test_strudel_integration.py)
  - valida adaptacao para Strudel, preview e fallback de portas.

---

## 8. Estruturas De Dados Fundamentais

### `Landmark`

- representa um ponto anatomico com `x`, `y`, `z`.

### `HandFrame`

- representa uma mao detectada em um instante.

Campos:

- `landmarks`
- `handedness`
- `timestamp`

### `HandsFrame`

- encapsula todas as maos detectadas no frame.

Campos e utilitarios:

- `hands`
- `timestamp`
- `count`
- `handedness_labels`
- `get_hand()`
- `select_primary()`
- `select_secondary()`

### `HandMotion`

- representa a feature semantica de uma mao individual.

Campos:

- `raw_x`
- `raw_y`
- `x`
- `y`
- `velocity`
- `openness`
- `handedness`
- `active`

### `MotionFeatures`

- representa o estado combinado do frame.

Campos:

- `primary`
- `secondary`
- `hands_detected`

Propriedades importantes:

- `active`
- `x`, `y`, `velocity`, `openness`, `handedness` da mao primaria
- `has_secondary`
- `secondary_handedness`

### `SoundParameters`

- representa o estado sonoro calculado antes da traducao Strudel.

Campos:

- `frequency`
- `amplitude`
- `brightness`
- `note_label`
- `synth_name`
- `active`

### `StrudelState`

- representa o estado pronto para publicacao na UI/Strudel.

Campos:

- `active`
- `note_label`
- `strudel_note`
- `frequency`
- `gain`
- `brightness`
- `lpf`
- `synth`
- `hands_detected`
- `primary_handedness`
- `secondary_handedness`
- `brightness_source`
- `code`
- `timestamp`

---

## 9. Como O Sistema Funciona Hoje

## 9.1 Captura

O [capture/hand_tracker.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/capture/hand_tracker.py) faz:

1. `cv2.VideoCapture`
2. espelhamento do frame
3. conversao `BGR -> RGB`
4. criacao de `mp.Image`
5. inferencia com `HandLandmarker.detect_for_video()`
6. conversao do resultado do MediaPipe para `HandsFrame`

Se o modelo `.task` nao existir, ele tenta baixar automaticamente.

## 9.2 Processamento

O [processing/movement_processor.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/processing/movement_processor.py) faz:

1. normaliza a entrada para lista de maos;
2. escolhe a mao primaria com persistencia de handedness;
3. escolhe a mao secundaria se houver;
4. para cada mao, calcula:
   - `raw_x`, `raw_y`
   - `velocity`
   - `openness`
5. aplica suavizacao exponencial;
6. retorna `MotionFeatures`.

### Formula de velocidade

```text
delta_t = max(t2 - t1, 1e-3)
delta_pos = distancia((x2, y2), (x1, y1))
velocity = clamp((delta_pos / delta_t) / velocity_reference)
```

Com `velocity_reference = 1.3`.

### Formula de abertura

```text
hand_scale = max(dist(wrist, middle_mcp), 1e-4)
openness = clamp(dist(thumb_tip, index_tip) / (hand_scale * hand_span_reference))
```

Com `hand_span_reference = 2.2`.

### Formula de suavizacao

```text
smooth(v, prev, alpha) = prev + alpha * (v - prev)
```

Se `prev` for `None`, retorna `v`.

## 9.3 Mapeamento musical

O [mapping/gesture_mapper.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/mapping/gesture_mapper.py) usa:

- mao primaria para `nota + gain`;
- mao secundaria para `brilho + synth`.

### Escala atual

Configuracao:

- `root_midi = 48`
- `octaves = 3`
- `scale_intervals = (0, 3, 5, 7, 10)`

Isso gera uma pentatonica menor de `C` em tres oitavas:

- `C3, D#3, F3, G3, A#3`
- `C4, D#4, F4, G4, A#4`
- `C5, D#5, F5, G5, A#5`

### Formula da nota

```text
note_index = round(primary.x * (len(scale) - 1))
```

### Formula do gain

```text
amplitude = min_amplitude + (1 - primary.y) * (max_amplitude - min_amplitude)
```

Com defaults:

```text
amplitude = 0.08 + (1 - y) * 0.57
```

### Formula do brilho

Se houver mao secundaria:

```text
modulator = secondary
```

Caso contrario:

```text
modulator = primary
```

Entao:

```text
brightness = clamp(
  modulator.velocity * velocity_weight +
  modulator.openness * openness_weight
)
```

Com defaults:

```text
brightness = clamp(
  modulator.velocity * 0.6 +
  modulator.openness * 0.4
)
```

### Escolha do synth pela segunda mao

```text
synth_index = round(secondary.x * (len(secondary_synths) - 1))
```

Defaults:

- `sine`
- `triangle`
- `sawtooth`
- `square`

Se nao houver segunda mao:

- synth default = `sawtooth`

## 9.4 Visualizacao

O [utils/visualizer.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/utils/visualizer.py) desenha:

- malha da mao;
- indice numerico dos 21 landmarks;
- label `LEFT/RIGHT`;
- mao primaria e secundaria;
- nota;
- frequencia;
- amplitude;
- brilho;
- synth;
- velocidade e abertura de cada mao.

## 9.5 Publicacao para o navegador

O [integration/strudel/publisher.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/publisher.py) gera `StrudelState`.

Transformacoes importantes:

- `note_label -> strudel_note`
- `amplitude -> gain`
- `brightness -> lpf`
- `synth_name -> synth`

### Formula do LPF

```text
lpf = round(lpf_min + brightness * (lpf_max - lpf_min))
```

Com defaults:

```text
lpf = round(400 + brightness * 3600)
```

### Politica de publicacao

Publica imediatamente quando:

- o primeiro estado chega;
- `active` muda;
- `note_label` muda;
- `synth` muda;
- `hands_detected` muda;
- `primary_handedness` muda;
- `secondary_handedness` muda.

Tambem publica quando:

- `gain_delta >= 0.03`
- `brightness_delta >= 0.05`
- ou passou o intervalo de `1 / update_hz`

Com default:

- `update_hz = 8`

## 9.6 Preview da camera

O [integration/strudel/preview_publisher.py](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/integration/strudel/preview_publisher.py) faz:

- resize opcional;
- codificacao JPEG;
- conversao para base64;
- envio como `data:image/jpeg;base64,...`

Defaults:

- `preview_update_hz = 12`
- `preview_jpeg_quality = 72`
- `preview_max_width = 960`

## 9.7 Frontend/browser

O [web/strudel/app.js](/C:/Users/lucas/OneDrive/Faculdade%20e%20Carreira/Faculdade%202026.1/Tcc%202/MoveCodeBeats/web/strudel/app.js) faz:

1. carrega `config.json`;
2. descobre `wsUrl`;
3. conecta no WebSocket ao clicar `Conectar`;
4. inicializa Strudel ao clicar `Ativar Audio`;
5. recebe payloads `state` e `frame`;
6. atualiza a UI;
7. monta pattern:

```javascript
note(state.strudel_note).s(state.synth).gain(state.gain).lpf(state.lpf)
```

8. toca essa pattern com `.play()`;
9. usa `hush()` para silenciar.

---

## 10. Decisoes Arquiteturais Importantes Ja Fechadas

1. **Strudel e a saida sonora oficial**
   - o projeto atual nao depende de SuperCollider.

2. **Browser-first**
   - sem janela OpenCV local como interface principal;
   - sem sintetizador local Python.

3. **Duas maos com papeis diferentes**
   - mao primaria = controle melodico/dinamico;
   - mao secundaria = controle timbrico.

4. **Estado continuo antes de patterns**
   - a implementacao atual envia o estado musical atual;
   - ainda nao gera patterns complexos baseados em historico.

5. **Fallback automatico de portas**
   - necessario por conflitos reais em Windows com `8080` e `8765`.

6. **Modularidade por camadas**
   - captura, processamento, mapeamento e output foram separados intencionalmente para facilitar evolucao.

---

## 11. O Que Foi Removido Ou Abandonado

### Ja removido do codigo

- sintetizador local Python (`SoundEngine`) e output local antigo.

### Ja abandonado como direcao principal

- integracao com SuperCollider como proximo foco imediato.

### O que ainda existe apenas como passado historico

- partes da narrativa antiga do projeto podem mencionar fases anteriores de prototipacao local;
- a arquitetura atual, porem, e totalmente centrada em `Strudel`.

---

## 12. Validacao Atual

### Comandos de teste usados recentemente

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py capture\hand_tracker.py processing\movement_processor.py mapping\gesture_mapper.py integration\strudel\bridge_server.py integration\strudel\web_server.py integration\strudel\output.py integration\strudel\publisher.py utils\config.py utils\models.py utils\visualizer.py tests\test_pipeline.py tests\test_strudel_integration.py
```

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_pipeline tests.test_strudel_integration
```

### Cobertura validada pelos testes

- ativacao do pipeline quando ha mao;
- calculo de velocidade;
- selecao de mao preferida;
- fallback de mao primaria;
- exposicao da mao secundaria;
- aumento de pitch com movimento horizontal;
- mute sem mao;
- mapeamento da mao secundaria para brilho/synth;
- conversao de nota para Strudel;
- geracao do codigo Strudel equivalente;
- throttle da publicacao de estado;
- throttle do preview;
- fallback de portas para HTTP e WebSocket.

### Observacao operacional relevante

No Windows do usuario ja houve conflito real de porta:

- `8080` estava ocupada;
- a integracao falhava com `[WinError 10013]`.

Isso foi corrigido por fallback automatico de porta. Em um smoke test recente, a saida subiu corretamente em:

- `http://127.0.0.1:8081`

---

## 13. Limitacoes E Debitos Tecnicos Atuais

1. O sistema ainda trabalha com `estado continuo`, nao com `patterns` temporais ricos.
2. O frontend toca um estado por vez e usa `hush()` antes de tocar o proximo.
3. Nao ha transicao sonora mais sofisticada no Strudel.
4. O preview trafega como JPEG base64, o que pode ser pesado.
5. Nao ha calibracao por usuario.
6. Nao ha persistencia de configuracao.
7. Nao ha gestos discretos identificados semanticamente.
8. A segunda mao ainda nao controla eventos/patterns, apenas timbre continuo.
9. Nao ha multiplexacao polifonica real por mao.
10. O browser precisa de gesto do usuario para liberar audio por politica de autoplay.

---

## 14. Proximos Passos Mais Coerentes

Se outro assistente for continuar este projeto, os proximos caminhos mais coerentes sao:

### Caminho 1. Evolucao gestual-musical

- detectar eventos como:
  - `pinch`
  - `release`
  - `hold`
  - `sweep`
  - `cross`
- usar isso para disparar patterns ou mudancas estruturais no Strudel.

### Caminho 2. Evolucao da segunda mao

- transformar a segunda mao em controle de:
  - densidade ritmica;
  - efeitos adicionais;
  - troca de pattern;
  - layer secundaria.

### Caminho 3. Evolucao da saida Strudel

- deixar de tocar apenas snapshots;
- construir frases/patterns a partir de buffer temporal curto;
- gerar codigo mais idiomatico de live coding.

### Caminho 4. Evolucao da experiencia de uso

- painel de calibracao;
- reset de estado;
- troca de escala;
- selecao da mao dominante via interface.

---

## 15. Regras Importantes Para Quem Continuar

1. Nao reintroduzir audio local Python sem necessidade real.
2. Tratar Strudel como motor sonoro oficial do projeto.
3. Preservar a separacao em camadas.
4. Manter os testes atualizados quando o mapeamento mudar.
5. Nao assumir que `8080` e `8765` estarao livres no Windows do usuario.
6. Se mexer no mapeamento, atualizar:
   - `README.md`
   - `docs/implementation-deep-dive.md`
   - testes
   - UI web, se os campos mudarem

---

## 16. Observacoes De Estado Do Repositorio

No momento desta consolidacao:

- o projeto possui alteracoes locais nao commitadas em varios arquivos do prototipo;
- tambem existem alteracoes na pasta `.idea`, que parecem ser artefatos de IDE e nao devem ser revertidas sem pedido explicito;
- outro assistente deve tomar cuidado para nao sobrescrever mudancas do usuario fora do escopo do backend/frontend principal.

---

## 17. Resumo Final Em Uma Frase

O `MoveCodeBeats` ja e hoje um prototipo funcional de controle musical gestual com duas maos, executando som exclusivamente em `Strudel` no navegador, com pipeline modular, preview visual via WebSocket e base pronta para a proxima etapa: sair de estado continuo e entrar em gestos/eventos/patterns mais expressivos.

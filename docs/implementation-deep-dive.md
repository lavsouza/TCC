# MoveCodeBeats - Documento Tecnico Detalhado Da Implementacao Atual

## 1. Objetivo Deste Documento

Este documento descreve a implementacao atual do `MoveCodeBeats` com nivel maximo de detalhe tecnico. O foco e explicar:

- o papel de cada arquivo relevante;
- a topologia de execucao do sistema;
- as bibliotecas utilizadas e como elas interagem;
- os contratos de dados entre as camadas;
- os calculos numericos e as formulas de mapeamento;
- a integracao exata entre Python, WebSocket, navegador e Strudel;
- os artefatos visuais existentes no projeto;
- os testes que validam a implementacao.

O documento descreve a versao atual do prototipo, isto e, a versao `browser-first`, sem sintetizador local em Python. O som agora e produzido no navegador pelo runtime do Strudel, enquanto o backend Python e responsavel por:

1. capturar a imagem da camera;
2. detectar a mao com MediaPipe;
3. extrair features de movimento;
4. mapear essas features para parametros musicais;
5. desenhar o overlay visual;
6. publicar o estado musical e o preview visual via HTTP + WebSocket.

---

## 2. Snapshot Tecnologico Atual

### 2.1 Linguagem principal

- `Python 3.14.0`

### 2.2 Dependencias Python declaradas

- `mediapipe==0.10.33`
- `numpy==2.4.4`
- `opencv-contrib-python==4.13.0.92`
- `websockets==15.0.1`

### 2.3 Dependencias JavaScript / navegador

- `@strudel/web@1.0.3` carregado por CDN em `web/strudel/index.html`
- APIs nativas do navegador:
  - `WebSocket`
  - `fetch`
  - DOM API
  - `HTMLImageElement`
  - WebAudio, indiretamente, por meio do runtime do Strudel

### 2.4 Bibliotecas da standard library do Python utilizadas

- `dataclasses`
- `pathlib`
- `time`
- `urllib.request`
- `math`
- `re`
- `asyncio`
- `json`
- `threading`
- `typing`
- `functools`
- `http.server`
- `http`
- `urllib.parse`
- `base64`
- `webbrowser`
- `unittest`

---

## 3. Artefatos Do Projeto

### 3.1 Artefatos de codigo

- `main.py`
- `capture/hand_tracker.py`
- `processing/movement_processor.py`
- `mapping/gesture_mapper.py`
- `utils/config.py`
- `utils/models.py`
- `utils/visualizer.py`
- `integration/strudel/models.py`
- `integration/strudel/note_adapter.py`
- `integration/strudel/code_generator.py`
- `integration/strudel/publisher.py`
- `integration/strudel/preview_publisher.py`
- `integration/strudel/bridge_server.py`
- `integration/strudel/web_server.py`
- `integration/strudel/output.py`
- `web/strudel/index.html`
- `web/strudel/app.js`
- `web/strudel/style.css`
- `tests/test_pipeline.py`
- `tests/test_strudel_integration.py`

### 3.2 Artefatos de diagrama

#### Fontes UML em PlantUML

- `docs/uml/component-diagram.puml`
- `docs/uml/sequence-diagram.puml`
- `docs/uml/class-diagram.puml`

#### Renderizacoes PNG atualizadas

- `docs/uml/component-diagram.png`
- `docs/uml/sequence-diagram.png`
- `docs/uml/class-diagram.png`

### 3.3 Outros artefatos relevantes

- `models/hand_landmarker.task`
  - modelo do MediaPipe Tasks usado para deteccao/rastreamento da mao.

---

## 4. Arquitetura Atual Em Alto Nivel

O sistema atual possui uma arquitetura em camadas com separacao clara entre:

1. captura;
2. processamento semantico;
3. mapeamento musical;
4. visualizacao;
5. integracao de saida para navegador/Strudel.

### 4.1 Diagrama Geral Em Mermaid

```mermaid
flowchart LR
    U["Usuario<br/>Movimenta a mao"] --> C["Webcam"]
    C --> H["HandTracker"]
    H --> P["MovementProcessor"]
    P --> M["GestureMapper"]
    H --> V["render_overlay"]
    P --> V
    M --> V
    M --> O["StrudelOutput"]
    V --> O
    O --> B["Browser UI"]
    B --> S["Strudel Runtime"]
```

### 4.2 Diagrama De Topologia De Execucao

```mermaid
flowchart TD
    subgraph PythonProcess["Processo Python"]
        Main["main.py<br/>thread principal"]
        WS["StrudelBridgeServer<br/>thread + asyncio loop"]
        HTTP["StrudelWebServer<br/>thread HTTP"]
    end

    subgraph Browser["Navegador"]
        UI["web/strudel/index.html + app.js"]
        Audio["Strudel WebAudio Runtime"]
    end

    Main --> WS
    Main --> HTTP
    WS --> UI
    HTTP --> UI
    UI --> Audio
```

### 4.3 Consequencia arquitetural mais importante

A implementacao atual usa o Python como:

- camada de captura e analise gestual;
- gerador de estado musical;
- servidor local de interface;
- publicador de preview visual e parametros musicais.

O Python nao sintetiza mais audio. O audio pertence ao navegador, via Strudel.

---

## 5. Ciclo Completo De Execucao

## 5.1 Startup

Quando `main.py` e executado:

1. `load_config()` cria um `AppConfig`;
2. `HandTracker` tenta abrir a camera e carregar o modelo do MediaPipe;
3. `MovementProcessor` e instanciado;
4. `GestureMapper` e instanciado;
5. `StrudelOutput` e instanciado;
6. `StrudelOutput.start()` sobe:
   - um servidor WebSocket;
   - um servidor HTTP para a UI;
7. o terminal imprime a URL local;
8. inicia o loop infinito de captura e publicacao.

## 5.2 Loop principal

Em cada iteracao:

1. `tracker.read()` captura um frame da camera e tenta detectar ate duas maos;
2. `processor.process(hands_frame)` transforma landmarks em features numericas;
3. `mapper.map(motion)` converte features em parametros sonoros;
4. `render_overlay(...)` desenha landmarks e informacoes textuais;
5. `strudel_output.publish_state(motion, sound_params)` envia o estado musical enriquecido com o papel das duas maos;
6. `strudel_output.publish_preview(overlay)` envia um preview JPEG do frame anotado.

## 5.3 Encerramento

O encerramento normal acontece por `KeyboardInterrupt` (`Ctrl+C`):

1. o `except KeyboardInterrupt` registra o encerramento;
2. o bloco `finally` fecha a camera;
3. o bloco `finally` encerra o servidor HTTP e o servidor WebSocket.

---

## 6. Detalhamento Arquivo A Arquivo

## 6.1 `main.py`

### 6.1.1 Papel

`main.py` e o orquestrador central. Ele nao implementa deteccao, processamento, mapeamento, interface web ou Strudel em si. Ele apenas:

- instancia os modulos;
- define a ordem de chamada;
- controla o loop;
- garante o encerramento correto.

### 6.1.2 Dependencias importadas

- `HandTracker`
- `StrudelOutput`
- `GestureMapper`
- `MovementProcessor`
- `load_config`
- `render_overlay`

### 6.1.3 Detalhes de controle

- Se a camera falha na inicializacao, o programa termina com codigo `1`.
- Se `StrudelOutput` estiver desabilitado em configuracao, a versao atual nao continua em modo degradado; ela encerra com erro, porque este prototipo agora depende da saida web como componente central.
- O loop principal nao possui `sleep()`. O ritmo de execucao e imposto por:
  - tempo de `cv2.VideoCapture.read()`;
  - tempo de inferencia do MediaPipe;
  - custo do processamento de movimento;
  - custo do mapeamento;
  - custo de desenho do overlay;
  - throttling de preview e de estado no `StrudelOutput`.

### 6.1.4 Implicacao

O `main.py` funciona como um scheduler simples de tempo real, porem sem fila, sem buffer historico e sem processamento em batch.

---

## 6.2 `utils/config.py`

### 6.2.1 Papel

Centralizar todos os parametros configuraveis do sistema.

### 6.2.2 `PROJECT_ROOT`

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

Esse valor define a raiz logica do projeto e e utilizado para localizar:

- `models/hand_landmarker.task`
- `web/strudel/`

### 6.2.3 `CameraConfig`

Campos:

- `device_index=0`
  - usa a camera padrao do sistema.
- `frame_width=1280`
- `frame_height=720`
  - resolucao alvo da captura.
- `mirror_feed=True`
  - espelha horizontalmente o video.
- `max_num_hands=2`
  - permite inferencia de ate duas maos no mesmo frame.
- `min_detection_confidence=0.65`
- `min_presence_confidence=0.5`
- `min_tracking_confidence=0.55`
  - limiares do MediaPipe.
- `model_path`
  - caminho local para o arquivo `.task`.
- `model_url`
  - URL de download do modelo oficial.

### 6.2.4 `ProcessingConfig`

- `position_smoothing=0.3`
- `velocity_smoothing=0.25`
- `openness_smoothing=0.2`
- `velocity_reference=1.3`
- `hand_span_reference=2.2`
- `primary_handedness="right"`

Interpretacao:

- os tres primeiros valores sao fatores `alpha` para media exponencial;
- `velocity_reference` define a velocidade considerada suficiente para normalizar o valor perto de `1`;
- `hand_span_reference` regula a abertura normalizada da mao;
- `primary_handedness` define a mao preferencial para controle quando duas maos sao detectadas e nao existe ainda uma mao ativa persistida.

### 6.2.5 `MappingConfig`

- `root_midi=48` -> `C3`
- `octaves=3`
- `scale_intervals=(0, 3, 5, 7, 10)` -> pentatonica menor
- `min_amplitude=0.08`
- `max_amplitude=0.65`
- `velocity_weight=0.6`
- `openness_weight=0.4`
- `default_synth_name="sawtooth"`
- `secondary_synths=("sine", "triangle", "sawtooth", "square")`

### 6.2.6 `StrudelConfig`

Campos de transporte:

- `enabled=True`
- `ws_host="127.0.0.1"`
- `ws_port=8765`
- `http_host="127.0.0.1"`
- `http_port=8080`
- `port_search_span=20`

Campos de publicacao do estado musical:

- `update_hz=8`
- `note_change_immediate=True`
- `gain_precision=3`
- `gain_delta=0.03`
- `brightness_delta=0.05`
- `lpf_min=400`
- `lpf_max=4000`
- `synth_name="sawtooth"`
- `send_inactive_state=True`

Campos de publicacao do preview:

- `preview_update_hz=12`
- `preview_jpeg_quality=72`
- `preview_max_width=960`

Campo utilitario:

- `auto_open_browser=False`

Observacao:

- se as portas preferenciais estiverem ocupadas ou bloqueadas, os servidores HTTP e WebSocket tentam automaticamente as portas seguintes dentro da faixa definida por `port_search_span`.

### 6.2.7 `UiConfig`

- `window_name="MoveCodeBeats"`

Mesmo sem janela local OpenCV, o nome ainda e usado como titulo no overlay textual e no frontend.

### 6.2.8 `AppConfig`

Agrega:

- `camera`
- `processing`
- `mapping`
- `strudel`
- `ui`

### 6.2.9 `load_config()`

Atualmente:

```python
def load_config() -> AppConfig:
    return AppConfig()
```

Isto significa que:

- nao ha parsing de `.env`, `json`, `yaml` ou CLI;
- a configuracao atual e puramente in-code;
- reproducibilidade depende do versionamento do repositorio.

---

## 6.3 `utils/models.py`

### 6.3.1 Papel

Definir os contratos estruturais de dados do backend.

### 6.3.2 `Landmark`

Representa um ponto 3D detectado:

- `x`
- `y`
- `z`

`frozen=True` significa:

- o objeto e imutavel depois de criado;
- isso reduz risco de mutacao acidental.

### 6.3.3 `HandFrame`

Representa a mao detectada em um instante:

- `landmarks: list[Landmark]`
- `handedness: str`
- `timestamp: float`

Observacao importante:

- `HandFrame` continua sendo a estrutura de uma mao individual.
- a expansao para duas maos adiciona um contêiner acima dele, `HandsFrame`, em vez de alterar o significado de `HandFrame`.

### 6.3.4 `HandsFrame`

Representa o conjunto de maos detectadas no mesmo frame:

- `hands: list[HandFrame]`
- `timestamp: float`

Metodos e propriedades relevantes:

- `count`
- `handedness_labels`
- `get_hand(handedness)`
- `select_primary(preferred_handedness=None)`

`select_primary(...)` aplica a regra atual de selecao:

1. tenta a mao preferida informada;
2. se nao existir, tenta `"right"`;
3. se nao existir, tenta `"left"`;
4. se ainda assim nao houver correspondencia, usa a primeira mao disponivel.

### 6.3.5 `HandMotion`

Representa uma mao isolada ja traduzida em variaveis semanticas:

- `raw_x`
- `raw_y`
- `x`
- `y`
- `velocity`
- `openness`
- `handedness`
- `active`

Observacao importante:

- `raw_x` e `raw_y` sao os valores brutos clamped;
- `x` e `y` sao os valores suavizados;
- `velocity` e `openness` pertencem a essa mao especifica, nao ao frame inteiro.

### 6.3.6 `MotionFeatures`

Representa o estado combinado do frame atual:

- `primary: HandMotion`
- `secondary: HandMotion`
- `hands_detected: int`

Propriedades derivadas:

- `active` -> espelha `primary.active`
- `x`, `y`, `velocity`, `openness`, `handedness` -> atalhos para a mao primaria
- `has_secondary` -> indica se ha uma mao secundaria util no frame
- `secondary_handedness` -> handedness da mao secundaria

### 6.3.7 `ScaleNote`

Representa uma nota precomputada da escala:

- `midi`
- `label`
- `frequency`

### 6.3.8 `SoundParameters`

Representa o estado musical calculado pelo mapper:

- `frequency`
- `amplitude`
- `brightness`
- `note_label`
- `synth_name`
- `active`

Observacao importante:

- `SoundParameters.frequency` ainda existe e e calculado com precisao, embora o frontend atual do Strudel execute pela nota (`note(...)`) e nao por `freq(...)`.
- Portanto, `frequency` hoje e usada principalmente para observabilidade, depuracao e extensao futura.
- `synth_name` permite que a mao secundaria escolha explicitamente qual synth do Strudel sera usado na execucao.

---

## 6.4 `capture/hand_tracker.py`

### 6.4.1 Papel

Camada de aquisicao e inferencia visual.

### 6.4.2 Bibliotecas utilizadas

- `cv2`
- `mediapipe as mp`
- `urllib.request`
- `time`

### 6.4.3 Inicializacao

No construtor:

1. guarda a configuracao;
2. abre a camera com `_open_capture`;
3. configura largura e altura;
4. cria o detector de mao com `_create_landmarker`.

### 6.4.4 Selecao da camera

`_open_capture()` tenta:

1. `cv2.CAP_DSHOW` quando disponivel;
2. se falhar, `cv2.VideoCapture(device_index)` padrao.

Motivo:

- em Windows, `CAP_DSHOW` frequentemente reduz problemas de inicializacao.

### 6.4.5 Pipeline de leitura

`read()` faz:

1. `self._capture.read()`
2. valida `ok` e `frame`
3. aplica espelhamento se `mirror_feed=True`
4. converte `BGR -> RGB`
5. encapsula o frame em `mp.Image`
6. gera `timestamp_ms = int(time.perf_counter() * 1000)`
7. chama `detect_for_video`
8. converte a resposta para `HandsFrame`

### 6.4.6 Por que `time.perf_counter()`?

Porque:

- e monotonicamente crescente;
- e apropriado para intervalos e medições temporais;
- evita problemas de ajuste de relogio do sistema.

### 6.4.7 Modelo do MediaPipe

`_create_landmarker()` usa:

- `mp.tasks.BaseOptions(model_asset_path=...)`
- `mp.tasks.vision.HandLandmarkerOptions(...)`
- `mp.tasks.vision.RunningMode.VIDEO`

`VIDEO` e importante porque:

- o MediaPipe passa a considerar o fluxo temporal;
- isso e mais apropriado para webcam do que `IMAGE`.

### 6.4.8 Extração de dados da mao

`_extract_hand(result)`:

- le `result.hand_landmarks`;
- usa apenas a primeira mao detectada;
- converte cada ponto em `Landmark`;
- extrai `handedness` de `result.handedness`;
- carimba `timestamp=time.perf_counter()`.

### 6.4.9 Download do modelo

`_ensure_model_file()`:

- verifica se `model_path` existe;
- se nao existir, cria a pasta;
- tenta baixar via `urllib.request.urlretrieve`;
- em caso de falha, levanta `RuntimeError` com orientacao manual.

### 6.4.10 Limitacoes da implementacao

- somente a primeira mao e usada;
- nao ha reconexao automatica da camera se ela falhar no meio da execucao;
- nao ha selecao de camera por UI;
- o frame retornado e o frame BGR espelhado, nao um RGB pronto para web.

---

## 6.5 `processing/movement_processor.py`

### 6.5.1 Papel

Transformar landmarks crus em features dinamicas e relativamente estaveis.

### 6.5.2 Estado interno

O processador e stateful. Ele guarda:

- `_prev_raw_x`
- `_prev_raw_y`
- `_prev_timestamp`
- `_smoothed_x`
- `_smoothed_y`
- `_smoothed_velocity`
- `_smoothed_openness`

Sem esse estado:

- nao seria possivel calcular velocidade temporal;
- nao seria possivel aplicar suavizacao exponencial.

### 6.5.3 Landmarks utilizados

- `8` -> ponta do indicador
- `4` -> ponta do polegar
- `0` -> punho
- `9` -> base do dedo medio (`middle_mcp`)

### 6.5.4 Calculo de posicao

```python
raw_x = _clamp(index_tip.x)
raw_y = _clamp(index_tip.y)
```

Como o MediaPipe usa coordenadas normalizadas:

- `x=0` = esquerda;
- `x=1` = direita;
- `y=0` = topo;
- `y=1` = base.

### 6.5.5 Calculo de velocidade

Se nao houver frame anterior, a velocidade e `0.0`.

Se houver:

```text
delta_t = max(timestamp_atual - timestamp_anterior, 1e-3)
delta_pos = distancia_euclidiana((x_atual, y_atual), (x_anterior, y_anterior))
velocity = delta_pos / delta_t
velocity_normalizada = clamp(velocity / velocity_reference)
```

Formula expandida:

```text
delta_pos = sqrt((x2 - x1)^2 + (y2 - y1)^2)
velocity = delta_pos / delta_t
velocity_normalizada = clamp(velocity / 1.3)
```

O `1e-3` evita divisao por zero.

### 6.5.6 Calculo de escala aproximada da mao

```text
hand_scale = max(dist(wrist, middle_mcp), 1e-4)
```

Objetivo:

- impedir que a abertura dependa apenas da distancia absoluta na imagem;
- aproximar uma normalizacao pelo tamanho da mao.

### 6.5.7 Calculo de abertura

```text
raw_openness = clamp(
    dist(thumb_tip, index_tip) / (hand_scale * hand_span_reference)
)
```

Com a configuracao atual:

```text
raw_openness = clamp(
    dist(thumb_tip, index_tip) / (hand_scale * 2.2)
)
```

### 6.5.8 Suavizacao

Funcao:

```python
def _smooth(value, previous, alpha):
    if previous is None:
        return value
    return previous + alpha * (value - previous)
```

Isto e uma forma de media movel exponencial discreta.

Equacao:

```text
valor_suavizado_novo = valor_anterior + alpha * (valor_bruto - valor_anterior)
```

Parametros atuais:

- posicao: `alpha = 0.3`
- velocidade: `alpha = 0.25`
- abertura: `alpha = 0.2`

Interpretacao:

- alpha menor -> mais estabilidade, menos responsividade;
- alpha maior -> mais responsividade, menos estabilidade.

### 6.5.9 Reset sem mao

Quando `hand_frame is None`:

- o estado interno e zerado;
- `MotionFeatures()` padrao e retornado;
- `active=False`.

Isto evita “memoria fantasma” quando a mao sai do quadro.

---

## 6.6 `mapping/gesture_mapper.py`

### 6.6.1 Papel

Transformar `MotionFeatures` em `SoundParameters`.

### 6.6.2 Observacao importante sobre constantes

O modulo define:

- `NOTE_NAMES`
- `STRUDEL_NOTES`

Na implementacao atual:

- `NOTE_NAMES` e usado;
- `STRUDEL_NOTES` esta declarado, mas nao participa do fluxo ativo.

Ou seja, `STRUDEL_NOTES` e hoje um artefato residual/auxiliar nao utilizado.

### 6.6.3 Escala musical

Configuracao:

- `root_midi=48`
- `octaves=3`
- `scale_intervals=(0, 3, 5, 7, 10)`

Isto gera 15 notas:

| Indice | Nota | Frequencia (Hz) |
|---|---|---:|
| 0 | C3 | 130.8128 |
| 1 | D#3 | 155.5635 |
| 2 | F3 | 174.6141 |
| 3 | G3 | 195.9977 |
| 4 | A#3 | 233.0819 |
| 5 | C4 | 261.6256 |
| 6 | D#4 | 311.1270 |
| 7 | F4 | 349.2282 |
| 8 | G4 | 391.9954 |
| 9 | A#4 | 466.1638 |
| 10 | C5 | 523.2511 |
| 11 | D#5 | 622.2540 |
| 12 | F5 | 698.4565 |
| 13 | G5 | 783.9909 |
| 14 | A#5 | 932.3275 |

### 6.6.4 Formula MIDI -> frequencia

```text
frequency = 440 * 2^((midi - 69)/12)
```

### 6.6.5 Formula MIDI -> label

```text
note_name = NOTE_NAMES[midi % 12]
octave = (midi // 12) - 1
label = f"{note_name}{octave}"
```

### 6.6.6 Mapeamento da posicao horizontal para nota

```text
note_index = round(motion.x * (len(scale) - 1))
```

Como `len(scale)=15`, então:

```text
note_index = round(motion.x * 14)
```

Consequencia:

- `x=0.0` -> indice 0 -> `C3`
- `x=1.0` -> indice 14 -> `A#5`

### 6.6.7 Mapeamento da posicao vertical para amplitude

```text
amplitude_span = max_amplitude - min_amplitude
amplitude = min_amplitude + (1 - motion.y) * amplitude_span
```

Com valores atuais:

```text
amplitude = 0.08 + (1 - y) * (0.65 - 0.08)
amplitude = 0.08 + (1 - y) * 0.57
```

Interpretacao:

- mao mais alta (`y` menor) -> gain maior;
- mao mais baixa (`y` maior) -> gain menor.

### 6.6.8 Mapeamento da mao secundaria para brilho

Na implementacao atual, o brilho usa a mao secundaria quando ela esta presente. Caso contrario, faz fallback para a mao primaria.

```text
modulator = motion.secondary, se motion.secondary.active
modulator = motion.primary, caso contrario

brightness = clamp(
    modulator.velocity * velocity_weight +
    modulator.openness * openness_weight
)
```

Com valores atuais:

```text
brightness = clamp(
    modulator.velocity * 0.6 +
    modulator.openness * 0.4
)
```

### 6.6.9 Mapeamento da mao secundaria para synth

Se a mao secundaria estiver ativa, sua posicao horizontal define o synth do Strudel:

```text
synth_index = round(motion.secondary.x * (len(secondary_synths) - 1))
synth = secondary_synths[synth_index]
```

Com os defaults atuais:

```text
secondary_synths = ("sine", "triangle", "sawtooth", "square")
```

Portanto:

- mais a esquerda -> `sine`
- meio-esquerda -> `triangle`
- meio-direita -> `sawtooth`
- mais a direita -> `square`

Se nao houver mao secundaria:

```text
synth = default_synth_name = "sawtooth"
```

### 6.6.10 Estado sem mao

Se `motion.active == False`, o mapper retorna:

- `frequency=0.0`
- `amplitude=0.0`
- `brightness=0.0`
- `note_label="--"`
- `active=False`

---

## 6.7 `utils/visualizer.py`

### 6.7.1 Papel

Gerar a camada de overlay visual que sera enviada ao navegador.

### 6.7.2 `HAND_CONNECTIONS`

Tupla com os pares de indices conectados:

- polegar
- indicador
- medio
- anelar
- minimo
- conexoes da palma

### 6.7.3 `render_overlay()`

Passos:

1. clona o frame (`frame.copy()`);
2. calcula `frame_height` e `frame_width`;
3. se houver mao, chama `_draw_hand()`;
4. define `status`;
5. monta lista `lines`;
6. desenha cada linha com `cv2.putText()`;
7. retorna a imagem anotada.

### 6.7.4 Conteudo textual atual do overlay

- titulo (`window_name`)
- status da mao
- mao primaria e mao secundaria
- string fixa `Saida ativa: navegador + Strudel`
- nota
- frequencia
- amplitude
- brilho
- synth
- velocidade e abertura da mao primaria
- velocidade e abertura da mao secundaria
- instrucao de encerramento

### 6.7.5 Desenho dos landmarks

Para cada landmark:

- converte coordenadas normalizadas em pixels;
- desenha as linhas da malha com `cv2.line`;
- desenha circulos com `cv2.circle`;
- escreve o indice com duas chamadas `cv2.putText`:
  - uma escura grossa como contorno;
  - uma branca fina por cima.

### 6.7.6 Destaques visuais

- landmark `8` (indicador) recebe cor diferenciada;
- landmarks `4` e `8` recebem raio maior.

### 6.7.7 Observacao

O overlay e o proprio artefato visual principal do backend. O frontend apenas o exibe; ele nao redesenha landmarks por conta propria.

---

## 6.8 `integration/strudel/models.py`

### 6.8.1 `StrudelState`

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

Metodo:

```python
to_payload()
```

Ele transforma a dataclass em `dict` via `asdict` e acrescenta:

```python
payload["type"] = "state"
```

### 6.8.2 `PreviewFrame`

Campos:

- `image`
- `width`
- `height`
- `timestamp`

Metodo:

```python
to_payload()
```

que adiciona:

```python
payload["type"] = "frame"
```

### 6.8.3 Significado dos dois payloads

O canal WebSocket e multiplexado semanticamente:

- mensagens de tipo `state` atualizam o motor musical e o painel textual;
- mensagens de tipo `frame` atualizam o preview visual.

---

## 6.9 `integration/strudel/note_adapter.py`

### 6.9.1 Papel

Converter labels de nota do backend Python para o token textual esperado pela API de `note(...)` do Strudel.

### 6.9.2 Estrategia

Exemplos:

- `A#4` -> `a#4`
- `C3` -> `c3`
- `Bb4` -> `bb4`

### 6.9.3 Regex

```python
NOTE_PATTERN = re.compile(r"([A-G])([#b]?)(-?\d+)")
```

Partes:

- grupo 1 -> letra base
- grupo 2 -> acidente opcional
- grupo 3 -> oitava, inclusive negativa se necessario

### 6.9.4 Notas inativas

Se `note_label` estiver em `{ "", "--", "~" }`, retorna `"~"`.

No contexto do projeto:

- `"--"` = sem nota valida no backend;
- `"~"` = repouso/ausencia no dominio Strudel.

### 6.9.5 Observacao

O adapter aceita sustenidos e bemois, mas o mapper atual do backend emite sustenidos, porque `NOTE_NAMES` usa `C#`, `D#`, `F#`, `G#`, `A#`.

---

## 6.10 `integration/strudel/code_generator.py`

### 6.10.1 Papel

Gerar uma representacao textual legivel do estado musical equivalente em Strudel.

### 6.10.2 Regras

Se `state.active == False`:

```text
hush()
```

Se `state.active == True`:

```text
note("<strudel_note>").s("<synth>").gain(<gain>).lpf(<lpf>)
```

### 6.10.3 Observacao

Esse codigo e exibido ao usuario e tambem serve como referencia conceitual. Entretanto, o frontend atual nao executa essa string por `eval`; ele reconstrui a pattern por API JS a partir do JSON estruturado.

---

## 6.11 `integration/strudel/publisher.py`

### 6.11.1 Papel

Converter `SoundParameters` em `StrudelState` e controlar quando um novo estado deve ser publicado.

### 6.11.2 `build_state()`

Regras:

```text
active = params.active
note_label = params.note_label se ativo; caso contrario "--"
strudel_note = to_strudel_note(note_label)
gain = round(params.amplitude, gain_precision) se ativo; caso contrario 0.0
brightness = round(params.brightness, 3) se ativo; caso contrario 0.0
lpf = round(lpf_min + brightness * (lpf_max - lpf_min))
frequency = params.frequency se ativo; caso contrario 0.0
synth = params.synth_name se ativo; caso contrario config.synth_name
timestamp = time.time()
code = build_code(state)
```

### 6.11.3 Formula do LPF

```text
lpf = round(400 + brightness * (4000 - 400))
```

ou:

```text
lpf = round(400 + brightness * 3600)
```

Exemplo:

- `brightness = 0.20`
- `lpf = round(400 + 0.20 * 3600)`
- `lpf = round(1120)`
- `lpf = 1120`

### 6.11.4 Politica de publicacao

`should_publish()` envia imediatamente se:

1. nao houver estado anterior;
2. `active` mudou;
3. a nota mudou e `note_change_immediate=True`;
4. `gain_delta >= gain_delta_config`;
5. `brightness_delta >= brightness_delta_config`;
6. ja passou `1/update_hz` segundos desde o ultimo envio.

Com a configuracao atual:

- `update_hz=8` -> intervalo minimo de `0.125s`
- `gain_delta=0.03`
- `brightness_delta=0.05`

### 6.11.5 Proposito dessa politica

Evitar flood do WebSocket com uma mensagem a cada frame.

Sem isso:

- o navegador receberia atualizacoes excessivas;
- o `hush() + play()` do frontend seria disparado em excesso;
- a experiencia sonora ficaria mais instavel.

---

## 6.12 `integration/strudel/preview_publisher.py`

### 6.12.1 Papel

Preparar o overlay visual para transporte eficiente ao navegador.

### 6.12.2 `should_publish()`

Usa:

```text
interval = 1 / preview_update_hz
```

Com o default:

```text
interval = 1 / 12 = 0.083333...
```

Se menos tempo que isso tiver passado, o preview nao e reenviado.

### 6.12.3 `build_frame()`

Passos:

1. redimensiona se necessario;
2. codifica como JPEG com `cv2.imencode`;
3. converte bytes para Base64;
4. prefixa com `data:image/jpeg;base64,`;
5. retorna `PreviewFrame`.

### 6.12.4 Redimensionamento

Se `width <= preview_max_width`, nada e redimensionado.

Se `width > preview_max_width`:

```text
scale = preview_max_width / width
new_width = preview_max_width
new_height = round(height * scale)
```

Exemplo com a configuracao default:

- frame original: `1280x720`
- `preview_max_width = 960`
- `scale = 960/1280 = 0.75`
- preview: `960x540`

### 6.12.5 Qualidade JPEG

`preview_jpeg_quality=72`

Trade-off:

- qualidade visual intermediaria;
- payload menor do que JPEG de alta qualidade;
- adequado para loopback local.

### 6.12.6 Consequencia estrutural

O preview enviado ao browser nao e video bruto, nao e MJPEG streaming nativo e nao e canvas; e uma sequencia de imagens JPEG encapsuladas em payloads WebSocket.

---

## 6.13 `integration/strudel/bridge_server.py`

### 6.13.1 Papel

Servidor WebSocket assíncrono que difunde payloads para todos os clientes conectados.

### 6.13.2 Modelo de concorrencia

- thread dedicada: `strudel-websocket-server`
- dentro dela: um `asyncio` event loop

### 6.13.3 Estruturas de estado

- `_clients: set[Any]`
- `_loop`
- `_server_ready: threading.Event`
- `_stop_requested: threading.Event`
- `_thread`
- `_stop_event: asyncio.Event`

### 6.13.4 Startup

`start()`:

1. cria a thread daemon;
2. inicia a thread;
3. espera ate 5 segundos por `_server_ready`.

Se a espera exceder 5 segundos:

- `RuntimeError("Servidor WebSocket do Strudel nao iniciou a tempo.")`

### 6.13.5 Publicacao

`publish(payload)`:

1. serializa com `json.dumps`;
2. agenda `_broadcast(message)` no loop async com `asyncio.run_coroutine_threadsafe`;
3. espera `future.result(timeout=1)`.

Se falhar:

- o erro e suprimido;
- o prototipo continua.

### 6.13.6 Razao da tolerancia

A ausencia de navegador conectado nao deve matar a captura da camera nem o pipeline de mapeamento.

### 6.13.7 Clientes

`_handle_client()`:

- adiciona o cliente ao set;
- consome passivamente mensagens de entrada;
- descarta o cliente ao desconectar.

Observacao:

O protocolo atual e unidirecional em pratica:

- servidor -> cliente

As mensagens do cliente, se existirem, sao ignoradas.

### 6.13.8 Broadcast

`_broadcast()`:

- percorre a copia do set de clientes;
- tenta `client.send(message)`;
- clientes que falham vao para `stale_clients`;
- depois sao removidos do set.

---

## 6.14 `integration/strudel/web_server.py`

### 6.14.1 Papel

Servidor HTTP local para a interface web.

### 6.14.2 Bibliotecas utilizadas

- `ThreadingHTTPServer`
- `SimpleHTTPRequestHandler`
- `functools.partial`
- `HTTPStatus`

### 6.14.3 Modelo

- thread dedicada `strudel-http-server`
- arquivos servidos a partir de `web/strudel/`

### 6.14.4 `base_url`

```python
return f"http://{self._host}:{self._port}"
```

### 6.14.5 Endpoint especial

`/config.json`

Resposta:

```json
{
  "wsUrl": "ws://127.0.0.1:8765"
}
```

Objetivo:

- desacoplar o frontend da configuracao hardcoded do WebSocket.

### 6.14.6 Silenciamento de logs

`log_message()` e sobrescrito para descartar mensagens do `SimpleHTTPRequestHandler`.

Objetivo:

- manter o terminal do backend mais limpo.

---

## 6.15 `integration/strudel/output.py`

### 6.15.1 Papel

Facade/orquestrador da camada de saida web.

Ele agrega:

- `StrudelPublisher`
- `PreviewPublisher`
- `StrudelBridgeServer`
- `StrudelWebServer`

### 6.15.2 `start()`

Ordem:

1. sobe o servidor WebSocket;
2. sobe o servidor HTTP;
3. opcionalmente abre o navegador.

Se qualquer erro ocorrer:

- `stop()` e chamado;
- `RuntimeError` e propagado.

### 6.15.3 `publish_state()`

1. valida `enabled`;
2. gera `StrudelState`;
3. respeita `send_inactive_state`;
4. respeita a politica de `should_publish`;
5. publica o payload `state`.

### 6.15.4 `publish_preview()`

1. valida `enabled`;
2. consulta `PreviewPublisher.should_publish()`;
3. gera `PreviewFrame`;
4. publica o payload `frame`.

### 6.15.5 `stop()`

Encerra:

1. servidor HTTP;
2. servidor WebSocket.

---

## 6.16 `web/strudel/index.html`

### 6.16.1 Papel

Definir a estrutura DOM da interface browser-first.

### 6.16.2 Dependencias front-end declaradas

- `style.css`
- `https://unpkg.com/@strudel/web@1.0.3`
- `app.js`

### 6.16.3 Estrutura principal

`<main class="layout">` contem:

1. `hero`
2. `workspace-grid`
3. `code-panel`

### 6.16.4 `hero`

Contem:

- nome do projeto;
- titulo da interface;
- descricao;
- botoes:
  - `Conectar`
  - `Ativar Audio`
  - `Parar`
- texto de status.

### 6.16.5 `workspace-grid`

Dividido em dois paines:

- `preview-panel`
- `state-panel`

### 6.16.6 `preview-panel`

Contem:

- cabecalho com badge `WebSocket`
- container `preview-frame`
- `<img id="preview-image">`
- placeholder textual inicial

### 6.16.7 `state-panel`

Exibe:

- nota
- nota Strudel
- frequencia
- gain
- brilho
- LPF
- synth
- ativo/inativo

### 6.16.8 `code-panel`

Exibe o codigo Strudel equivalente dentro de `<pre id="code-view">`.

---

## 6.17 `web/strudel/app.js`

### 6.17.1 Papel

Cliente JavaScript que:

- conecta no WebSocket;
- recebe payloads do backend;
- atualiza a UI;
- controla o runtime do Strudel;
- toca ou silencia o som no navegador.

### 6.17.2 Estado global JS

- `runtimeReady`
- `socket`
- `wsUrl`
- `playbackArmed`
- `latestState`

### 6.17.3 Carregamento da configuracao

`loadConfig()` faz:

1. `fetch("./config.json")`
2. valida `response.ok`
3. parseia JSON
4. extrai `wsUrl`
5. atualiza `status`

### 6.17.4 Estado textual

`renderState(state)` aplica:

- `note_label`
- `strudel_note`
- `frequency.toFixed(1)`
- `gain.toFixed(3)`
- `brightness.toFixed(3)`
- `lpf`
- `synth`
- `active`
- `code`

### 6.17.5 Preview

`renderPreview(frame)`:

- troca `src` da imagem pelo `data:image/jpeg;base64,...`
- atualiza `width` e `height`
- exibe a imagem
- oculta o placeholder

### 6.17.6 Inicializacao do runtime Strudel

`ensureRuntime()`:

- valida que `initStrudel` existe;
- chama `Promise.resolve(initStrudel())`;
- marca `runtimeReady=true`.

Uso de `Promise.resolve(...)`:

- normaliza a chamada caso `initStrudel()` seja sync ou async.

### 6.17.7 Construcao da pattern

```javascript
note(state.strudel_note).s(state.synth).gain(state.gain).lpf(state.lpf)
```

Observacao crucial:

- `state.frequency` nao e usada aqui.
- O playback atual e baseado no token `note(...)`, nao em frequencia absoluta.

### 6.17.8 Aplicacao do estado musical

`applyState(state)`:

1. guarda `latestState`;
2. atualiza os campos da UI;
3. se runtime nao estiver pronto ou o audio nao estiver armado, para ali;
4. se `active=false`, chama `hush()`;
5. se `active=true`, chama:
   - `hush()`
   - `buildPattern(state).play()`

### 6.17.9 Consequencia sonora importante

O frontend atual substitui a pattern anterior agressivamente:

```text
hush() + nova pattern.play()
```

Isso privilegia previsibilidade e simplicidade, mas nao suavidade de transicao.

### 6.17.10 Dispatch de payloads

`handlePayload(payload)`:

- `type === "state"` -> `applyState(payload)`
- `type === "frame"` -> `renderPreview(payload)`

### 6.17.11 WebSocket

`connectSocket()`:

- evita reconectar se `socket !== null`;
- cria `new WebSocket(wsUrl)`;
- atualiza estado visual em:
  - `open`
  - `message`
  - `close`
  - `error`

### 6.17.12 Botoes

#### Conectar

- abre o WebSocket.

#### Ativar Audio

- chama `ensureRuntime()`;
- define `playbackArmed = true`;
- se `latestState` ja existir, reaplica o estado imediatamente.

Esse detalhe e importante:

- se o backend ja estiver publicando antes do clique, o usuario nao precisa esperar um novo gesto para ouvir som.

#### Parar

- `playbackArmed = false`
- se runtime existe, chama `hush()`

---

## 6.18 `web/strudel/style.css`

### 6.18.1 Papel

Definir o sistema visual da interface browser-first.

### 6.18.2 Variaveis CSS

`--bg`, `--panel`, `--ink`, `--muted`, `--accent`, `--accent-strong`, `--border`, `--shadow`

### 6.18.3 Estrategia de layout

- container central responsivo com largura maxima de `1280px`
- grid principal para preview + estado
- fallback mobile abaixo de `980px`

### 6.18.4 Preview

`.preview-frame`:

- fundo escuro com gradiente;
- `overflow: hidden`;
- imagem responsiva;
- placeholder centralizado.

### 6.18.5 Estado e codigo

- `state-grid` para os cards numericos;
- `pre` estilizado como bloco de codigo escuro.

### 6.18.6 Observacao

Toda a apresentacao visual do frontend atual e puramente declarativa em HTML/CSS. O backend nao envia instrucoes de layout, apenas dados.

---

## 7. Integracao Python -> Navegador -> Strudel

## 7.1 Camadas envolvidas

1. Python gera `SoundParameters` e `overlay`
2. Python converte isso em:
   - `StrudelState`
   - `PreviewFrame`
3. Python serializa para JSON
4. WebSocket entrega ao navegador
5. JavaScript processa por tipo
6. Strudel runtime toca a pattern

## 7.2 Schema de `state`

Exemplo representativo:

```json
{
  "type": "state",
  "active": true,
  "note_label": "A#4",
  "strudel_note": "a#4",
  "frequency": 466.1638,
  "gain": 0.35,
  "brightness": 0.2,
  "lpf": 1120,
  "synth": "square",
  "hands_detected": 2,
  "primary_handedness": "right",
  "secondary_handedness": "left",
  "brightness_source": "left",
  "code": "note(\"a#4\").s(\"square\").gain(0.35).lpf(1120)",
  "timestamp": 1760000000.0
}
```

## 7.3 Schema de `frame`

Exemplo estrutural:

```json
{
  "type": "frame",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "width": 960,
  "height": 540,
  "timestamp": 1760000000.0
}
```

## 7.4 Propriedades da integracao

- o canal e local (`127.0.0.1`);
- o transporte e texto JSON;
- nao ha autenticação;
- nao ha compressao WebSocket explicita;
- nao ha ACK do cliente;
- nao ha fila historica no servidor;
- o cliente recebe apenas o que estiver sendo empurrado no momento em que esta conectado.

---

## 8. Calculos E Formulas Consolidadas

## 8.1 Distancia euclidiana

```text
dist((x1, y1), (x2, y2)) = sqrt((x2 - x1)^2 + (y2 - y1)^2)
```

## 8.2 Clamp

```text
clamp(v, min, max) = max(min, min(max, v))
```

No projeto, o default e:

```text
clamp(v, 0, 1)
```

## 8.3 Suavizacao exponencial

```text
smooth(v, prev, alpha) =
  v, se prev for None
  prev + alpha * (v - prev), caso contrario
```

## 8.4 Velocidade normalizada

```text
delta_t = max(t2 - t1, 1e-3)
delta_pos = dist((x2, y2), (x1, y1))
velocity = delta_pos / delta_t
velocity_norm = clamp(velocity / 1.3)
```

## 8.5 Abertura normalizada

```text
hand_scale = max(dist(wrist, middle_mcp), 1e-4)
openness = clamp(dist(thumb_tip, index_tip) / (hand_scale * 2.2))
```

## 8.6 Escolha da nota

```text
note_index = round(x * 14)
```

## 8.7 Amplitude

```text
amplitude = 0.08 + (1 - y) * 0.57
```

## 8.8 Brilho

```text
brightness = clamp(velocity * 0.6 + openness * 0.4)
```

## 8.9 LPF no Strudel

```text
lpf = round(400 + brightness * 3600)
```

## 8.10 Code generation

Se ativo:

```text
note("<nota>").s("<synth>").gain(<gain>).lpf(<lpf>)
```

Se inativo:

```text
hush()
```

---

## 9. Sequencia Exata De Responsabilidade Por Camada

## 9.1 HandTracker

- responsabilidade: converter camera em `HandsFrame`
- nao sabe nada sobre som

## 9.2 MovementProcessor

- responsabilidade: converter landmarks em features
- nao sabe nada sobre Strudel ou transporte web

## 9.3 GestureMapper

- responsabilidade: converter features em semantica musical
- nao sabe nada sobre WebSocket, HTML ou JPEG

## 9.4 Visualizer

- responsabilidade: converter frame + estado em overlay visual
- nao sabe nada sobre WebSocket ou Strudel runtime

## 9.5 StrudelOutput

- responsabilidade: publicar estado musical e preview visual
- nao detecta mao, nao calcula mapeamento

## 9.6 app.js

- responsabilidade: consumir payloads e controlar a UI/browser audio
- nao sabe nada sobre MediaPipe ou OpenCV

---

## 10. Artefatos Visuais E Diagramas

## 10.1 Artefatos UML atuais

### Diagramas fonte

- [Diagrama de Componentes](./uml/component-diagram.puml)
- [Diagrama de Sequencia](./uml/sequence-diagram.puml)
- [Diagrama de Classes](./uml/class-diagram.puml)

### Diagramas renderizados em PNG

- ![Diagrama de Componentes](./uml/component-diagram.png)
- ![Diagrama de Sequencia](./uml/sequence-diagram.png)
- ![Diagrama de Classes](./uml/class-diagram.png)

## 10.2 Artefatos da interface web

- `web/strudel/index.html`
- `web/strudel/style.css`
- `web/strudel/app.js`

Esses tres arquivos compoem todo o frontend da implementacao atual.

## 10.3 Artefato visual central do runtime

O artefato visual mais importante em execucao nao e um canvas dinamico autossuficiente, e sim:

- um `overlay` produzido pelo backend;
- compactado em JPEG;
- enviado por WebSocket;
- desenhado em `<img>` no navegador.

Portanto, o browser atual atua mais como terminal visual enriquecido do que como motor de renderizacao de landmarks.

---

## 11. Testes E Validacao

## 11.1 `tests/test_pipeline.py`

Valida:

- ativacao do `MovementProcessor` quando ha mao;
- calculo de velocidade entre dois frames;
- aumento de pitch quando a mao vai para a direita;
- silenciamento sem mao.

### Estrategia

O arquivo cria maos sinteticas com 21 landmarks e timestamps controlados.

## 11.2 `tests/test_strudel_integration.py`

Valida:

- adaptacao de notas para Strudel;
- codigo `hush()` em estado inativo;
- geracao de `lpf`;
- politica de `should_publish` para estado musical;
- geracao de `data:image/jpeg;base64,...` para o preview;
- controle de taxa de publicacao do preview.

### Observacao importante

Os testes de `StrudelPublisher` sobrescrevem `synth_name` para `"triangle"` em alguns cenarios. Isso nao altera o default do runtime do projeto, que hoje e `"sawtooth"`. Trata-se apenas de isolamento de teste.

## 11.3 Validacao operacional manual

O fluxo manual esperado e:

1. iniciar `main.py`
2. abrir `http://127.0.0.1:8080`
3. clicar `Conectar`
4. clicar `Ativar Audio`
5. mover a mao
6. observar:
   - preview com landmarks;
   - estado textual mudando;
   - codigo Strudel equivalente;
   - resposta sonora do browser

---

## 12. Limitacoes Tecnicas Atuais

1. O sistema captura ate duas maos e hoje distribui papeis entre elas, mas a segunda mao ainda atua apenas na camada de timbre/synth continuo, sem gerar eventos ou patterns temporais proprios.
2. O frontend substitui o som por `hush() + play()` em vez de transicao suave.
3. A nota e discreta, nao continua.
4. O preview trafega como JPEG base64, o que aumenta payload.
5. Nao ha historico gestual longo para gerar patterns.
6. Nao ha persistencia de sessao nem gravação de gestos.
7. O `WebSocket` e unidirecional na pratica.
8. O backend nao faz autenticacao local.
9. `SoundParameters.frequency` e observacional no frontend atual.
10. O browser precisa de gesto do usuario para liberar audio por politica de autoplay.

---

## 13. Interpretacao Arquitetural Final

A implementacao atual pode ser resumida assim:

- o corpo fornece entrada gestual;
- o MediaPipe fornece estrutura anatomica;
- o `MovementProcessor` converte anatomia em cinetica;
- o `GestureMapper` converte cinetica em semantica musical;
- o `Visualizer` converte estado interno em overlay legivel;
- o `StrudelOutput` converte estado e overlay em protocolos de rede locais;
- o navegador converte esses protocolos em interface e audio Strudel.

Em termos formais:

```text
frame de camera
-> landmarks
-> features de movimento
-> parametros musicais
-> estado Strudel / preview visual
-> navegador
-> runtime Strudel
-> audio
```

Essa e a forma mais precisa de descrever a implementacao atual do `MoveCodeBeats`.

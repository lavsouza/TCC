# Arquitetura Do Sistema

Este documento descreve a arquitetura atual do `MoveCodeBeats` em sua fase browser-first. O objetivo e mostrar como o movimento capturado pela camera percorre cada camada do sistema ate resultar em preview visual e execucao Strudel no navegador.

## Versao UML

Os diagramas UML em PlantUML estao em `docs/uml/`.

## Visao Geral Em Camadas

```mermaid
flowchart LR
    user["Usuario<br/>Movimenta a mao"] --> camera["Camera / Webcam"]
    camera --> capture["Camada de Captura<br/>capture/hand_tracker.py"]
    capture --> processing["Camada de Processamento<br/>processing/movement_processor.py"]
    processing --> mapping["Camada de Mapeamento Musical<br/>mapping/gesture_mapper.py"]
    mapping --> strudel["Camada de Saida Web<br/>integration/strudel/"]
    capture --> visualizer["Camada de Visualizacao<br/>utils/visualizer.py"]
    processing --> visualizer
    mapping --> visualizer
    visualizer --> strudel
    strudel --> browser["Navegador<br/>Preview + Codigo + Strudel"]

    config["Configuracao Central<br/>utils/config.py"] --> capture
    config --> processing
    config --> mapping
    config --> strudel
    config --> visualizer

    models["Modelos de Dados<br/>utils/models.py"] --> capture
    models --> processing
    models --> mapping
    models --> strudel
    models --> visualizer

    main["Orquestracao do Sistema<br/>main.py"] --> capture
    main --> processing
    main --> mapping
    main --> visualizer
    main --> strudel
```

## Fluxo De Dados Em Tempo Real

```mermaid
sequenceDiagram
    participant U as Usuario
    participant C as Camera
    participant H as HandTracker
    participant P as MovementProcessor
    participant M as GestureMapper
    participant V as Visualizer
    participant O as StrudelOutput
    participant B as Browser

    U->>C: Movimenta a mao em frente a camera
    C->>H: Entrega frame de video
    H->>H: Detecta landmarks com MediaPipe
    H->>P: HandFrame
    P->>P: Calcula posicao, velocidade e abertura
    P->>M: MotionFeatures
    M->>M: Traduz gesto para parametros sonoros
    M->>O: SoundParameters
    H->>V: Frame + landmarks
    P->>V: Features processadas
    M->>V: Nota, frequencia, brilho e estado
    V->>O: Overlay da camera
    O->>B: Estado musical por WebSocket
    O->>B: Preview visual por WebSocket
    B-->>U: Interface visual + execucao Strudel
```

## Papel De Cada Camada

- `main.py`: inicia o sistema, instancia os modulos, controla o loop principal e encerra os recursos corretamente.
- `capture/hand_tracker.py`: abre a camera, prepara o modelo do MediaPipe, detecta a mao e converte o resultado para a estrutura `HandFrame`.
- `processing/movement_processor.py`: transforma landmarks em features semanticas mais estaveis, como posicao suavizada, velocidade e abertura da mao.
- `mapping/gesture_mapper.py`: traduz essas features em parametros musicais e acusticos, como nota, frequencia, amplitude e brilho.
- `integration/strudel/`: publica o estado Strudel, gera o codigo equivalente, expande o preview da camera e entrega tudo para o navegador.
- `utils/visualizer.py`: desenha a malha da mao, os indices dos landmarks e os valores principais do sistema para depuracao e demonstracao.
- `utils/config.py`: centraliza os parametros configuraveis do sistema.
- `utils/models.py`: define as estruturas de dados trocadas entre as camadas.
- `tests/`: valida partes importantes da logica sem depender de camera real.

## Estruturas De Dados Que Interligam O Sistema

```mermaid
flowchart TD
    raw["Frame da camera"] --> hand["HandFrame<br/>landmarks + handedness + timestamp"]
    hand --> motion["MotionFeatures<br/>x, y, velocidade, abertura"]
    motion --> sound["SoundParameters<br/>frequencia, amplitude, brilho"]
    sound --> state["StrudelState<br/>note, gain, lpf, codigo"]
    raw --> overlay["Overlay visual<br/>camera + anotacoes"]
    overlay --> preview["PreviewFrame<br/>JPEG + metadados"]
    state --> browser["Navegador"]
    preview --> browser
```

## Justificativa Arquitetural

- A separacao em camadas reduz acoplamento e facilita manutencao.
- O uso de estruturas de dados intermediarias torna o fluxo claro e testavel.
- A centralizacao da interface no navegador aproxima o prototipo da ideia central de integracao com Strudel.
- A remocao do sintetizador local reduz redundancia e concentra a evolucao do projeto na traducao gesto -> codigo executavel.

# Arquitetura Do Sistema

Este documento descreve a arquitetura atual do `MoveCodeBeats` em uma forma visual e textual. O objetivo e mostrar como o movimento capturado pela camera percorre cada camada do sistema ate resultar em audio em tempo real.

## Versao UML

Os diagramas UML em PlantUML estao em `docs/uml/`:

- `docs/uml/component-diagram.puml`
- `docs/uml/sequence-diagram.puml`
- `docs/uml/class-diagram.puml`

## Visao Geral Em Camadas

```mermaid
flowchart LR
    user["Usuario<br/>Movimenta a mao"] --> camera["Camera / Webcam"]
    camera --> capture["Camada de Captura<br/>capture/hand_tracker.py"]
    capture --> processing["Camada de Processamento<br/>processing/movement_processor.py"]
    processing --> mapping["Camada de Mapeamento Musical<br/>mapping/gesture_mapper.py"]
    mapping --> sound["Camada de Sintese Sonora<br/>sound/sound_engine.py"]
    sound --> output["Saida de Audio<br/>Alto-falantes / Fones"]

    capture --> visualizer["Camada de Visualizacao<br/>utils/visualizer.py"]
    processing --> visualizer
    mapping --> visualizer
    visualizer --> screen["Janela OpenCV"]

    config["Configuracao Central<br/>utils/config.py"] --> capture
    config --> processing
    config --> mapping
    config --> sound
    config --> visualizer

    models["Modelos de Dados<br/>utils/models.py"] --> capture
    models --> processing
    models --> mapping
    models --> sound
    models --> visualizer

    main["Orquestracao do Sistema<br/>main.py"] --> capture
    main --> processing
    main --> mapping
    main --> sound
    main --> visualizer
```

## Fluxo De Dados Em Tempo Real

```mermaid
sequenceDiagram
    participant U as Usuario
    participant C as Camera
    participant H as HandTracker
    participant P as MovementProcessor
    participant M as GestureMapper
    participant S as SoundEngine
    participant V as Visualizer

    U->>C: Movimenta a mao em frente a camera
    C->>H: Entrega frame de video
    H->>H: Detecta landmarks com MediaPipe
    H->>P: HandFrame
    P->>P: Calcula posicao, velocidade e abertura
    P->>M: MotionFeatures
    M->>M: Traduz gesto para parametros sonoros
    M->>S: SoundParameters
    M->>V: Nota, frequencia, brilho e estado
    H->>V: Frame + landmarks
    P->>V: Features processadas
    S->>S: Atualiza oscilador e gera bloco de audio
    S-->>U: Som em tempo real
    V-->>U: Feedback visual na tela
```

## Papel De Cada Camada

- `main.py`: inicia o sistema, instancia os modulos, controla o loop principal e encerra os recursos corretamente.
- `capture/hand_tracker.py`: abre a camera, prepara o modelo do MediaPipe, detecta a mao e converte o resultado para a estrutura `HandFrame`.
- `processing/movement_processor.py`: transforma landmarks em features semanticas mais estaveis, como posicao suavizada, velocidade e abertura da mao.
- `mapping/gesture_mapper.py`: traduz essas features em parametros musicais e acusticos, como nota, frequencia, amplitude e brilho.
- `sound/sound_engine.py`: recebe os parametros sonoros e mantem um sintetizador digital continuo, responsavel pela geracao do audio.
- `utils/visualizer.py`: desenha a malha da mao, os indices dos landmarks e os valores principais do sistema para depuracao e demonstracao.
- `utils/config.py`: centraliza os parametros configuraveis do sistema.
- `utils/models.py`: define as estruturas de dados trocadas entre as camadas.
- `tests/test_pipeline.py`: valida partes importantes da logica sem depender de camera ou audio reais.

## Estruturas De Dados Que Interligam O Sistema

```mermaid
flowchart TD
    raw["Frame da camera"] --> hand["HandFrame<br/>landmarks + handedness + timestamp"]
    hand --> motion["MotionFeatures<br/>x, y, velocidade, abertura"]
    motion --> sound["SoundParameters<br/>frequencia, amplitude, brilho"]
    sound --> audio["Bloco de audio digital"]
```

## Justificativa Arquitetural

- A separacao em camadas reduz acoplamento e facilita manutencao.
- O uso de estruturas de dados intermediarias torna o fluxo claro e testavel.
- A sintese local em tempo real permite validar rapidamente a relacao entre gesto e som.
- A arquitetura ja prepara o caminho para uma etapa futura de integracao com Strudel, SuperCollider ou outro ambiente de live coding.

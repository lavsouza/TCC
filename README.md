# MoveCodeBeats

Prototipo inicial de TCC para transformar movimentos corporais em parametros musicais. Nesta fase o projeto foca em capturar a mao, extrair features de movimento e publicar uma interface unificada no navegador, combinando preview da camera com overlay e execucao Strudel.

## Arquitetura revisada

O projeto foi reorganizado em uma pipeline pequena separada em camadas:

1. `capture/hand_tracker.py`
   Responsavel por abrir a camera, espelhar o feed e extrair landmarks da mao com MediaPipe.
2. `processing/movement_processor.py`
   Converte landmarks em features mais estaveis por mao: posicao suavizada, velocidade do indicador e abertura entre polegar e indicador. A etapa atual produz uma mao primaria, uma secundaria e uma primeira camada de gestos discretos na mao primaria (`pinch`, `release`, `hold`, `sweep`).
3. `mapping/gesture_mapper.py`
   Traduz as features em parametros musicais coerentes: a mao primaria controla nota e gain, enquanto a mao secundaria controla brilho e escolha do synth no Strudel.
4. `integration/strudel/`
   Publica o estado musical do prototipo, incorpora o preset manual selecionado, gera o codigo Strudel equivalente e envia tudo para a interface web por HTTP + WebSocket.
5. `utils/visualizer.py`
   Desenha a malha da mao, os indices dos landmarks e os valores principais do sistema sobre o frame da camera.
6. `main.py`
   Orquestra o ciclo principal, atualiza a ponte web e faz o cleanup da camera e dos servidores locais.

O desenho da arquitetura do sistema esta em `docs/architecture.md`.
Os diagramas UML em PlantUML estao em `docs/uml/`.
O detalhamento tecnico completo da implementacao atual esta em `docs/implementation-deep-dive.md`.
O relatorio sintetico de handoff para outro assistente de IA esta em `docs/ai-handoff-report.md`.

## Por que esta arquitetura e melhor para o TCC

- Separa claramente captura, processamento, mapeamento e saida web.
- Centraliza o prototipo no navegador, mais alinhado ao caminho de integracao com Strudel.
- Facilita trocar a traducao atual por patterns e eventos gestuais mais sofisticados.
- Permite demonstracao visual e sonora em uma unica interface.

## Mapeamento atual

- Mao primaria: movimento horizontal (eixo x) do indicador -> escolha de nota em escala pentatonica menor.
- Mao primaria: movimento vertical (eixo y) do indicador -> gain.
- Mao secundaria: movimento horizontal (eixo x) -> escolha do synth entre `sine`, `triangle`, `sawtooth` e `square`.
- Mao secundaria: velocidade + abertura entre polegar e indicador -> brilho timbrico, convertido depois em LPF no Strudel.
- Se a mao secundaria nao estiver presente, o brilho volta a ser calculado pela mao primaria e o synth assume o default `sawtooth`.
- Gestos discretos da mao primaria:
  - `pinch` intensifica a execucao atual;
  - `release` relaxa a articulacao logo apos a soltura;
  - `hold` ativa uma camada ritmica continua;
  - `sweep` alterna variacoes simples de pattern no Strudel.
- Presets manuais de Strudel:
  - `neutral`
  - `happy`
  - `sad`
  - `angry`

Os presets sao selecionados manualmente na interface e funcionam, nesta etapa, como substitutos temporarios da futura classificacao emocional baseada em dataset.

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

Ao iniciar:

1. o terminal exibe a URL local da interface, por padrao `http://127.0.0.1:8080`
2. abra essa URL no navegador
3. clique em `Conectar`
4. clique em `Ativar Audio`
5. escolha um preset manual no seletor da interface

Se `8080` ou `8765` estiverem ocupadas ou bloqueadas no Windows, o prototipo tenta automaticamente as proximas portas livres dentro de uma pequena faixa local e imprime a URL final no terminal.

Para encerrar o prototipo, use `Ctrl+C` no terminal onde o backend Python esta rodando.

## Interface Browser-First

O prototipo agora funciona sem a janela local do OpenCV e sem o sintetizador local anterior.

- O backend Python continua responsavel pela captura da camera e pela deteccao da mao.
- O overlay visual e convertido em preview JPEG e enviado ao navegador via WebSocket.
- O estado musical atual tambem e enviado ao navegador.
- A pagina renderiza o preview da camera sem o bloco textual antigo sobre a imagem, mostra os parametros atuais em um painel proprio e executa o Strudel diretamente no browser.
- A pagina tambem permite selecionar manualmente um preset sonoro, que altera ritmo base, velocidade, ganho base, filtro e synth padrao.

Nesta versao, o sistema ainda trabalha com estado continuo e nao com patterns gestuais complexos.

## Expansao Para Duas Maos

- A captura agora aceita ate duas maos no MediaPipe.
- O overlay visual ja desenha as duas maos quando elas estao presentes.
- O backend informa qual mao esta sendo usada como mao primaria e qual esta atuando como mao secundaria.
- A mao primaria controla nota e gain.
- A mao secundaria controla brilho timbrico e escolha do synth do Strudel.
- Na ausencia da mao secundaria, o sistema faz fallback para um modo de uma mao, preservando a tocabilidade do prototipo.

## Proximas etapas sugeridas

- Definir eventos gestuais discretos para gerar patterns Strudel mais expressivos
- Expandir o papel da segunda mao para controlar eventos, patterns e modulacoes temporais mais complexas
- Substituir a selecao manual de preset por classificacao automatica de emocao quando a etapa de dataset/classificador entrar no projeto

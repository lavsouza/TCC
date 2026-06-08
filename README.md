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
   Publica o estado musical do prototipo, resolve cenas Strudel multicamada, combina o perfil expressivo com a modulacao gestual, gera o codigo equivalente e envia tudo para a interface web por HTTP + WebSocket.
5. `utils/visualizer.py`
   Desenha a malha da mao, os indices dos landmarks e a identificacao de cada mao sobre o frame da camera.
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
## Perfis expressivos parametricos

O sistema oferece quatro categorias expressivas simuladas:

| Perfil | Categoria interna | BPM | Densidade | Intensidade | Caracteristica |
| --- | --- | ---: | ---: | ---: | --- |
| Neutro | `neutral` | 92 | 1.00 | 1.00 | Estavel e equilibrado |
| Alegria | `joy` | 120 | 1.18 | 1.08 | Rapido, luminoso e variado |
| Tristeza | `sadness` | 68 | 0.74 | 0.88 | Lento, espacoso e suave |
| Raiva | `anger` | 136 | 1.24 | 1.16 | Denso, repetitivo e intenso |

Cada perfil define um espaco de possibilidades musicais e uma cena propria. A cena e uma receita estruturada de camadas que pode combinar melodia, harmonia, baixo, percussao e textura. O pattern final continua variando conforme a nota, o brilho, o synth e os gestos capturados.

| Perfil | Cena | Estrutura sonora principal |
| --- | --- | --- |
| Neutro | Pulso equilibrado | Melodia, baixo discreto e bateria regular |
| Alegria | Movimento luminoso | Arpejos, harmonia maior, sincopa e textura aguda |
| Tristeza | Espaco suspenso | Notas longas, acorde menor, drone e grande ambiencia |
| Raiva | Pressao fragmentada | Repeticao densa, ritmos euclidianos, bit crush e distorcao |

O compilador usa recursos nativos do Strudel como `stack`, `setcpm`, `euclid`,
`euclidRot`, `palindrome`, envelopes de ataque/release, panorama, delay, reverb,
filtros, `shape`, `distort` e `crush`. As variacoes sao deterministicas para
facilitar comparacao experimental e reproducao dos testes.

O runtime web usa `@strudel/web@1.3.0` e carrega explicitamente o banco
`github:tidalcycles/dirt-samples`, necessario para as camadas de bateria
(`bd`, `sd`, `hh`, `cp`, `rim` e `oh`). Atualizacoes gestuais substituem o
pattern com `setPattern(...)` sem reiniciar o relogio musical, permitindo que
os ciclos ritmicos avancem normalmente.

Cada cena tambem possui um `master_gain` aplicado depois da soma das camadas.
Esse ganho compensa a reducao causada pelos ganhos relativos de melodia, baixo,
bateria e textura, mantendo margem menor nas cenas mais distorcidas.

Para evitar transicoes quebradas, o navegador:

- limita atualizacoes continuas do pattern a aproximadamente 150 ms;
- prioriza mudancas estruturais como gesto, synth, pattern e perfil;
- suaviza gain, brilho e LPF exponencialmente usando `transition_seconds`;
- tolera perdas de rastreamento de ate 360 ms antes de interromper o scheduler.

A cena de Raiva usa uma politica um pouco mais conservadora porque possui mais
ataques por ciclo: atualizacao continua a cada 240 ms, tolerancia de rastreamento
de 520 ms e mudanca de synth tratada como modulacao continua. Seus envelopes
tambem possuem releases maiores para evitar microvazios entre eventos densos.

Nesta etapa, a categoria e escolhida manualmente e publicada com `emotion_source="manual"` e `emotion_confidence=1.0`. Essa selecao simula a futura saida de um classificador treinado com movimentos corporais representados. O sistema ainda nao detecta emocoes internas reais.

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
5. escolha uma categoria expressiva simulada no seletor da interface

Na primeira ativacao, o carregamento dos samples de bateria pode levar alguns
segundos, dependendo da conexao.

Se `8080` ou `8765` estiverem ocupadas ou bloqueadas no Windows, o prototipo tenta automaticamente as proximas portas livres dentro de uma pequena faixa local e imprime a URL final no terminal.

Para encerrar o prototipo, use `Ctrl+C` no terminal onde o backend Python esta rodando.

## Interface Browser-First

O prototipo agora funciona sem a janela local do OpenCV e sem o sintetizador local anterior.

- O backend Python continua responsavel pela captura da camera e pela deteccao da mao.
- O overlay visual e convertido em preview JPEG e enviado ao navegador via WebSocket.
- O estado musical atual tambem e enviado ao navegador.
- A pagina renderiza o preview da camera sem o bloco textual antigo sobre a imagem, mostra os parametros atuais em um painel proprio e executa o Strudel diretamente no browser.
- A pagina permite selecionar manualmente um perfil expressivo, que altera ritmo, velocidade, faixas de gain/LPF, intensidade, variacao e synth padrao.
- O painel informa a cena musical e as camadas ativas, enquanto a camera permanece livre de blocos textuais.
- A escolha e enviada ao backend por WebSocket; o frontend nao contem a regra musical principal.

Nesta versao, o sistema combina estado continuo com eventos gestuais discretos e cenas Strudel multicamada.

## Expansao Para Duas Maos

- A captura agora aceita ate duas maos no MediaPipe.
- O overlay visual ja desenha as duas maos quando elas estao presentes.
- O backend informa qual mao esta sendo usada como mao primaria e qual esta atuando como mao secundaria.
- A mao primaria controla nota e gain.
- A mao secundaria controla brilho timbrico e escolha do synth do Strudel.
- Na ausencia da mao secundaria, o sistema faz fallback para um modo de uma mao, preservando a tocabilidade do prototipo.

## Proximas etapas sugeridas

- Expandir a interpolacao para crossfade completo entre as camadas de cenas diferentes
- Expandir o papel da segunda mao para controlar eventos, patterns e modulacoes temporais mais complexas
- Definir o protocolo e coletar o dataset de movimentos corporais representando as quatro categorias
- Treinar o classificador e substituir `emotion_source="manual"` por `emotion_source="classifier"`
- Adicionar suavizacao temporal das probabilidades antes de trocar ou interpolar perfis

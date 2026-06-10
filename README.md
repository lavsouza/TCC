# MoveCodeBeats

Prototipo de TCC que transforma movimentos das maos em estruturas musicais
executadas no Strudel. O backend captura a camera com MediaPipe, extrai features
e gestos, aplica o mapeamento musical e transmite o estado. O frontend React
renderiza a performance e executa o motor sonoro no navegador.

## Tecnologias

- Python 3.11+
- FastAPI 0.136.3 e Uvicorn 0.49.0
- MediaPipe 0.10.33 e OpenCV 4.13.0.92
- React 19.2.7, TypeScript 6.0.3 e Vite 8.0.16
- Strudel Web 1.3.0

## Arquitetura

```text
Camera -> MediaPipe -> MovementProcessor -> GestureMapper
       -> StrudelPublisher -> FastAPI/WebSocket
       -> React -> PatternBuilder -> StrudelEngine -> WebAudio
```

O repositorio continua monolitico, mas possui duas aplicacoes desacopladas:

- `backend/`: API, sessoes, contratos e runtime de captura.
- `frontend/`: interface React e runtime Strudel.
- `capture/`: camera e deteccao de landmarks.
- `processing/`: suavizacao, features e gestos temporais.
- `mapping/`: traducao das features em parametros musicais.
- `integration/strudel/`: perfis, cenas e estado musical declarativo.
- `contracts/`: protocolo publico REST/WebSocket.
- `tests/`: testes do dominio e da API.

O detalhamento visual esta em `docs/architecture.md` e a decisao arquitetural em
`docs/adr/0001-fastapi-react-boundary.md`.

## Mapeamento atual

- Mao primaria no eixo X: nota da escala pentatonica menor.
- Mao primaria no eixo Y: gain.
- Mao secundaria no eixo X: synth.
- Velocidade e abertura da mao secundaria: brilho e filtro LPF.
- Sem a segunda mao, a mao primaria assume o brilho e o synth volta ao padrao.
- `pinch`: acentua a cena.
- `release`: relaxa ganho e ambiencia.
- `hold`: adiciona uma camada continua propria do perfil.
- `sweep`: altera a variacao ritmica para esquerda ou direita.

Os perfis `neutral`, `happy`, `sad` e `angry` definem cenas multicamada
distintas. A escolha ainda e manual; o contrato ja guarda origem e confianca
para uma futura selecao por classificador.

## Instalacao

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

Na primeira execucao, o modelo `hand_landmarker.task` pode ser baixado para
`models/`.

## Execucao

Terminal 1, na raiz:

```powershell
python main.py
```

A API fica em `http://127.0.0.1:8000`. A documentacao OpenAPI fica em
`http://127.0.0.1:8000/docs`.

Terminal 2:

```powershell
cd frontend
npm run dev
```

Abra `http://127.0.0.1:5173`. A interface cria uma sessao, conecta o WebSocket
automaticamente e mostra o preview. O audio so inicia depois do clique em
`Ativar audio`, conforme a politica WebAudio dos navegadores.

Para executar a API sem abrir a camera:

```powershell
$env:MCB_CAPTURE_ENABLED="false"
python main.py
```

## API v1

- `GET /api/v1/health`
- `GET /api/v1/catalog`
- `GET /api/v1/profiles`
- `GET /api/v1/profiles/{profile_id}`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `PATCH /api/v1/sessions/{session_id}/profile`
- `WS /api/v1/sessions/{session_id}/stream`

Os eventos usam envelope com `schema_version`, `type`, `timestamp`,
`session_id` e `data`. Consulte `contracts/README.md`.

## Testes

```powershell
python -m unittest discover -s tests -v
cd frontend
npm run test
npm run build
```

## Limitacoes atuais

- A camera e o perfil ativo ainda sao compartilhados pelo processo Python.
- O backend precisa executar no computador que possui a webcam.
- O preview e enviado como JPEG Base64; WebRTC sera mais eficiente em uma fase
  posterior.
- Nao existe autenticacao, persistencia de sessoes ou classificador emocional.
- A captura diretamente no navegador nao faz parte das fases 0 a 4.

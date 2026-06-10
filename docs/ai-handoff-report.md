# Handoff Tecnico Atual

## Estado

O MoveCodeBeats usa FastAPI no backend e React/TypeScript no frontend. O audio
local Python foi removido e Strudel 1.3.0 permanece como unico motor sonoro.

## Fluxo

1. `CaptureRuntime` abre a camera e executa `HandTracker`.
2. `StateService` chama `MovementProcessor`, `GestureMapper`,
   `StrudelPublisher` e `PreviewPublisher`.
3. `RealtimeHub` envia `music.state.v1` e `preview.frame.v1`.
4. React cria uma sessao REST e conecta ao WebSocket.
5. `patternBuilder.ts` converte a cena declarativa em pattern Strudel.
6. `engine.ts` aplica CPS, suavizacao e `setPattern`.

## Decisoes Importantes

- Contratos externos sao versionados em `1.0`.
- O frontend nunca executa codigo arbitrario enviado pelo backend.
- Perfis e cenas continuam definidos no Python.
- A compilacao do pattern existe somente no TypeScript.
- O runtime Strudel e carregado sob demanda no clique de audio.
- A camera roda em thread separada do event loop FastAPI.
- Se a camera falhar, a API continua ativa em estado degradado.

## Comandos

```powershell
python main.py
cd frontend
npm run dev
```

Testes:

```powershell
python -m unittest discover -s tests -v
cd frontend
npm run test
npm run build
```

## Limites

- Camera e perfil sao globais no processo.
- Sessoes nao persistem.
- Preview Base64 ainda nao e ideal para internet.
- Sem autenticacao e sem classificador emocional.
- Captura browser-side ainda nao foi implementada.

## Proxima Fase Recomendada

Preparar implantacao: configuracao por ambiente, reverse proxy, HTTPS/WSS,
autenticacao basica e decisao entre MediaPipe browser-side ou agente local para
acesso seguro a webcam.

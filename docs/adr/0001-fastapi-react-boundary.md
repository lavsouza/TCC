# ADR 0001: Fronteira FastAPI e React

## Status

Aceito.

## Contexto

O prototipo original mantinha captura, servidor HTTP, WebSocket, interface e
controle Strudel acoplados ao mesmo processo e a uma pagina JavaScript
monolitica. Isso dificultava testar contratos, substituir a interface e
publicar o frontend separadamente.

## Decisao

- Python permanece responsavel por camera, MediaPipe, processamento temporal,
  gestos, mapeamento musical, perfis e cenas.
- FastAPI passa a expor catalogo, sessoes e estado em REST/WebSocket versionado.
- React/TypeScript passa a renderizar a interface e executar o Strudel.
- O estado musical e transportado como dados. O pattern executavel e compilado
  apenas no frontend.
- Nesta fase a camera continua no computador do backend. A captura no navegador
  fica para uma fase posterior.

## Consequencias

Backend e frontend podem ser executados e implantados separadamente. A API fica
testavel sem camera com `MCB_CAPTURE_ENABLED=false`. Como a camera e o perfil
selecionado ainda sao recursos compartilhados, o MVP suporta varias conexoes,
mas nao varias performances independentes no mesmo processo.

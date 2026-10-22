# RoundLens — VALORANT Event Map

Projeto inicial funcional: API Python/FastAPI, frontend React/TypeScript, visualização Canvas com React Konva e armazenamento PostgreSQL/Neon ou SQLite local.

**Estado desta versão:** importação real, filtros combinados, relatórios, seleção de pontos, tratamento de sobreposição, tema escuro, paginação interna da API e calibração manual implementados. Não inclui imagens oficiais de mapas, calibrações validadas ou nomes legíveis de armas/agentes. Sem imagem calibrada, mostra um plano de coordenadas explicitamente identificado. Nenhuma conexão Neon foi criada ou testada sem credenciais. Não inclui autenticação: executar localmente ou atrás de controle de acesso antes de publicar a base.

## 1. Iniciar com Docker (opcional)

Pré-requisito: Docker com Compose. Na raiz do projeto:

```sh
docker compose up --build -d
```

Copie o ZIP oficial para `data/partidas.zip` e importe:

```sh
docker compose exec backend python -m app.ingest /data/partidas.zip --qualifiers-only
```

Abra **http://localhost:8080** e recarregue após importar. A API está em **http://localhost:8000/docs**. O volume preserva o banco local. Os serviços estão vinculados somente a localhost.

O filtro `--qualifiers-only` importa as classificatórias 1–4. Remova-o apenas se usar também as pastas adicionais fornecidas, conforme orientação da organização. Não coleta dados externos.

## 2. Iniciar sem Docker (Windows / PowerShell)

Instale Python 3.11+ e Node.js 22 LTS. No primeiro terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m app.ingest "..\data\partidas.zip" --qualifiers-only
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

No segundo terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abra **http://localhost:5173**. Usar diretamente o executável da venv evita depender de permissões de execução de scripts do PowerShell. Se o ZIP tiver outro nome, ajuste o caminho.

## 3. Iniciar sem Docker (Linux / macOS)

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/python -m app.ingest ../data/partidas.zip --qualifiers-only
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Em outro terminal, execute `npm ci` e `npm run dev` dentro de `frontend`.

## 4. Neon / PostgreSQL

Crie um projeto Neon, copie a connection string e configure apenas `backend/.env`:

```dotenv
DATABASE_URL=postgresql://USUARIO:SENHA@HOST/BANCO?sslmode=require
CORS_ORIGINS=http://localhost:5173
```

A URL é convertida para o driver psycopg pelo código. Não colocar DATABASE_URL em variáveis VITE_, no React, Git ou screenshots. Escape caracteres da senha conforme a URL fornecida pelo provedor. Use a string pooled para a API conforme o perfil de hospedagem; para migrações, use a conexão direta quando exigido. A base local não é copiada automaticamente: rode o importador com a URL Neon configurada.

Banco novo, antes de importar/iniciar:

```sh
python -m alembic upgrade head
python -m app.ingest ../data/partidas.zip --qualifiers-only
```

No Windows, use `.\.venv\Scripts\python.exe` no lugar de `python`.

Para um banco local já criado automaticamente por esta versão, com o esquema sem modificações, `python -m alembic stamp 0001` registra a versão existente. Não usar stamp em um esquema desconhecido. Na produção, configurar `AUTO_CREATE_TABLES=false` e aplicar migrações durante o deploy.

No Docker Compose, a variável precisa estar no ambiente do Compose ou em um `.env` na raiz, não apenas em `backend/.env`. Nunca commitar esse arquivo.

## 5. Como usar a interface

1. Selecione um mapa. A aplicação consulta as opções disponíveis.
2. Combine campeonato, time, player, lado, tempo e tipo de evento. Segure Ctrl/Cmd para múltiplas opções; seleção vazia significa todos.
3. Início = [0,30) s; meio = [30,60) s; fim = [60,infinito) s. São presets do produto, não fases oficiais. Campo final é exclusivo.
4. Verde preenchido = posição do responsável pelo abate adversário. Vermelho vazado = posição da vítima. A lista acessível oferece botões com texto.
5. Clique no ponto; se houver sobreposição, escolha na lista. O mesmo evento pode ter um marcador de origem e um de destino. A linha tracejada é uma ligação visual, não um disparo reconstruído.
6. O relatório mostra os dados originais e a economia do round. IDs de agentes/armas são preservados enquanto não houver catálogo autorizado.
7. Zoom pelos botões/roda do mouse; arraste o canvas; botão restaurar centraliza novamente.
8. A URL guarda os filtros. A listagem é paginada em 40 itens, e o mapa carrega todas as páginas do recorte pela API, sem truncamento silencioso.

Categorias distintas combinam por AND; opções dentro de uma categoria por OR. Player/time/lado referem-se à pessoa representada pelo marcador (killer em abates, victim em mortes). Quando ambos os tipos estiverem ativos, um evento pode corresponder às duas perspectivas. As contagens distinguem eventos de marcadores.

## 6. Adicionar imagem e calibrar o mapa

O código não inventa plantas ou calibrações. Confirme o uso de assets estáticos com a organização; obtenha uma imagem autorizada do mapa e pontos correspondentes confiáveis.

Transformação usada:

```text
u = a*x + b*y + c
v = d*x + e*y + f
```

x/y são coordenadas do jogo; u/v vão de 0 a 1 na imagem. Se um ponto está no pixel (250,100) de uma imagem 1000×500, então u=0.25 e v=0.20. O canvas preserva a proporção da imagem.

Crie `pontos.json` com pelo menos três pontos não colineares. Este exemplo é somente sintético:

```json
[
  {"x": 0, "y": 0, "u": 0.1, "v": 0.1},
  {"x": 100, "y": 0, "u": 0.9, "v": 0.1},
  {"x": 0, "y": 100, "u": 0.1, "v": 0.9}
]
```

Na raiz:

```sh
python scripts/calibrate.py pontos.json
```

No botão de configurações do mapa, carregue a imagem PNG/JPEG/WebP (até 2 MB) e cole os seis coeficientes. Valide com pontos adicionais não usados no ajuste, distribuídos pelo mapa. A configuração fica no localStorage desse navegador, separada por mapId; não é compartilhada entre usuários e deve ser revista se o asset/mapa mudar. A identificação “calibração manual” não certifica que ela está correta.

Sem imagem, o plano usa limites dos dados e mesma escala para os eixos para permitir exploração. Esses limites **não calibram o mapa real**. Não interpretar distância entre eventos como trajeto, linha de visão ou possibilidade de trade.

## 7. Modelo e importação

Esta versão inicial usa três tabelas com projeções de leitura:

- `matches`: metadados, origem, hash, resolução dos times e JSON completo (JSONB no PostgreSQL).
- `kill_events`: um evento por registro de origem, timestamps, categoria e relatório JSON.
- `markers`: projeções consultáveis de abate/morte com player, time, lado, posição e tempo indexados.

Isso reduz o número de joins no MVP e preserva o material para normalização futura. É uma simplificação intencional do desenho completo da especificação anterior.

Uma transação por partida; reimportação idêntica é ignorada. Conteúdo alterado substitui eventos e marcadores daquela partida sem duplicação. Não importa observadores como jogadores ativos. O importador imprime contagem de falhas e termina com código diferente de zero se houver erro. Não registra detalhes de conexão em logs de exceção.

### Equipes e lados

Nomes de equipes são extraídos dos arquivos e associados a Red/Blue usando os placares. A origem desse vínculo fica no banco. Nomes não resolvidos são explícitos. Não unificamos automaticamente `inatel` com `inatel_legacy` ou outros aliases.

Overrides podem ser fornecidos:

```json
{"MATCH_ID": {"Red": "Nome canônico A", "Blue": "Nome canônico B"}}
```

```sh
python -m app.ingest ../data/partidas.zip --teams ../data/teams.json
```

Reimportar com overrides atualiza os marcadores. O lado é derivado de winningTeam e winningTeamRole de cada round; funciona independentemente de troca de lado/prorrogação. Nome de jogador permanece o registrado naquela partida; puuid identifica a pessoa. O catálogo agrega os aliases, sem afirmar que um deles é o atual.

### Mortes especiais

`enemy`: responsável e vítima em equipes diferentes. `self`: mesmo participante. `friendly`: mesma equipe. `unknown`: identidade não resolvida. Somente enemy conta como abate. Mortes incluem as categorias registradas, discriminadas no relatório. Ausência da posição do responsável não remove o evento: apenas impede o marcador de origem no canvas.

## 8. API

Documentação interativa: `/docs`.

- `GET /health`: verifica a conexão.
- `GET /api/v1/catalog?map_id=...`: opções da interface.
- `GET /api/v1/map-bounds?map_id=...`: limites para plano de coordenadas.
- `GET /api/v1/events?map_id=...&kind=kill&kind=death&side=Defender&start_ms=30000&end_ms=60000`: consulta paginada. Filtros repetíveis: competition, team, player, side, kind. Cada página inclui o resumo completo do recorte.
- `GET /api/v1/events/{event_id}`: relatório completo.

Paginação por `after`/`next_cursor`, até 5000 marcadores por página; ordem determinística por ID. A lista da interface ordena pelo tempo no round. Em filtros combinados, os IDs devem ser codificados em URL; o frontend faz isso automaticamente.

## 9. Testes e build

```sh
cd backend
python -m pytest -q
```

Use o Python da venv. Os testes criam SQLite temporário e nunca alteram a base configurada no `.env`.

```sh
cd frontend
npm ci
npm run build
```

O projeto inclui package-lock.json. `requirements-lock.txt` registra as versões do ambiente de verificação Python; para reproduzi-las, use `pip install -r requirements-lock.txt` em Python compatível. O requirements principal mantém faixas de compatibilidade.

## 10. Produção e próximos incrementos

- Hospedar frontend estático e backend Python separadamente; Neon hospeda somente PostgreSQL.
- Configurar VITE_API_URL antes do build se usar domínios separados, e CORS_ORIGINS no backend.
- Restringir acesso, aplicar TLS, limites de requisição e usuário PostgreSQL somente leitura para a API. Importação/migração usa usuário próprio de escrita.
- Não publicar dados identificáveis em site aberto sem verificar o contexto de uso do evento.
- A versão inicial não inclui login, vídeos, heatmap contínuo, catálogo de agentes/armas, calibração automática, gráficos avançados ou trajetórias interpoladas.
- Agregação espacial no servidor/cache será útil para bases maiores; o recorte atual é carregado em páginas completas antes da renderização.
- Habilidades: registra somente damageType/damageItem do dano final. Não inventa local de smoke, lançamento, cegueira nem headshot do evento.
- As quatro classificatórias têm 199 partidas. O ZIP completo tem 336; confirmar com a organização a inclusão das pastas adicionais.

Fontes: JSONs e referências fornecidos pelo usuário. Projeto independente e não afiliado à Riot Games. Nenhuma partida, imagem oficial, segredo ou dependência instalada faz parte deste ZIP de código.

# Filtros guiados e contexto do evento — 20/10/2026

## Experiência

- O usuário escolhe um mapa e marca um ou mais campeonatos com caixas de seleção.
- Ao marcar campeonatos, os eventos aparecem automaticamente; os demais filtros são opcionais.
- O time é liberado após mapa e campeonato; a lista contém apenas times desse recorte.
- Escolher um time libera jogadores, lado e partidas. Não é necessário escolher jogador para filtrar lado.
- Partidas pertencem ao mapa/campeonato/time; selecionar uma libera todos os rounds da fonte.
- Alterar mapa, campeonato ou time limpa as seleções dependentes; alterar partida limpa o round.
- O período do round tem botões com intervalos descritos em segundos e uma opção de intervalo personalizado.
- A lista de eventos abaixo do mapa foi removida.

## Relatório e mapa

O relatório mostra o round e o placar existente no início desse round, contando apenas
as vitórias de rounds anteriores. Foram removidos tempo na partida, coordenadas da
origem/vítima e detalhes técnicos em JSON. O resultado do round aparece em português:
por exemplo, `Eliminated` significa eliminação do time adversário; o nome seguinte
é o time vencedor daquele round, não necessariamente o time que venceu a partida.

O catálogo local de conteúdo traduz UUIDs de armas e fornece os retratos dos agentes.
Fonte: https://valorant-api.com (catálogo comunitário, não oficial). Foi confirmado:
`A03B24D3-4319-996D-0F8C-94BBFBA1DFC7` = Operator. São 29 agentes e 21 armas no catálogo
baixado nesta sessão. Os retratos e nomes são servidos localmente, sem exigir rede no navegador.
O script scripts/download_content.py permite atualizá-los posteriormente.

Ao selecionar um evento, o mapa mostra o instante daquele evento, sem os marcadores
dos outros eventos. Retratos azuis representam o time de quem abateu e laranjas o
adversário. Anéis verde/vermelho destacam quem abateu/a vítima; a cruz no centro do
retrato é a posição projetada. O botão Voltar à distribuição retorna aos eventos filtrados.

A fonte só fornece posições dos jogadores presentes em playerLocations naquele
instante, acrescidas da victimLocation. Jogadores já mortos/ausentes não ganham
posições estimadas; continuam na relação dos dez participantes com a indicação
de ausência. A posição da vítima usa victimLocation, inclusive quando não aparece
em playerLocations. Os retratos usam a mesma projeção dos eventos e o zoom mantém
seu tamanho visual.

A spike é exibida em amarelo em plantLocation quando o plant já ocorreu e não
houve desarme até o instante do evento. Sem coordenada registrada não há posição
estimada. Antes do plant e após o desarme, o ícone não aparece.

O dano é o agregado do round recebido pela vítima, por atacante, com dano, cabeça,
corpo e pernas. Não há informação suficiente para afirmar se o tiro final foi HS:
headshots contabiliza acertos no round, não a região do golpe final. Isso fica
explícito no relatório. Também pode haver dano posterior ao evento em caso de
ressurreição; o painel não apresenta o agregado como dano exclusivamente daquele abate.

## Validação

- Build TypeScript/Vite aprovado (aviso de bundle acima de 500 kB).
- Seis testes Node aprovados: geometria/zoom e dependência/serialização dos filtros.
- Três testes pytest aprovados; abrangem fluxo original, filtros em cascata,
  múltiplos campeonatos, isolamento de partidas, rounds, placar anterior, dano,
  vítima ausente da lista de posições, jogador sem posição e spike antes/depois do plant/desarme.
- scripts/verify_event_context.py aprovado sobre o banco local em modo somente leitura:
  um evento real de cada um dos dez mapas, com partida/round, dez participantes,
  retratos existentes e placar conferido. Resumo em smoke-test.json.
- Não foi executada interação em navegador nem reconstrução dos contêineres.

Os testes sintéticos usam um banco temporário. A checagem real usa conexão SQLite
com mode=ro e desabilita leitura de .env. O banco importado e o volume Docker não
foram alterados; os campos novos são derivados do payload já preservado, sem migração
ou reimportação.

## Atualizar Docker

Na raiz do projeto, com Docker Desktop aberto:

```powershell
docker compose up -d --build backend frontend
```

Depois abra http://localhost:8080 e pressione Ctrl+F5. É necessário reconstruir os
dois serviços, pois catálogo, filtros de partida/round e relatório também mudaram no backend.

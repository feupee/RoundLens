# Verificação da versão inicial

Executada em 19/10/2026, Python 3.12, Node 24, SQLite local temporário.

- Build TypeScript + Vite: concluído. Vite emitiu aviso de chunk JavaScript superior a 500 kB; não é falha de build.
- pytest: 2 testes aprovados, abrangendo fluxo de importação, filtros, paginação, detalhes, valores ausentes, reimportação e lados. Houve aviso de depreciação do adaptador httpx do TestClient.
- Migração Alembic em banco SQLite vazio: concluída.
- Importação do ZIP real: 336 partidas, 46.753 eventos, zero falhas e zero vínculos de time não resolvidos pelo método de placar/nome do arquivo. Isso não certifica a identidade canônica entre aliases.
- Banco real de validação: 46.371 marcadores de abate e 46.753 de morte, total 93.124.
- Reimportação do mesmo ZIP: 336 partidas ignoradas, nenhuma duplicação.
- API com TestClient sobre dados reais: catálogo com 10 mapas, paginação completa sem IDs repetidos, origem do abate conferida com o relatório, filtros conjuntos de player/time/lado/tipo/tempo, health check.
- O banco real usado na verificação fica fora do ZIP entregue.

Limites: não foi executado teste visual em navegador, nem Docker, nem conexão com Neon/PostgreSQL remoto. Imagens e calibrações oficiais não foram fornecidas; o mapa começa como plano de coordenadas. A geometria sobre imagem deve ser validada pelo usuário com referências confiáveis. O projeto é uma base inicial, não uma implantação de produção com autenticação.

# Alinhamento dos minimapas — 20/10/2026

A atualização de minimapas já estava aplicada ao iniciar esta verificação:
MapView.tsx carrega catalog.json, há 13 imagens calibradas e o downloader está presente.

O banco SQLite local foi aberto com mode=ro, sem carregar .env ou importar novamente
as partidas. Foram verificados 93.124 registros: 93.053 com posição, em dez mapas,
e 71 sem posição. Todas as imagens utilizadas têm as dimensões declaradas no catálogo.
Os totais por mapa estão em report.json.

contact-sheet.png mostra uma amostra determinística de aproximadamente 800 posições
por mapa (todos os registros nos mapas menores). A inspeção visual da sobreposição
mostra correspondência geral entre eventos, corredores e áreas dos mapas, sem evidência
de inversão de eixos, rotação ou erro global de escala/deslocamento. Os coeficientes
do catálogo foram preservados. Isso não certifica cada posição nem a compatibilidade
de cada versão histórica do mapa com a imagem atual, e não houve comparação com VOD.

Há 47 posições projetadas fora da imagem: Breeze 4, Abyss 23 e Haven 20.
Em Abyss, as amostras inspecionadas são mortes classificadas como self; em Breeze
e Haven há coordenadas que resultam em v próximo de 4,3. Esses registros exigem
investigação da partida/fonte antes de qualquer correção. Não foram removidos,
limitados às bordas ou usados para redimensionar o minimapa.

Correções no frontend:

- Zoom pela roda preserva o ponto sob o cursor; botões preservam o centro.
- Zoom e deslocamento são atualizados juntos, com limites de 0,5 a 8.
- Editor abre com a imagem e os coeficientes atualmente usados.
- Ajuste da imagem impede escala negativa em contêineres muito estreitos.
- Imagem, marcadores e ligação do confronto continuam no mesmo espaço de coordenadas.

Validação: três testes de geometria aprovados (eixos/projeção, zoom após arraste,
limites sem deslocamento); build TypeScript/Vite aprovado, com aviso de bundle >500 kB.
Não foi executada interação em navegador nem reconstrução Docker nesta sessão.

Reproduzir a análise local (Python com Pillow, sem acessar configuração da aplicação):

```powershell
python scripts/verify_alignment.py
node --test frontend/src/mapGeometry.test.mjs
cd frontend
npm.cmd run build
```

O script verifica o banco local backend/eventmap.db, não o volume Docker ou um banco
remoto. Ele só grava os artefatos em docs/alignment. Os testes Node requerem Node
com suporte a execução de TypeScript (usado Node 24.18).

Para atualizar o frontend a partir da raiz, preservando o volume de dados:

```powershell
docker compose up -d --build frontend
```

Não é necessário reimportar as partidas nem executar o downloader novamente.

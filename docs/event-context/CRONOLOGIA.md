# Cronologia e equipamento — 20/10/2026

Após selecionar uma partida, a barra apresenta todos os seus rounds em ordem,
independentemente dos filtros de jogador, lado, tipo e tempo. Verde/✓ indica vitória
do time selecionado; vermelho/✕, derrota; cinza/—, resultado indisponível.
As cores são acompanhadas por símbolos e rótulos acessíveis. O round selecionado
tem contorno branco e fica sincronizado com o seletor já existente. Ambos usam
o mesmo filtro de eventos. “Todos os rounds” remove apenas o filtro de round.

O relatório mostra dois cartões: quem abateu e a vítima, com arma, colete,
valor do equipamento, gasto total, gasto com utilitários e créditos restantes.
Os dados são os do registro do round, não um inventário garantido no instante do
evento. Coletes usam nomes do catálogo local da Valorant-API; valor vazio significa
sem colete, enquanto campo ausente significa informação indisponível.

Gasto com utilitários é apresentado como “Não informado”: os registros de economia
contêm gasto total, mas não discriminam compras de habilidades. Subtrair preços de
arma e colete produziria resultados incorretos com equipamentos carregados de rounds
anteriores, recebidos de companheiros ou reparados. Zero e valor ausente são tratados
de forma diferente.

Validação: build TypeScript/Vite aprovado (aviso de tamanho de bundle); oito testes
Node e três testes pytest aprovados. Os testes de backend incluem a inversão de
vitória/derrota ao mudar de time e ausência de cronologia para partida fora do recorte.
O script verify_event_context.py também confere cronologia e catálogo de coletes
em eventos reais dos dez mapas, com SQLite em modo somente leitura. Não houve
teste interativo em navegador ou reconstrução Docker.

Atualizar os dois serviços na raiz:

```powershell
docker compose up -d --build backend frontend
```

Recarregar localhost:8080 com Ctrl+F5. Sem migração ou reimportação de dados.

# Financeiro e recomendações gerenciais

Consulta em **10/11/2026 às 19:19 (horário de Brasília)**. Recorte de todo o histórico disponível, sem seleção de máquina, produto ou turno.

## Conexão com o Supabase

A página Início confirmou a conexão e a leitura das seis tabelas.

| Tabela | Leitura | Registros na consulta |
| --- | --- | ---: |
| `machines` | Liberado | 4 |
| `production_events` | Liberado | 31.692 |
| `machine_telemetry` | Liberado | 226.472 |
| `sales_orders` | Liberado | 25.990 |
| `parts_wear` | Liberado | 12 |
| `wear_events` | Liberado | 48.528 |

## Principais resultados

- **Faturamento** — R$ 102.492.956,29.
- **Custo estimado de produção** — R$ 128.972.304,13.
- **Custo estimado dos rejeitados** — R$ 5.488.999,79.
- **Maior custo total no período** — Módulo Eletrônico D (R$ 55.652.529,41).
- **Maior custo médio por unidade** — Módulo Eletrônico D (R$ 158,81).

O faturamento de **R$ 102.492.956,29** foi conferido com a página Vendas no mesmo recorte.

## Consultas e premissas

- A receita vem de `sales_orders`. Somamos `total_amount` por produto e canal, com filtro na data do pedido e exclusão de cancelados.
- O custo de fabricação vem de `production_events`. Somamos `qty_produced × unit_cost` e usamos `machines` para identificar a máquina. O custo dos rejeitados é `qty_rejected × unit_cost` e está incluído no custo total de produção.
- Para cada pedido, estimamos o custo das unidades vendidas com o custo médio ponderado do lote e do código do produto. Na ausência de custo de lote, usamos a média ponderada do produto fabricado no período, quando disponível.
- A margem estimada em reais é receita menos custo das unidades vendidas. Dividir esse resultado pela receita dá a margem percentual. Frete, tributos e outras despesas não identificadas no custo ficam fora da estimativa.
- Os filtros de máquina e turno afetam os custos de produção. Receita e margem usam período e produto. O desgaste vem de `parts_wear` e reflete o estado atual.

## Recomendações para a direção

### 1. Investigar as rejeições de Cabine de Pintura 01

12.449 rejeitadas em 289.973 unidades produzidas (4,29%).
Revisar os lotes e turnos dessa máquina para identificar onde a rejeição se concentra.

Fonte no painel: Produção · rejeição por máquina.

### 2. Revisar as paradas de Cabine de Pintura 01

31.788,7 minutos de parada e 99,6 unidades por hora.
Levantar as causas das paradas e verificar a capacidade das outras máquinas antes de redistribuir ordens de produção.

Fonte no painel: Produção · produtividade por máquina.

### 3. Revisar o planejamento de Módulo Eletrônico D

335.366 unidades aprovadas e 122.613 vendidas. Diferença de 212.753 unidades.
Conferir pedidos, produção anterior e estoque físico antes de ajustar o próximo lote.

Fonte no painel: Produção x vendas · aprovados versus vendidos por produto.

### 4. Acompanhar o desempenho do canal Distribuidor

R$ 26.187.133,74 em receita (25,6% do total) e 154.532 unidades vendidas.
Comparar a receita com os custos comerciais do canal antes de ampliar o investimento.

Fonte no painel: Vendas · faturamento por canal.

### 5. Revisar o custo de fabricação de Módulo Eletrônico D

R$ 158,81 por unidade em média e R$ 55.652.529,41 de custo total estimado.
Comparar o custo unitário entre lotes para identificar variações e oportunidades de redução de custo.

Fonte no painel: Financeiro · custo estimado por produto.

### 6. Priorizar a inspeção de Correia de transmissão

Cabine de Pintura 01 registra 99,5% de desgaste e 9,6 horas restantes estimadas.
Verificar o componente e programar a intervenção conforme o resultado da inspeção.

Fonte no painel: Visão geral · componentes críticos no estado atual.

## Roteiro para a demonstração

1. Abrir **Início** e mostrar a leitura das seis tabelas.
2. Abrir **Financeiro**, aplicar um período e mostrar o maior custo de fabricação. Explicar a diferença entre custo total e custo unitário e como a margem foi estimada.
3. Abrir **Recomendações** e defender pelo menos cinco ações usando as evidências.
4. Aguardar 10 segundos e mostrar que o horário da última atualização muda sozinho. Com o simulador em execução, mostrar também a chegada de novos registros.

O painel usa consultas automáticas ao Supabase a cada 10 segundos (polling). Na entrega, incluir a configuração de exemplo e manter o arquivo `.env` fora do Git.

## Capturas do painel

[Início e conexão](01_Inicio.png) · [Visão geral](02_Visao_Geral.png) ·
[Produção](03_Producao.png) · [Vendas](04_Vendas.png) ·
[Produção x vendas](05_Producao_x_Vendas.png) · [Financeiro](07_Financeiro.png) ·
[Recomendações](08_Recomendacoes.png)

Na verificação em navegador, o horário de atualização passou de 19:21:36 a 19:21:46
automaticamente na página Recomendações.

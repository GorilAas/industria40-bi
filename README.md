# Indústria 4.0 - BI

Painel que mostra, em gráficos e números, o que acontece numa fábrica: quanto foi produzido, quanto foi rejeitado, quanto foi vendido, como estão as máquinas e quais peças estão perto de quebrar. Os dados vêm de um banco online (Supabase) que o professor mantém, e a tela se atualiza sozinha a cada 10 segundos.

Este é um trabalho em grupo da disciplina de Business Intelligence.

## O que você precisa ter instalado

1. **Python 3.10 ou mais novo.** Baixe em python.org. Na instalação, marque a caixa "Add Python to PATH".
2. **Git**, que já traz o Git Bash. Baixe em git-scm.com.

## Como abrir o painel pela primeira vez

1. Baixe o projeto e abra a pasta dele no Git Bash (botão direito dentro da pasta, "Open Git Bash here").
2. Copie e cole os comandos abaixo, um de cada vez, apertando Enter depois de cada um.

Criar o ambiente do projeto:

```bash
python -m venv .venv
```

Ligar o ambiente:

```bash
source .venv/Scripts/activate
```

No macOS ou Linux, use `source .venv/bin/activate`.

Instalar o que o painel usa (demora um ou dois minutos):

```bash
pip install -r requirements.txt
```

Criar o arquivo com o endereço do banco:

```bash
cp .env.example .env
```

3. Abra o arquivo `.env` com o Bloco de Notas ou o VS Code e troque o texto depois do `=` pelo endereço do banco que o professor passou no PDF do trabalho. Salve e feche.
4. Abra o painel:

```bash
streamlit run app.py
```

O navegador abre sozinho em `http://localhost:8501`. Para fechar, volte ao Git Bash e aperte Ctrl+C.

## Das próximas vezes

Só estes dois comandos, dentro da pasta do projeto:

```bash
source .venv/Scripts/activate
```

No macOS ou Linux, use `source .venv/bin/activate`.

```bash
streamlit run app.py
```

## O que aparece na tela

No menu à esquerda ficam as páginas: Início, Visão geral, Produção, Vendas, Produção x vendas, Financeiro, Recomendações e Entrega. Na barra lateral você filtra por período, máquina, produto e turno. Em branco, o filtro vale para tudo. Se não houver registros recentes, selecione **Todo o histórico** no filtro de período.

Na página Início, a tabela mostra se o seu usuário consegue ler cada tabela do banco. Se aparecer "Sem acesso" em todas, as demais páginas ficam vazias e mostram o aviso "Sem permissão para acessar os dados". Isso não é defeito do seu computador: o acesso de leitura ainda precisa ser liberado no banco.

O [relatório de Financeiro e Recomendações](evidencias/Financeiro_e_Recomendacoes.md) reúne as premissas, os resultados e o roteiro de demonstração. A página **Entrega** mostra o relatório e permite baixar o relatório e as capturas em um ZIP.

## Quando algo dá errado

- **"python" não é reconhecido:** o Python não foi instalado com "Add Python to PATH". Instale de novo marcando a caixa.
- **"No such file or directory: .env.example":** o Git Bash não está dentro da pasta do projeto. Abra de novo a partir da pasta.
- **Aviso de conexão ou de autenticação na tela:** o endereço no `.env` está errado ou incompleto. Confira se copiou a linha inteira, sem espaços.
- **Mudei o `.env` e nada mudou:** feche o painel com Ctrl+C e abra de novo.

O detalhe técnico de cada erro aparece no Git Bash, na janela onde o painel está rodando.

## Para quem vai programar

- `app.py`: monta o menu. Página nova entra na lista `paginas`.
- `pages/`: uma página por assunto. `1_Overview.py` é o exemplo para copiar.
- `core/data.py`: todas as consultas ao banco. As colunas, que no banco estão em inglês, ganham nome em português aqui.
- `core/metrics.py`: os cálculos dos indicadores.
- `core/filters.py`, `core/charts.py`, `core/ui.py`: filtros, gráficos e componentes de tela.
- `core/database.py` e `core/config.py`: conexão com o banco e configurações.
- `evidencias/`: prints e provas para entregar.

Regras do grupo:

- Funções, variáveis e colunas em português.
- Nunca use `SELECT *`, e coloque o filtro de período dentro da própria consulta.
- Nunca suba o arquivo `.env` para o git, porque ele guarda a senha do banco.
- Antes de subir o código, rode `ruff check .` (instale com `pip install ruff`) e abra a página que você mexeu.

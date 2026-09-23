# Deploy do SonarGest (gratuito)

Arquitetura publicada:

```text
Navegador (empresa / celular do motorista)
        │  HTTPS
        ▼
Streamlit Community Cloud  ← código vindo do GitHub
        │  conexão SSL
        ▼
PostgreSQL na nuvem (Supabase ou Neon)
```

Custo total: **R$ 0** nos planos gratuitos.

---

## Passo 1 — Banco de dados na nuvem

Recomendação: **Supabase** (painel visual, editor SQL no navegador, plano
gratuito estável). Alternativa: **Neon**, se preferir um banco que hiberna
quando ocioso.

1. Crie a conta e um projeto PostgreSQL na região `South America (sa-east-1)`.
2. Copie a **connection string** em *Project Settings → Database → Connection
   string → URI*. Use a opção **Session pooler** (porta 5432) — o Streamlit
   Cloud abre e fecha conexões com frequência.
3. Garanta o sufixo `?sslmode=require` no fim da URL.
4. No editor SQL do painel, cole e execute, nesta ordem:
   - todo o conteúdo de `database/schema.sql`
   - todo o conteúdo de `database/seed.sql`

Alternativa pelo terminal, se tiver o `psql` instalado:

```bash
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/seed.sql
```

Confira no painel que a tabela `servicos` tem 120 linhas.

## Passo 2 — Código no GitHub

O repositório deve conter **apenas o conteúdo da pasta `sonargest/`**, com o
`Home.py` na raiz — é onde o Streamlit Cloud procura o arquivo principal. Não
sincronize a pasta que está acima dela: o repositório precisa ser criado a
partir de dentro de `sonargest/`, com os comandos abaixo.

```bash
cd sonargest
git init
git add .
git commit -m "SonarGest - sistema de gestao de carro de som"
git branch -M main
git remote add origin https://github.com/Wilianpnasc/sonargest.git
git push -u origin main
```

Antes do push, confirme que **o `.env` não está na lista**:

```bash
git status --short | grep -c "\.env$"   # precisa imprimir 0
```

E confirme que o repositório é 100% Python, sem nenhum arquivo estranho ao
projeto:

```bash
git ls-files | head -40          # só deve listar Home.py, app/, pages/, database/, ...
git grep -i lovable || echo "nenhuma referência encontrada"
```

## Passo 3 — Publicar no Streamlit Community Cloud

1. Acesse <https://share.streamlit.io> e entre com a conta do GitHub.
2. **Create app → Deploy a public app from GitHub**.
3. Preencha:
   - Repository: `Wilianpnasc/sonargest`
   - Branch: `main`
   - Main file path: `Home.py`
   - Python version: `3.11`
4. Abra **Advanced settings → Secrets** e cole (com os seus valores reais):

```toml
DATABASE_URL = "postgresql://usuario:senha@host:5432/postgres?sslmode=require"
APP_SECRET_KEY = "uma-chave-aleatoria-longa"
TIMEZONE = "America/Sao_Paulo"
```

5. **Deploy**. O primeiro build leva de 2 a 4 minutos (instala o
   `requirements.txt`).

A URL final fica no formato `https://sonargest.streamlit.app`. Essa é a URL que
o motorista salva na tela inicial do celular.

> Por que secrets e não `.env`? O `.env` fica só na sua máquina e nunca vai para
> o GitHub. Na nuvem, o mesmo papel é feito pelos secrets do Streamlit, que
> `app/config.py` lê automaticamente quando a variável de ambiente não existe.

## Passo 4 — Validar em produção

| Verificação | Resultado esperado |
|---|---|
| Abrir a URL | tela de login, sem erro de conexão |
| Entrar como `admin@sonargest.com` | menu com Serviços, Cadastros e Dashboard |
| Abrir o Dashboard | KPIs preenchidos e 7 gráficos com os 120 serviços |
| Entrar como motorista pelo celular | apenas Itinerário e Histórico, em uma coluna |
| INICIAR e FINALIZAR um serviço no celular | status muda e a diferença aparece |
| Recarregar e tentar iniciar de novo | ação bloqueada pela regra |

## Passo 5 — Depois da publicação

- **Trocar as senhas de demonstração** antes de mostrar o link publicamente:

```bash
python -m scripts.criar_usuario --nome "Empresa" --email admin@sonargest.com --perfil admin
```

- Cada `git push` na branch `main` redeploya o app automaticamente.
- Após uma alteração em `requirements.txt`, use **Reboot app** no painel.

## Problemas comuns

| Sintoma | Causa | Correção |
|---|---|---|
| `ConfiguracaoAusente: DATABASE_URL` | secrets não salvos | cadastre em *Settings → Secrets* e reinicie o app |
| `SSL connection has been closed unexpectedly` | connection string sem SSL | acrescente `?sslmode=require` |
| `too many connections` | uso da porta direta em vez do pooler | troque pela URL do *Session pooler* |
| App "dorme" e demora a abrir | inatividade no plano gratuito | normal; a primeira visita reativa em segundos |
| Tabelas vazias | seed não executado | rode `database/seed.sql` no editor SQL |

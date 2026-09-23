# SonarGest — Sistema de Gestão de Carro de Som

Projeto Integrador do curso de Ciência de Dados. Sistema web para uma empresa de
carro de som planejar serviços de divulgação, permitir que o motorista registre o
horário real de execução e analisar a diferença entre o **contratado** e o
**realizado** por meio de indicadores e um dashboard.

## Objetivo

Demonstrar um ciclo completo de dados:

```text
dado planejado -> dado operacional -> dado realizado -> transformação -> KPI -> decisão
```

## Tecnologias

| Camada | Tecnologia | Motivo |
|---|---|---|
| Aplicação web | Python 3.11 + Streamlit | telas, login e dashboard no mesmo projeto, com pouquíssimo código |
| Acesso a dados | SQLAlchemy | consultas seguras (evita SQL injection) e código organizado |
| Banco | PostgreSQL (Supabase ou Neon) | relacional, gratuito na nuvem, aceita conexão externa |
| Análise | pandas | tratamento e agregação dos dados |
| Visualização | Plotly | gráficos interativos |
| Senhas | bcrypt | hash seguro, nunca senha em texto puro |
| Testes | pytest | validação das regras de negócio |

## Arquitetura

```text
Empresa (desktop) ─┐
                   ├─► Streamlit (Python) ─► PostgreSQL na nuvem
Motorista (celular)┘            │
                                └─► pandas + Plotly ─► Dashboard / Power BI
```

Separação de responsabilidades: `app/` (telas) · `app/services` (regras de negócio) ·
`app/db` (acesso ao banco) · `analytics/` (análise) · `database/` (SQL).

## Estrutura do projeto

```text
sonargest/
├── Home.py                  # ponto de entrada: login e roteamento por perfil
├── pages/                   # telas do Streamlit (empresa e motorista)
├── app/                     # camadas da aplicação
│   ├── config.py            # variáveis de ambiente e fuso horário
│   ├── db.py                # conexão e sessões do PostgreSQL
│   ├── models.py            # ORM SQLAlchemy (6 tabelas)
│   ├── security.py          # hash de senha (bcrypt)
│   ├── calculos.py          # indicadores (funções puras)
│   ├── repositories.py      # acesso ao banco
│   ├── services.py          # regras de negócio e autorização
│   ├── auth.py              # sessão, login/logout e proteção de páginas
│   └── ui.py                # formatação e montagem das tabelas
├── analytics/               # notebook e funções de análise (pandas)
├── database/
│   ├── schema.sql           # tabelas, constraints, índices e views analíticas
│   ├── seed.sql             # dados fictícios (gerado)
│   └── queries.sql          # consultas analíticas principais
├── scripts/
│   ├── gerar_seed.py        # gera o seed.sql com dados variados
│   └── criar_usuario.py     # cria usuário com senha em hash
├── tests/                   # testes das regras de negócio
├── docs/
│   ├── MODELO_DADOS.md      # diagrama ER, dicionário, índices e normalização
│   ├── APRESENTACAO.md      # roteiro da banca e perguntas prováveis
│   └── DEPLOY.md            # publicação gratuita passo a passo
├── .streamlit/              # tema e modelo de secrets da nuvem
├── .env.example             # modelo das variáveis de ambiente
├── .gitignore               # impede o envio do .env
├── requirements.txt
└── README.md
```

## Modelo de dados

| Tabela | Papel |
|---|---|
| `usuarios` | identidade de login (perfil `admin` ou `motorista`) |
| `clientes` | quem contrata o serviço |
| `motoristas` | dados operacionais, 1:1 com `usuarios` |
| `carros` | frota |
| `servicos` | **tabela-fato**: planejado (data, horas contratadas) + realizado (início, fim) |
| `servicos_log` | auditoria das ações relevantes |

Relacionamentos: um cliente tem muitos serviços (1:N); um motorista tem muitos
serviços (1:N); um carro é usado em muitos serviços (1:N). Cada tabela tem chave
primária `id`; `servicos` referencia as três por chave estrangeira.

Restrições implementadas no próprio banco: `horas_contratadas > 0`,
`fim_real > inicio_real`, não existe fim sem início, status em uma lista fechada,
placa e CNH únicas.

Índices: `data_servico`, `cliente_id`, `status` e o par `(motorista_id, data_servico)` —
que é exatamente a consulta da tela do motorista.

Normalização em 3FN: nada de nome de cliente repetido dentro de `servicos`, apenas a
chave estrangeira. Os indicadores também não são gravados: são calculados na view
`vw_servicos_analitico`, evitando dado inconsistente.

## Indicadores

| Indicador | Fórmula | Leitura simples |
|---|---|---|
| Horas realizadas | `fim_real - inicio_real` | quanto o carro realmente rodou |
| Desvio de horas | `realizado - contratado` | horas a mais (+) ou a menos (−) |
| Desvio percentual | `(realizado - contratado) / contratado × 100` | o desvio em % |
| Aderência | `realizado / contratado` | 1,00 = execução perfeita |
| Classificação | tolerância de 5 min | Dentro / Acima / Abaixo |
| Taxa de execução | `finalizados / planejados` | quanto do plano virou serviço |

## Como configurar

```bash
git clone https://github.com/Wilianpnasc/sonargest.git
cd sonargest
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # preencha DATABASE_URL e APP_SECRET_KEY
```

## Como configurar o banco

1. Crie uma conta gratuita no [Supabase](https://supabase.com) ou [Neon](https://neon.tech).
2. Crie um projeto PostgreSQL e copie a **connection string**.
3. Cole em `DATABASE_URL` no arquivo `.env` (que nunca vai para o GitHub).
4. Crie as tabelas e carregue os dados de demonstração:

```bash
psql "$DATABASE_URL" -f database/schema.sql
python scripts/gerar_seed.py
psql "$DATABASE_URL" -f database/seed.sql
```

Usuários de demonstração — senha `senha123`:
`admin@sonargest.com` (empresa) e `joao@sonargest.com` (motorista).

## Como executar localmente

```bash
streamlit run Home.py
```

A aplicação abre na tela de login. Para criar um usuário próprio (a senha é
digitada no terminal e gravada apenas como hash):

```bash
python -m scripts.criar_usuario --nome "Empresa" --email admin@sonargest.com --perfil admin
python -m scripts.criar_usuario --nome "João" --email joao@sonargest.com --perfil motorista --motorista-id 1
```

## Como rodar os testes

```bash
pytest
```

Os testes não usam o banco de produção: montam um SQLite em memória a partir do
próprio ORM, então rodam sem `.env` de banco e sem internet. São 36 casos em
quatro arquivos: `test_calculos.py` (fórmulas dos indicadores),
`test_seguranca.py` (hash bcrypt), `test_servicos.py` (regras de negócio e
autorização por perfil) e `test_indicadores.py` (KPIs em pandas).

## Deploy

Streamlit Community Cloud (gratuito), apontando para este repositório do GitHub,
com o banco PostgreSQL no Supabase ou Neon. As credenciais são cadastradas em
*Settings → Secrets* — nunca no código. Passo a passo completo, validação em
produção e solução de problemas: [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Segurança

- Senhas em hash bcrypt, jamais em texto puro.
- Credenciais em variáveis de ambiente (`.env`), com `.env` no `.gitignore`.
- Autorização por perfil: o motorista só enxerga e altera os próprios serviços.
- Consultas parametrizadas via SQLAlchemy, evitando SQL injection.

## Roteiro de desenvolvimento

- [x] Etapa 1 — Arquitetura
- [x] Etapa 2 — Banco de dados (schema, seed, consultas)
- [x] Etapa 3 — Backend
- [x] Etapa 4 — Autenticação (login, sessão, perfis)
- [x] Etapa 5 — Telas da empresa (serviços e cadastros)
- [x] Etapa 6 — Tela do motorista (itinerário e histórico)
- [x] Etapa 7 — Analytics (extração, indicadores e perguntas de negócio)
- [x] Etapa 8 — Dashboard interno (KPIs, gráficos e exportação CSV)
- [x] Etapa 9 — Testes
- [x] Etapa 10 — Documentação final e material de apresentação
- [x] Etapa 11 — Deploy (Streamlit Community Cloud + PostgreSQL na nuvem)

## Documentação complementar

- [`docs/MODELO_DADOS.md`](docs/MODELO_DADOS.md) — diagrama entidade-relacionamento,
  cardinalidades, dicionário da tabela-fato, restrições, índices e normalização.
- [`docs/DEPLOY.md`](docs/DEPLOY.md) — publicação gratuita passo a passo, do banco
  na nuvem ao app no ar, com checklist de validação em produção.
- [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md) — roteiro de 8 blocos para a
  apresentação acadêmica (problema, solução, dados, processamento, análise,
  visualização, resultado, qualidade) e respostas às perguntas prováveis da banca.

## Como contribuir

Abra uma issue descrevendo a melhoria, crie um branch a partir de `main`
(`feature/nome-da-melhoria`) e envie um pull request.

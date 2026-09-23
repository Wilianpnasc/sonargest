# Modelo de dados — SonarGest

## Diagrama entidade-relacionamento

```text
        usuarios                         clientes            carros
  ┌────────────────────┐          ┌────────────────┐   ┌──────────────┐
  │ id (PK)            │          │ id (PK)        │   │ id (PK)      │
  │ nome               │          │ nome           │   │ modelo       │
  │ email (UNIQUE)     │          │ contato        │   │ placa (UNIQ) │
  │ senha_hash         │          │ telefone       │   │ ativo        │
  │ perfil             │          │ ativo          │   └──────┬───────┘
  │ ativo              │          └───────┬────────┘          │
  └─────────┬──────────┘                  │ 1                 │ 1
            │ 1                           │                   │
            │ 0..1                        │ N                 │ N
      ┌─────┴────────────┐          ┌─────┴───────────────────┴───────┐
      │ motoristas       │  1     N │ servicos  (TABELA-FATO)         │
      │ id (PK)          ├──────────┤ id (PK)                         │
      │ nome             │          │ cliente_id (FK)                 │
      │ cnh (UNIQUE)     │          │ motorista_id (FK)               │
      │ telefone         │          │ carro_id (FK)                   │
      │ usuario_id (FK)  │          │ data_servico                    │
      │ ativo            │          │ horas_contratadas   ← PLANEJADO │
      └──────────────────┘          │ hora_prevista                   │
                                    │ inicio_real         ← REALIZADO │
                                    │ fim_real            ← REALIZADO │
                                    │ status                          │
                                    │ observacao                      │
                                    └───────────────┬─────────────────┘
                                                    │ 1
                                                    │ N
                                          ┌─────────┴──────────┐
                                          │ servicos_log       │
                                          │ id (PK)            │
                                          │ servico_id (FK)    │
                                          │ usuario_id (FK)    │
                                          │ acao / detalhe     │
                                          │ criado_em          │
                                          └────────────────────┘
```

## Cardinalidades

| Relação | Cardinalidade | Leitura |
|---|---|---|
| `clientes` → `servicos` | 1:N | um cliente contrata vários serviços |
| `motoristas` → `servicos` | 1:N | um motorista executa vários serviços |
| `carros` → `servicos` | 1:N | um carro é usado em vários serviços |
| `usuarios` → `motoristas` | 1:0..1 | todo motorista tem login; nem todo login é motorista |
| `servicos` → `servicos_log` | 1:N | cada serviço acumula seu histórico de ações |

## Dicionário da tabela-fato `servicos`

| Coluna | Tipo | Regra |
|---|---|---|
| `id` | serial | chave primária |
| `cliente_id` | int | FK obrigatória |
| `motorista_id` | int | FK obrigatória |
| `carro_id` | int | FK obrigatória |
| `data_servico` | date | obrigatória |
| `horas_contratadas` | numeric | `> 0` (CHECK) |
| `hora_prevista` | time | opcional, referência de agenda |
| `inicio_real` | timestamp | gravado pelo motorista |
| `fim_real` | timestamp | nunca anterior a `inicio_real` (CHECK) |
| `status` | text | `planejado`, `em_andamento`, `finalizado`, `cancelado` (CHECK) |
| `observacao` | text | livre |

## Restrições de integridade

- `horas_contratadas > 0`
- `fim_real >= inicio_real` e não existe `fim_real` sem `inicio_real`
- `status` limitado à lista fechada
- `email`, `placa` e `cnh` únicos
- FKs impedem serviço órfão; cadastros são **desativados**, nunca excluídos

## Índices e por quê

| Índice | Consulta que ele acelera |
|---|---|
| `data_servico` | filtro de período do dashboard |
| `cliente_id` | ranking e KPIs por cliente |
| `status` | listagens filtradas por situação |
| `(motorista_id, data_servico)` | itinerário do dia — a consulta mais frequente |

## Normalização

O modelo está na **3ª Forma Normal**: `servicos` guarda apenas chaves
estrangeiras, nunca o nome do cliente ou a placa do carro; e nenhum atributo
depende de outro atributo não-chave. Os indicadores (realizado, desvio,
aderência, classificação) também não são armazenados — são derivados na view
`vw_servicos_analitico`, garantindo que dado bruto e dado calculado nunca
divirjam.

## Views analíticas

| View | Entrega |
|---|---|
| `vw_servicos_analitico` | um registro por serviço já com horas realizadas, desvio, desvio %, aderência e classificação |
| `vw_kpi_cliente` | agregação por cliente: serviços, horas contratadas, realizadas e desvio |
| `vw_kpi_motorista` | agregação por motorista: serviços, horas e aderência média |

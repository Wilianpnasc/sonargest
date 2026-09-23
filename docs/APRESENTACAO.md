# SonarGest — Roteiro de apresentação acadêmica

Material de apoio para a banca. Tempo alvo: **12 a 15 minutos**, 8 blocos.

---

## 1. Problema (1 min)

Uma empresa de carro de som vende **horas de divulgação**. O planejamento é feito
em papel ou WhatsApp e o registro do que foi executado depende da memória do
motorista. Consequência: a empresa não sabe se entregou o que vendeu.

Perguntas que hoje ficam sem resposta:

- Quantas horas foram contratadas no mês e quantas foram realmente rodadas?
- Qual cliente recebe mais do que contratou?
- Qual motorista cumpre o combinado?

## 2. Solução (1,5 min)

Um sistema web com **dois perfis de acesso** sobre a mesma base:

```text
Empresa  → cadastra e planeja → SERVIÇO → Motorista → inicia / finaliza
                                    │
                                    ▼
                            Banco PostgreSQL
                                    │
                                    ▼
                        Analytics (pandas) → Dashboard
```

A empresa planeja (cliente, motorista, carro, data, horas contratadas). O
motorista, pelo celular, vê apenas o próprio itinerário e toca em INICIAR e
FINALIZAR. O sistema calcula sozinho o realizado e o desvio.

## 3. Dados (2 min)

Modelo relacional em 3FN com 6 tabelas. A tabela **`servicos` é a tabela-fato**:
guarda lado a lado o planejado (`horas_contratadas`) e o realizado
(`inicio_real`, `fim_real`) — é essa convivência que torna a análise possível.

Mostrar na tela: `database/schema.sql` (constraints e índices) e
`docs/MODELO_DADOS.md` (diagrama e dicionário).

Frase para a banca: *"os indicadores não são gravados, são calculados — assim
nunca existe KPI desatualizado em relação ao dado bruto."*

## 4. Processamento (2 min)

- Coleta: o próprio motorista registra o horário no momento do evento (menos erro
  que o preenchimento posterior).
- Regras no banco: `horas_contratadas > 0`, fim nunca antes do início, status em
  lista fechada.
- Regras na aplicação (`app/services.py`): não finalizar sem iniciar, não iniciar
  serviço cancelado ou já finalizado, motorista só age no próprio serviço.
- Transformação: view `vw_servicos_analitico` entrega o dado já enriquecido com
  horas realizadas, desvio, desvio % e classificação.

## 5. Análise (2,5 min)

`analytics/indicadores.py` recebe DataFrame e devolve DataFrame — nenhuma função
toca no banco, o que separa **OLTP** (registro) de **OLAP** (análise).

| Indicador | Fórmula |
|---|---|
| Desvio | `realizado − contratado` |
| Desvio % | `(realizado − contratado) / contratado × 100` |
| Aderência | `realizado / contratado` |
| Classificação | Dentro / Acima / Abaixo (tolerância de 5 min) |

Rodar ao vivo, se houver tempo: `python -m analytics.perguntas`.

## 6. Visualização (2,5 min)

Abrir **Empresa Dashboard** e percorrer:

1. Cartões de KPI — horas contratadas × realizadas e o desvio no delta.
2. Contratado × realizado por mês — mostra se o problema é pontual ou crônico.
3. Aderência por motorista, com linha de referência em 1,00.
4. Histograma do desvio — concentração à direita do zero = horas dadas de graça.
5. Botão de exportação CSV: mesma base pronta para o Power BI.

## 7. Resultado (2 min)

Com a base de demonstração (120 serviços, 4 meses):

- Existem motoristas com padrão **sistemático** de estender e de encerrar antes —
  não é aleatório, é comportamento, e isso vira ação de gestão.
- As horas excedentes são serviço entregue sem faturamento; as horas não
  entregues são risco de reclamação do cliente.
- O ganho não está no cadastro, está na **medição**: a empresa passa a discutir
  contrato com número, não com impressão.

## 8. Qualidade e limites (1,5 min)

- 36 testes automatizados (`pytest`) cobrindo fórmulas, hash de senha, regras de
  negócio e KPIs, rodando em SQLite em memória, sem depender do banco real.
- Segurança: bcrypt, sessão, autorização por perfil, credenciais em `.env`.
- Fora do escopo desta versão (proposital): GPS, roteirização, nota fiscal e
  pagamentos. A prioridade foi medir bem o que já existe.
- Evolução natural: alerta automático de desvio, meta por cliente e modelo
  preditivo de duração do serviço a partir do histórico.

---

## Perguntas prováveis da banca

**Por que Streamlit e não Flask/Django?**
O projeto é de Ciência de Dados: Streamlit entrega tela, autenticação e gráficos
com pandas no mesmo processo, então o esforço fica na modelagem e na análise, não
em HTML. As regras de negócio estão isoladas em `services.py`, então trocar a
camada de tela não exigiria reescrever o sistema.

**Por que PostgreSQL e não CSV/planilha?**
Preciso de integridade referencial, restrições, concorrência (empresa e motorista
gravando ao mesmo tempo) e SQL analítico com views. Planilha não garante nada disso.

**Os indicadores não deveriam ser gravados por desempenho?**
Só se o volume exigisse. Nesta escala, calcular na view evita o pior problema de
BI: número salvo divergindo do dado de origem.

**Como você garante que o motorista não vê dados de outro?**
O filtro é por `motorista_id` da sessão no servidor, não na tela. Existe teste
automatizado provando que a ação em serviço de outro motorista é recusada.

**Como o dado poderia ser fraudado?**
O motorista pode apertar os botões fora do horário real. Mitigação futura:
carimbo de tempo do servidor comparado ao horário previsto (já existe) e, em uma
próxima versão, validação por localização.

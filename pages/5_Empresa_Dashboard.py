"""Dashboard de BI — visão gerencial de planejado x realizado.

Página exclusiva do perfil ADMIN. Nenhum cálculo acontece aqui: os números
vêm de `analytics.indicadores` e os dados de `analytics.extracao`, as mesmas
funções usadas pelo notebook de análise.
"""

from __future__ import annotations

from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from analytics import indicadores
from analytics.extracao import carregar_servicos
from analytics.perguntas import (
    cliente_com_maior_excesso,
    cliente_com_mais_horas,
    dia_de_maior_demanda,
    motorista_com_mais_horas,
    motorista_mais_aderente,
)
from app.auth import barra_lateral, exigir_perfil
from app.models import PERFIL_ADMIN

st.set_page_config(page_title="SonarGest — Dashboard", page_icon="📊", layout="wide")
exigir_perfil(PERFIL_ADMIN)
barra_lateral()

CORES = {"Dentro": "#2E7D32", "Acima": "#C62828", "Abaixo": "#EF6C00"}

st.title("📊 Dashboard gerencial")
st.caption("Comparação entre o que foi contratado e o que foi efetivamente realizado.")

# ------------------------------------------------------------------ filtros
hoje = date.today()
col1, col2 = st.columns(2)
data_inicio = col1.date_input("De", value=hoje - timedelta(days=120), format="DD/MM/YYYY")
data_fim = col2.date_input("Até", value=hoje, format="DD/MM/YYYY")

if data_inicio > data_fim:
    st.error("A data inicial não pode ser maior que a final.")
    st.stop()


@st.cache_data(ttl=120)
def obter_dados(inicio: date, fim: date):
    return carregar_servicos(inicio, fim)


df = obter_dados(data_inicio, data_fim)

if df.empty:
    st.info("Nenhum serviço no período selecionado.")
    st.stop()

resumo = indicadores.resumo_geral(df)
saldo = indicadores.horas_perdidas_e_excedidas(df)

# ------------------------------------------------------------- indicadores
st.subheader("Indicadores do período")
a, b, c, d = st.columns(4)
a.metric("Serviços", resumo["total_servicos"], f"{resumo['servicos_finalizados']} finalizados")
b.metric("Horas contratadas", f"{resumo['horas_contratadas']:.1f} h")
c.metric("Horas realizadas", f"{resumo['horas_realizadas']:.1f} h", f"{resumo['desvio_total']:+.1f} h")
d.metric("Dentro do contratado", f"{resumo['pct_dentro']:.1f} %")

e, f, g, h = st.columns(4)
e.metric("Aderência média", f"{resumo['aderencia_media']:.2f}")
f.metric("Média de horas/serviço", f"{resumo['media_horas_por_servico']:.2f} h")
g.metric("Horas não entregues", f"{saldo['horas_perdidas']:.1f} h")
h.metric("Horas excedentes", f"{saldo['horas_excedidas']:.1f} h")

st.divider()

# ----------------------------------------------------------------- gráficos
esq, dir_ = st.columns(2)

with esq:
    st.subheader("Contratado × realizado por mês")
    mensal = indicadores.evolucao_mensal(df)
    figura = px.bar(
        mensal.melt(id_vars="ano_mes", value_vars=["horas_contratadas", "horas_realizadas"],
                    var_name="tipo", value_name="horas"),
        x="ano_mes", y="horas", color="tipo", barmode="group",
        labels={"ano_mes": "Mês", "horas": "Horas", "tipo": ""},
    )
    st.plotly_chart(figura, use_container_width=True)

with dir_:
    st.subheader("Distribuição do desempenho")
    distribuicao = indicadores.distribuicao_classificacao(df)
    figura = px.pie(
        distribuicao, names="classificacao", values="servicos", hole=0.45,
        color="classificacao", color_discrete_map=CORES,
    )
    st.plotly_chart(figura, use_container_width=True)

esq, dir_ = st.columns(2)

with esq:
    st.subheader("Horas por cliente")
    clientes = indicadores.por_cliente(df)
    figura = px.bar(
        clientes.melt(id_vars="cliente", value_vars=["horas_contratadas", "horas_realizadas"],
                      var_name="tipo", value_name="horas"),
        x="horas", y="cliente", color="tipo", barmode="group", orientation="h",
        labels={"cliente": "", "horas": "Horas", "tipo": ""},
    )
    figura.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(figura, use_container_width=True)

with dir_:
    st.subheader("Aderência por motorista")
    motoristas = indicadores.por_motorista(df)
    figura = px.bar(
        motoristas, x="motorista", y="aderencia_media",
        labels={"motorista": "", "aderencia_media": "Aderência"},
        text=motoristas["aderencia_media"].round(2),
    )
    # linha de referência: 1,0 = entregou exatamente o contratado
    figura.add_hline(y=1.0, line_dash="dash", line_color="#555")
    st.plotly_chart(figura, use_container_width=True)

st.subheader("Serviços por dia")
diario = indicadores.servicos_por_dia(df)
figura = px.line(diario, x="data_servico", y="servicos", markers=True,
                 labels={"data_servico": "Data", "servicos": "Serviços"})
st.plotly_chart(figura, use_container_width=True)

esq, dir_ = st.columns(2)

with esq:
    st.subheader("Dispersão do desvio (horas)")
    finalizados = df[df["status"] == "finalizado"]
    figura = px.histogram(finalizados, x="desvio_horas", nbins=25,
                          labels={"desvio_horas": "Desvio (h)", "count": "Serviços"})
    figura.add_vline(x=0, line_dash="dash", line_color="#555")
    st.plotly_chart(figura, use_container_width=True)

with dir_:
    st.subheader("Demanda por dia da semana")
    semana = indicadores.demanda_por_dia_semana(df)
    figura = px.bar(semana, x="dia_semana", y="servicos",
                    labels={"dia_semana": "", "servicos": "Serviços"})
    st.plotly_chart(figura, use_container_width=True)

st.divider()

# ----------------------------------------------------------------- leituras
st.subheader("Leitura dos dados")
destaques = []
if (cliente := cliente_com_mais_horas(df)) is not None:
    destaques.append(f"**Cliente com mais horas:** {cliente['cliente']} — {cliente['horas_contratadas']:.1f} h contratadas")
if (excesso := cliente_com_maior_excesso(df)) is not None:
    destaques.append(f"**Maior excesso:** {excesso['cliente']} — {excesso['desvio_horas']:+.1f} h")
if (aderente := motorista_mais_aderente(df)) is not None:
    destaques.append(f"**Motorista mais aderente:** {aderente['motorista']} — aderência {aderente['aderencia_media']:.2f}")
if (produtivo := motorista_com_mais_horas(df)) is not None:
    destaques.append(f"**Motorista com mais horas:** {produtivo['motorista']} — {produtivo['horas_realizadas']:.1f} h")
if (dia := dia_de_maior_demanda(df)) is not None:
    destaques.append(f"**Dia de maior demanda:** {dia['data_servico'].date().strftime('%d/%m/%Y')} — {int(dia['servicos'])} serviços")
st.markdown("\n\n".join(f"- {linha}" for linha in destaques))

st.subheader("Maiores desvios do período")
st.dataframe(indicadores.maiores_desvios(df), use_container_width=True, hide_index=True)

st.subheader("Base para o Power BI")
st.caption("Exporte o dado já enriquecido para montar relatórios externos.")
st.download_button(
    "Baixar CSV do período",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"sonargest_{data_inicio}_{data_fim}.csv",
    mime="text/csv",
)


import plotly.express as px
import streamlit as st

import comum as c
from estatisticas import resumo_estatistico

SITUACOES = ["Ocupadas", "Não ocupadas"]


def render():
    st.header("D · Quem trabalha fora × quem não está ocupado")
    st.caption("Responsável: Ana Clara · Fonte: IBGE – PNAD Contínua, Tabela 7013")
    st.info("Pelo IBGE, **“Não ocupadas”** reúne as pessoas **desocupadas (desempregadas)** e as "
            "**fora da força de trabalho** (estudantes, aposentados, quem não procura emprego). "
            "A tabela não separa só os desempregados.")

    df = c.carregar_dados(7013, "tabela_7013_ocupacao_tratada.csv", "up_d")
    f = c.filtros(df)
    ufs, br = c.aplicar_filtros(df, f)
    ano = f["anos"][0]

    ufs = ufs[ufs["sexo"].isin(["Mulheres", "Homens"]) & ufs["recorte"].isin(SITUACOES)].copy()
    ufs["grupo"] = ufs["sexo"] + " – " + ufs["recorte"].str.lower()
    m = ufs.groupby(["sexo", "recorte"])["horas"].mean()

    c.kpis([
        ("Mulheres ocupadas", f"{c.fmt(m['Mulheres', 'Ocupadas'])} h"),
        ("Mulheres não ocupadas", f"{c.fmt(m['Mulheres', 'Não ocupadas'])} h",
         f"+{c.fmt(m['Mulheres', 'Não ocupadas'] - m['Mulheres', 'Ocupadas'])} h"),
        ("Homens ocupados", f"{c.fmt(m['Homens', 'Ocupadas'])} h"),
        ("Homens não ocupados", f"{c.fmt(m['Homens', 'Não ocupadas'])} h",
         f"+{c.fmt(m['Homens', 'Não ocupadas'] - m['Homens', 'Ocupadas'])} h"),
    ])
    st.caption("Médias das UFs selecionadas, em horas semanais.")

    resumo = m.reset_index()
    fig = px.bar(resumo, x="recorte", y="horas", color="sexo", barmode="group", text_auto=".1f",
                 color_discrete_map=c.CORES_SEXO, category_orders={"recorte": SITUACOES},
                 labels={"recorte": "Situação de ocupação", "horas": c.ROTULO_HORAS, "sexo": "Sexo"},
                 title=f"Horas semanais por situação de ocupação e sexo – {ano}")
    st.plotly_chart(fig, width="stretch")

    largo = ufs.pivot_table(index=["sigla_uf", "sexo"], columns="recorte", values="horas").reset_index()
    largo["Diferença"] = largo["Não ocupadas"] - largo["Ocupadas"]
    fig2 = px.bar(largo, x="sigla_uf", y="Diferença", color="sexo", barmode="group",
                  color_discrete_map=c.CORES_SEXO,
                  labels={"sigla_uf": "Estado (UF)", "Diferença": "Não ocupadas − Ocupadas (h)",
                          "sexo": "Sexo"},
                  title="Quantas horas a mais quem não está ocupado dedica, por estado")
    st.plotly_chart(fig2, width="stretch")

    st.subheader("Análise estatística")
    ordem = ["Mulheres – ocupadas", "Mulheres – não ocupadas", "Homens – ocupadas", "Homens – não ocupadas"]
    dados = ufs[["sigla_uf", "grupo", "horas"]].rename(columns={"horas": "valor"})
    dados = dados.set_index("grupo").loc[ordem].reset_index()
    c.bloco_estatistico(dados[["sigla_uf", "grupo", "valor"]], "Sexo e situação")

    st.subheader("Resposta para a persona")
    r = {g: resumo_estatistico(dados.loc[dados["grupo"] == g, "valor"]) for g in ordem}
    separadas = r["Mulheres – não ocupadas"]["q1"] > r["Mulheres – ocupadas"]["q3"]
    dif_m = m["Mulheres", "Não ocupadas"] - m["Mulheres", "Ocupadas"]
    dif_h = m["Homens", "Não ocupadas"] - m["Homens", "Ocupadas"]
    texto = (f"Em {ano}, mulheres não ocupadas dedicaram **{c.fmt(dif_m)} h a mais** por semana que "
             f"as ocupadas; entre os homens, a diferença foi de **{c.fmt(dif_h)} h**. ")
    if separadas:
        texto += ("No boxplot, as caixas das mulheres ocupadas e não ocupadas **não se sobrepõem** "
                  "(Q1 das não ocupadas > Q3 das ocupadas): a diferença aparece em praticamente "
                  "todos os estados, não só na média. ")
    else:
        texto += "As caixas do boxplot se sobrepõem em parte, então a diferença varia entre os estados. "
    if m["Mulheres", "Ocupadas"] > m["Homens", "Não ocupadas"]:
        texto += (f"Mesmo **trabalhando fora**, as mulheres dedicam mais horas "
                  f"({c.fmt(m['Mulheres', 'Ocupadas'])} h) que os **homens sem ocupação** "
                  f"({c.fmt(m['Homens', 'Não ocupadas'])} h) — é a dupla jornada feminina. ")
    texto += ("Observação: a tabela do IBGE não traz margem de erro, por isso a comparação é "
              "descritiva (não é um teste estatístico de significância).")
    st.markdown(texto)

    c.secao_noticias(["carga_mental", "economia_cuidado", "ibge"], "parte_d")

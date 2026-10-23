"""
Dashboard didático de controladoria de pavimentação com Assistente GPT (Microsoft Foundry).
Dados 100% fictícios.
"""
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
try:
    from openai import AzureOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Configuração da página Streamlit
st.set_page_config(page_title="ObraVision | Controladoria & IA", page_icon="🏗️", layout="wide")

st.markdown("""<style>
.block-container{padding-top:1.4rem;max-width:1500px}
h1,h2,h3{color:#18314d}
[data-testid="stMetric"]{background:#f4f7fa;border:1px solid #dfe6ed;border-radius:12px;padding:16px}
</style>""", unsafe_allow_html=True)

CATEGORIAS = ["Materiais", "Mão de obra", "Equipamentos / frota", "Combustíveis", "Manutenção de veículos", "Terceiros e indiretos"]
PESOS = {"Materiais": .37, "Mão de obra": .23, "Equipamentos / frota": .15, "Combustíveis": .10, "Manutenção de veículos": .05, "Terceiros e indiretos": .10}
OBRAS = [
    ("OBR-001", "Av. das Nações", 12000, 450000, 390000, .90, .88, 1.05),
    ("OBR-002", "Rua das Flores", 8500, 320000, 295000, 1.0, 1.0, .98),
    ("OBR-003", "Av. Industrial", 16000, 720000, 750000, 1.0, 1.0, 1.12),
    ("OBR-004", "Rua Primavera", 10500, 410000, 335000, .85, .82, .96),
    ("OBR-005", "Av. Central", 19000, 890000, 650000, .75, .72, 1.08),
    ("OBR-006", "Rua do Comércio", 7200, 280000, 265000, .95, .92, 1.02),
    ("OBR-007", "Av. Brasil", 14500, 640000, 490000, .80, .78, .93),
    ("OBR-008", "Rua dos Ipês", 9300, 370000, 305000, .90, .87, 1.10),
]

MULTIPLICADORES = {
    "OBR-001": [1.00, 1.00, 1.05, 1.14, 1.10, 1.00],
    "OBR-002": [1.00, .98, .96, .95, .94, 1.00],
    "OBR-003": [1.02, 1.00, 1.12, 1.30, 1.28, 1.00],
    "OBR-004": [1.00, 1.00, .95, .92, .90, 1.00],
    "OBR-005": [1.00, 1.00, 1.12, 1.22, 1.18, 1.00],
    "OBR-006": [1.00, 1.00, 1.03, 1.08, 1.06, 1.00],
    "OBR-007": [1.00, 1.00, .94, .88, .90, 1.00],
    "OBR-008": [1.00, 1.00, 1.12, 1.20, 1.24, 1.00],
}

def moeda(v):
    return "R$ " + f"{v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")

def pct(v):
    return f"{v:.1f}%".replace(".", ",")

@st.cache_data
def dados_base():
    linhas = []
    for ident, nome, area, receita, orcamento, fisico, financeiro, fator in OBRAS:
        mult = MULTIPLICADORES[ident]
        ponderado = sum(PESOS[c] * mult[i] for i, c in enumerate(CATEGORIAS))
        for i, cat in enumerate(CATEGORIAS):
            previsto = orcamento * PESOS[cat]
            realizado = orcamento * fisico * fator * PESOS[cat] * mult[i] / ponderado
            linhas.append({
                "ID": ident, "Obra": nome, "Área (m²)": area, "Receita contratada": receita,
                "Orçamento total": orcamento, "Avanço físico": fisico, "Avanço financeiro": financeiro,
                "Fator de custo": fator, "Categoria": cat, "Orçamento categoria": previsto,
                "Custo realizado categoria": realizado
            })
    return pd.DataFrame(linhas)

st.title("🏗️ ObraVision | Inteligência de Custos e Resultados")
st.caption("Portfólio de controladoria • 8 obras de pavimentação • Simulação fictícia • Integre com Microsoft Foundry")

# Barra lateral
st.sidebar.header("⚙️ Painel de Controle")
base = dados_base()
nomes = base["Obra"].drop_duplicates().tolist()
selecionadas = st.sidebar.multiselect("Obras analisadas", nomes, default=nomes)

if not selecionadas:
    st.warning("Selecione ao menos uma obra.")
    st.stop()

st.sidebar.divider()
st.sidebar.subheader("Premissas de Projeção")
st.sidebar.caption("As variações incidem apenas sobre o saldo a executar, exceto o aditivo de receita.")
aditivo = st.sidebar.slider("Aditivo de receita contratual (%)", -20, 30, 0, 1)
preco_comb = st.sidebar.slider("Variação futura do combustível (%)", -30, 60, 0, 1)
preco_manut = st.sidebar.slider("Variação futura da manutenção (%)", -30, 60, 0, 1)
preco_frota = st.sidebar.slider("Variação futura de frota (%)", -30, 60, 0, 1)
preco_outros = st.sidebar.slider("Variação futura dos demais custos (%)", -30, 60, 0, 1)
produtividade = st.sidebar.slider("Eficiência operacional futura (%)", -20, 20, 0, 1, help="Valor positivo reduz os custos futuros; negativo aumenta.")

st.sidebar.divider()
st.sidebar.subheader("🔑 Conexão Microsoft Foundry / Azure AI")
minha_chave = st.sidebar.text_input("Chave da API (minha_chave)", type="password", help="Chave de acesso do Azure OpenAI / Foundry")
meu_endpoint = st.sidebar.text_input("Endpoint (meu_endpoint)", placeholder="https://seu-recurso.openai.azure.com/")
meu_modelo = st.sidebar.text_input("Nome do Modelo / Deployment (meu_modelo)", placeholder="gpt-4o")

fat = {
    "Combustíveis": 1 + preco_comb / 100,
    "Manutenção de veículos": 1 + preco_manut / 100,
    "Equipamentos / frota": 1 + preco_frota / 100,
    "Materiais": 1 + preco_outros / 100,
    "Mão de obra": 1 + preco_outros / 100,
    "Terceiros e indiretos": 1 + preco_outros / 100
}
fat_eficiencia = 1 - produtividade / 100

x = base[base["Obra"].isin(selecionadas)].copy()
x["Orçado até a etapa"] = x["Orçamento categoria"] * x["Avanço físico"]
x["Saldo orçado"] = x["Orçamento categoria"] * (1 - x["Avanço físico"])
x["Saldo futuro base"] = x["Custo realizado categoria"] / x["Avanço físico"].replace(0, float("nan")) * (1 - x["Avanço físico"])
x["Saldo futuro base"] = x["Saldo futuro base"].fillna(x["Saldo orçado"])
x["Custo futuro cenário"] = x["Saldo futuro base"] * x["Categoria"].map(fat) * fat_eficiencia
x["Custo final cenário"] = x["Custo realizado categoria"] + x["Custo futuro cenário"]

agr = {
    "Área (m²)": "first", "Receita contratada": "first", "Orçamento total": "first",
    "Avanço físico": "first", "Avanço financeiro": "first", "Orçado até a etapa": "sum",
    "Custo realizado categoria": "sum", "Saldo futuro base": "sum",
    "Custo futuro cenário": "sum", "Custo final cenário": "sum"
}
res = x.groupby(["ID", "Obra"], as_index=False).agg(agr)
res["Receita gerencial estimada"] = res["Receita contratada"] * res["Avanço financeiro"]
res["Resultado gerencial atual"] = res["Receita gerencial estimada"] - res["Custo realizado categoria"]
res["Desvio atual (R$)"] = res["Custo realizado categoria"] - res["Orçado até a etapa"]
res["Desvio atual (%)"] = 100 * res["Desvio atual (R$)"] / res["Orçado até a etapa"].replace(0, float("nan"))
res["Receita final cenário"] = res["Receita contratada"] * (1 + aditivo / 100)
res["Resultado final cenário"] = res["Receita final cenário"] - res["Custo final cenário"]
res["Margem final cenário (%)"] = 100 * res["Resultado final cenário"] / res["Receita final cenário"].replace(0, float("nan"))
res["Custo final base"] = res["Custo realizado categoria"] + res["Saldo futuro base"]
res["Resultado final base"] = res["Receita contratada"] - res["Custo final base"]
res["Impacto cenário"] = res["Resultado final cenário"] - res["Resultado final base"]
res["Custo por m² executado"] = res["Custo realizado categoria"] / (res["Área (m²)"] * res["Avanço físico"]).replace(0, float("nan"))
res["Situação"] = res.apply(lambda r: "🔴 Prejuízo projetado" if r["Resultado final cenário"] < 0 else ("🟠 Desvio atual > 5%" if r["Desvio atual (%)"] > 5 else "🟢 Acompanhamento"), axis=1)

atual_receita = res["Receita gerencial estimada"].sum()
atual_custo = res["Custo realizado categoria"].sum()
projet_receita = res["Receita final cenário"].sum()
projet_custo = res["Custo final cenário"].sum()
resultado = projet_receita - projet_custo

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📊 Visão executiva", "🚚 Frota e combustíveis", "🔮 Simulador de cenários", "📋 Detalhamento e exportação", "🤖 Assistente GPT"
])

with aba1:
    st.subheader("Visão executiva | realizado até a data-base simulada")
    a, b, c, d = st.columns(4)
    a.metric("Receita gerencial estimada", moeda(atual_receita))
    b.metric("Custo realizado", moeda(atual_custo))
    c.metric("Resultado gerencial atual", moeda(atual_receita - atual_custo))
    d.metric("Margem gerencial atual", pct(100 * (atual_receita - atual_custo) / atual_receita) if atual_receita else "—")
    
    st.subheader("Visão projetada | conclusão dos contratos")
    a, b, c, d = st.columns(4)
    a.metric("Receita final no cenário", moeda(projet_receita))
    b.metric("Custo final estimado (EAC)", moeda(projet_custo))
    c.metric("Resultado final projetado", moeda(resultado), delta=moeda(res["Impacto cenário"].sum()) + " vs. base")
    d.metric("Margem final projetada", pct(100 * resultado / projet_receita) if projet_receita else "—")
    
    l, r = st.columns(2)
    with l:
        graf = res.melt(id_vars="Obra", value_vars=["Receita final cenário", "Custo final cenário"], var_name="Indicador", value_name="R$")
        fig = px.bar(graf, x="Obra", y="R$", color="Indicador", barmode="group", color_discrete_sequence=["#226d92", "#e5a347"], title="Receita x Custo final projetado")
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    with r:
        fig = px.bar(res, x="Obra", y="Resultado final cenário", color="Resultado final cenário", color_continuous_scale="RdYlGn", title="Resultado projetado por obra")
        fig.update_layout(xaxis_tickangle=-25, coloraxis_showscale=False)
        fig.add_hline(y=0, line_color="#667085")
        st.plotly_chart(fig, use_container_width=True)

with aba2:
    st.subheader("Estrutura de custos | frota, combustível e manutenção")
    cats = x.groupby("Categoria", as_index=False)[["Orçado até a etapa", "Custo realizado categoria", "Custo futuro cenário"]].sum()
    l, r = st.columns(2)
    with l:
        fig = px.bar(cats, x="Categoria", y=["Orçado até a etapa", "Custo realizado categoria"], barmode="group", title="Orçado proporcional x realizado por natureza", color_discrete_sequence=["#226d92", "#e5a347"])
        fig.update_layout(xaxis_tickangle=-20, legend_title="")
        st.plotly_chart(fig, use_container_width=True)
    with r:
        fig = px.pie(cats, names="Categoria", values="Custo realizado categoria", hole=.55, title="Composição do custo realizado", color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig, use_container_width=True)
    
    focos = ["Equipamentos / frota", "Combustíveis", "Manutenção de veículos"]
    f = x[x["Categoria"].isin(focos)].copy()
    frota_real = f["Custo realizado categoria"].sum()
    frota_orc = f["Orçado até a etapa"].sum()
    
    a, b, c = st.columns(3)
    a.metric("Frota + combustível + manutenção", moeda(frota_real))
    b.metric("Desvio desses custos", moeda(frota_real - frota_orc))
    c.metric("Participação no custo realizado", pct(100 * frota_real / atual_custo) if atual_custo else "—")

with aba3:
    st.subheader("Simulador interativo | e se os custos ou a receita mudarem?")
    a, b, c = st.columns(3)
    a.metric("Resultado no cenário base", moeda(res["Resultado final base"].sum()))
    b.metric("Resultado no cenário ajustado", moeda(resultado))
    c.metric("Impacto incremental", moeda(res["Impacto cenário"].sum()))
    
    impacto_receita = projet_receita - res["Receita contratada"].sum()
    impacto_custo = -(res["Custo futuro cenário"].sum() - res["Saldo futuro base"].sum())
    fig = go.Figure(go.Waterfall(
        x=["Resultado base", "Aditivos de receita", "Variação de custos futuros", "Resultado ajustado"],
        measure=["absolute", "relative", "relative", "total"],
        y=[res["Resultado final base"].sum(), impacto_receita, impacto_custo, resultado],
        connector={"line": {"color": "#9aa6b2"}},
        increasing={"marker": {"color": "#238a75"}},
        decreasing={"marker": {"color": "#cc6659"}},
        totals={"marker": {"color": "#226d92"}}
    ))
    fig.update_layout(title="Ponte do resultado (Waterfall)")
    st.plotly_chart(fig, use_container_width=True)

with aba4:
    st.subheader("Análise detalhada por contrato")
    vis = ["ID", "Obra", "Área (m²)", "Avanço físico", "Avanço financeiro", "Receita contratada", "Orçamento total", "Orçado até a etapa", "Custo realizado categoria", "Desvio atual (R$)", "Desvio atual (%)", "Resultado gerencial atual", "Custo final cenário", "Receita final cenário", "Resultado final cenário", "Margem final cenário (%)", "Custo por m² executado", "Situação"]
    st.dataframe(res[vis].rename(columns={"Custo realizado categoria": "Custo realizado"}).style.format({
        "Avanço físico": "{:.0%}", "Avanço financeiro": "{:.0%}", "Desvio atual (%)": "{:.1f}%", "Margem final cenário (%)": "{:.1f}%",
        **{c: "{:,.2f}" for c in ["Receita contratada", "Orçamento total", "Orçado até a etapa", "Custo realizado", "Desvio atual (R$)", "Resultado gerencial atual", "Custo final cenário", "Receita final cenário", "Resultado final cenário", "Custo por m² executado"]}
    }), use_container_width=True, hide_index=True)
    
    st.download_button("⬇️ Baixar resumo CSV", res.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"), "obras_resumo.csv", "text/csv")

with aba5:
    st.subheader("🤖 Assistente de Controladoria com IA (Microsoft Foundry)")
    st.write("Faça perguntas diretas sobre os dados do portfólio de obras.")
    
    if not HAS_OPENAI:
        st.error("A biblioteca `openai` não está instalada. Execute `pip install openai` para habilitar este recurso.")
    elif not minha_chave or not meu_endpoint or not meu_modelo:
        st.warning("⚠️ Insira as credenciais de conexão (Chave, Endpoint e Modelo) na barra lateral esquerda para ativar o assistente.")
    else:
        pergunta = st.text_input("Qual é a sua dúvida sobre o desempenho financeiro das obras?", placeholder="Ex: Quais obras estão com desvio de custo acima de 5% e qual o maior impacto?")
        
        if st.button("Perguntar à IA"):
            if not pergunta.strip():
                st.warning("Por favor, digite uma pergunta.")
            else:
                with st.spinner("Analisando dados do portfólio..."):
                    try:
                        client = AzureOpenAI(
                            azure_endpoint=meu_endpoint,
                            api_key=minha_chave,
                            api_version="2024-02-01"
                        )
                        
                        # Prepara o contexto dos dados em formato markdown
                        resumo_texto = res[["ID", "Obra", "Avanço físico", "Desvio atual (%)", "Resultado final cenário", "Situação"]].to_markdown(index=False)
                        
                        prompt_sistema = f"""Você é um especialista em controladoria de obras e engenharia civil.
Sua tarefa é analisar os dados financeiros e operacionais do portfólio abaixo e responder às dúvidas do gestor de forma concisa, técnica e direta.

Dados atuais do portfólio:
{resumo_texto}

Premissas simuladas:
- Aditivo de receita: {aditivo}%
- Variação combustível: {preco_comb}%
- Variação manutenção: {preco_manut}%
- Eficiência: {produtividade}%
"""
                        
                        resposta = client.chat.completions.create(
                            model=meu_modelo,
                            messages=[
                                {"role": "system", "content": prompt_sistema},
                                {"role": "user", "content": pergunta}
                            ],
                            temperature=0.2
                        )
                        
                        st.markdown("### 💬 Resposta do Assistente")
                        st.write(resposta.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Erro na conexão com a API do Microsoft Foundry / Azure OpenAI: {str(e)}")

st.divider()
st.caption("ObraVision • Python, Streamlit e IA Generativa")

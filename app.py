import io
import re
import unicodedata
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="ObraVision | Inteligência Financeira", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

NAVY = "#14253D"
BLUE = "#2563EB"
TEAL = "#0D9488"
RED = "#DC3545"
BG = "#F3F6FB"

# Estilo restrito: evita sobrescrever componentes internos do Streamlit.
st.markdown("""<style>
.stApp {background-color:#F4F7FC;}
.block-container {padding-top:1.5rem;max-width:1500px;}
[data-testid="stMetric"] {background-color:#FFFFFF;border:1px solid #E1E8F1;border-radius:12px;padding:14px;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def exemplo():
    return pd.DataFrame({
        "Obra": [f"Obra {i:02d}" for i in range(1, 9)],
        "Receita": [850000,1120000,760000,1400000,930000,1210000,680000,1580000],
        "Custo operacional": [620000,940000,590000,1090000,810000,970000,610000,1320000],
        "Combustível": [42000,57000,38000,69000,49000,60000,35000,75000],
        "Manutenção": [18000,23000,17000,32000,22000,27000,16000,36000],
        "Frota": [35000,44000,32000,54000,39000,48000,30000,62000],
    })

COLS = ["Obra", "Receita", "Custo operacional", "Combustível", "Manutenção", "Frota"]
NUM = COLS[1:]

def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def compact(v):
    sign = "−" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000: return f"{sign}R$ {v/1_000_000:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1000: return f"{sign}R$ {v/1000:,.1f} mil".replace(",", "X").replace(".", ",").replace("X", ".")
    return brl(-v if sign else v)

def preparar(df):
    df = df.copy()
    df.columns = [str(x).strip() for x in df.columns]
    if not set(COLS).issubset(df.columns):
        raise ValueError("O arquivo precisa conter as colunas: " + ", ".join(COLS))
    df = df[COLS]
    df["Obra"] = df["Obra"].astype(str).str.strip()
    if df["Obra"].eq("").any(): raise ValueError("Há obras sem identificação.")
    for c in NUM:
        if df[c].dtype == object:
            s = df[c].astype(str).str.strip().str.replace("R$", "", regex=False).str.replace(" ", "", regex=False)
            # Valores com vírgula são interpretados como padrão brasileiro.
            s = s.map(lambda x: x.replace(".", "").replace(",", ".") if "," in x else x)
            df[c] = pd.to_numeric(s, errors="raise")
        else:
            df[c] = pd.to_numeric(df[c], errors="raise")
    if df[NUM].isna().any().any(): raise ValueError("Há valores numéricos vazios.")
    if (df[NUM] < 0).any().any(): raise ValueError("Receitas e custos devem ser informados como valores não negativos.")
    if df["Obra"].duplicated().any():
        df = df.groupby("Obra", as_index=False)[NUM].sum()
    return calcular(df)

def calcular(df):
    d = df.copy()
    d["Custo total"] = d[["Custo operacional", "Combustível", "Manutenção", "Frota"]].sum(axis=1)
    d["Resultado"] = d["Receita"] - d["Custo total"]
    d["Margem (%)"] = (d["Resultado"] / d["Receita"].replace(0, np.nan) * 100).fillna(0)
    return d

def grafico_layout(fig, height=360, pct=False):
    fig.update_layout(height=height, margin=dict(l=10,r=12,t=32,b=15), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", color=NAVY, size=12), legend=dict(orientation="h", y=1.13, x=0), hovermode="x unified")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#E3EAF3", zeroline=False, tickformat=".1f" if pct else "~s")
    return fig

def chart_receita(d):
    f=go.Figure()
    f.add_bar(x=d["Obra"], y=d["Receita"], name="Receita", marker_color=BLUE, hovertemplate="%{x}: R$ %{y:,.2f}<extra></extra>")
    f.add_bar(x=d["Obra"], y=d["Custo total"], name="Custo total", marker_color="#74C5E8", hovertemplate="%{x}: R$ %{y:,.2f}<extra></extra>")
    f.update_layout(barmode="group", title="Receita x custo por obra")
    return grafico_layout(f)

def chart_margem(d):
    d=d.sort_values("Margem (%)")
    f=go.Figure(go.Bar(x=d["Margem (%)"],y=d["Obra"],orientation="h", marker_color=[TEAL if x>=10 else ("#F59E0B" if x>=0 else RED) for x in d["Margem (%)"]], text=[f"{x:.1f}%" for x in d["Margem (%)"]], textposition="outside", cliponaxis=False))
    f.update_layout(title="Ranking de margem (%)", showlegend=False)
    f.add_vline(x=10,line_dash="dot",line_color="#94A3B8")
    return grafico_layout(f)

import io
import re
import unicodedata
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sst.write("TESTE: O STREAMLIT ESTÁ EXECUTANDO O CÓDIGO")page_title='ObraVision | Inteligência Financeira', page_icon='🏗️', layout='wide', initial_sidebar_state='expanded')
NAVY='#14243A'; BLUE='#2563EB'; CYAN='#06B6D4'; GREEN='#0F9F79'; RED='#E05252'; GOLD='#E7A83E'; MUTED='#64748B'; BG='#F4F7FB'
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:Inter, sans-serif;}
.stApp {background:#F4F7FB;color:#14243A;}
.block-container {padding-top:1.5rem;padding-bottom:3rem;max-width:1550px;}
[data-testid="stSidebar"] {background:#14243A;}
[data-testid="stSidebar"] * {color:#ECF3FF!important;}
[data-testid="stSidebar"] input {color:#14243A!important;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:#14243A!important;}
h1,h2,h3 {color:#14243A!important;letter-spacing:-.025em;}
.hero {padding:23px 29px;background:linear-gradient(105deg,#14243A,#214F85);border-radius:18px;color:white;margin-bottom:20px;box-shadow:0 9px 28px #14243A18;}
.hero h1 {color:white!important;font-size:2rem;margin:0 0 5px 0;}
.hero p {color:#D5E4F5;margin:0;}
.kpi {background:white;border:1px solid #E5ECF4;border-radius:15px;padding:19px 20px;box-shadow:0 4px 16px #14243A0A;min-height:135px;}
.kpi-label {font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:#64748B;font-weight:700;}
.kpi-value {font-size:clamp(19px,2vw,29px);font-weight:800;color:#14243A;margin-top:11px;white-space:nowrap;}
.kpi-foot {font-size:12px;color:#64748B;margin-top:8px;}
.section-title {font-weight:800;font-size:1.18rem;color:#14243A;margin:23px 0 10px;}
.note {padding:12px 16px;background:#E9F1FF;border-left:4px solid #2563EB;border-radius:8px;color:#284568;}
[data-testid="stPlotlyChart"] {background:white;border:1px solid #E5ECF4;border-radius:15px;padding:6px;box-shadow:0 4px 16px #14243A08;}
[data-testid="stMetric"] {background:white;padding:14px;border-radius:12px;}
</style>''', unsafe_allow_html=True)

COLS=['Obra','Receita','Custo operacional','Combustível','Manutenção','Frota']
@st.cache_data
def sample():
    return pd.DataFrame({'Obra':[f'Obra {i:02d}' for i in range(1,9)],'Receita':[850000,1120000,760000,1400000,930000,1210000,680000,1580000], 'Custo operacional':[620000,940000,590000,1090000,810000,970000,610000,1320000], 'Combustível':[42000,57000,38000,69000,49000,60000,35000,75000], 'Manutenção':[18000,23000,17000,32000,22000,27000,16000,36000], 'Frota':[35000,44000,32000,54000,39000,48000,30000,62000]})

def money(x,short=False):
    if short:
        a=abs(x)
        if a>=1e6:return ('-' if x<0 else '')+'R$ '+f'{a/1e6:.2f}'.replace('.',',')+' mi'
        if a>=1e3:return ('-' if x<0 else '')+'R$ '+f'{a/1e3:.0f}'.replace('.',',')+' mil'
    return 'R$ '+f'{x:,.2f}'.replace(',','X').replace('.',',').replace('X','.')

def pct(x):return f'{x:.2f}%'.replace('.',',')

def prep(d):
    d=d.copy()
    d['Custo total']=d[['Custo operacional','Combustível','Manutenção','Frota']].sum(axis=1)
    d['Resultado']=d['Receita']-d['Custo total']
    d['Margem (%)']=np.where(d['Receita']>0,d['Resultado']/d['Receita']*100,0)
    d['Status']=np.select([d['Resultado']<0,d['Margem (%)']<8],['Prejuízo','Atenção'],default='Saudável')
    return d

def layout(fig,height=360):
    fig.update_layout(height=height,margin=dict(l=20,r=20,t=45,b=25),paper_bgcolor='white',plot_bgcolor='white',font=dict(family='Inter, Arial',color=NAVY,size=12),legend=dict(orientation='h',y=-.25,x=0),hovermode='x unified')
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#E9EEF6',zeroline=False,tickformat=',.0f')
    return fig

def kpi(title,value,foot,color=NAVY):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{title}</div><div class="kpi-value" style="color:{color}">{value}</div><div class="kpi-foot">{foot}</div></div>',unsafe_allow_html=True)

def normalize(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))

def assistant(question,d):
    q=normalize(question)
    if not q.strip():return 'Digite uma pergunta para iniciar a análise.'
    worst=d.loc[d['Resultado'].idxmin()]; best=d.loc[d['Margem (%)'].idxmax()]
    total=d['Receita'].sum();cost=d['Custo total'].sum();res=total-cost
    if any(x in q for x in ['prejuizo','negativ','pior obra','pior resultado']):
        bad=d[d['Resultado']<0].sort_values('Resultado')
        return ('Obras com prejuízo: '+ '; '.join(f"{r['Obra']}: {money(r['Resultado'])}" for _,r in bad.iterrows()) if len(bad) else f"Nenhuma obra selecionada apresenta prejuízo. O menor resultado é {worst['Obra']}: {money(worst['Resultado'])}.")
    if any(x in q for x in ['melhor margem','mais rentavel','maior margem']):return f"{best['Obra']} apresenta a maior margem: {pct(best['Margem (%)'])}, com resultado de {money(best['Resultado'])}."
    if any(x in q for x in ['combustivel','diesel']):
        nums=re.findall(r'(\d+(?:[.,]\d+)?)\s*%',q)
        if nums:
            n=float(nums[0].replace(',','.')); delta=d['Combustível'].sum()*n/100
            return f"Com aumento de {pct(n)} no combustível, o custo sobe {money(delta)} e o resultado consolidado cai de {money(res)} para {money(res-delta)}."
        return f"O gasto de combustível soma {money(d['Combustível'].sum())}, equivalente a {pct(d['Combustível'].sum()/cost*100 if cost else 0)} dos custos totais."
    if any(x in q for x in ['custo','despesa','frota','manutencao']):
        fields=['Custo operacional','Combustível','Manutenção','Frota']; field=max(fields,key=lambda x:d[x].sum())
        return f"O maior grupo de custos é {field}: {money(d[field].sum())}. O custo total é {money(cost)}, representando {pct(cost/total*100 if total else 0)} da receita."
    if any(x in q for x in ['risco','atencao','alerta']):
        risky=d[d['Status']!='Saudável'].sort_values('Margem (%)')
        return ('Obras que exigem atenção (margem abaixo de 8% ou prejuízo): '+', '.join(f"{r['Obra']} ({pct(r['Margem (%)'])})" for _,r in risky.iterrows()) if len(risky) else 'Todas as obras selecionadas estão acima do limite de atenção de 8% e apresentam resultado positivo.')
    if any(x in q for x in ['resultado','lucro','receita','margem','resumo','analise']):return f"Receita: {money(total)}; custos: {money(cost)}; resultado: {money(res)}; margem: {pct(res/total*100 if total else 0)}. Melhor margem: {best['Obra']} ({pct(best['Margem (%)'])})."
    return 'Posso analisar resultado, margem, custos, combustível, prejuízos e riscos. Exemplos: “Qual obra tem a melhor margem?”, “Há obras com prejuízo?” ou “E se o combustível subir 15%?”. Este assistente usa regras financeiras, não um modelo generativo.'

with st.sidebar:
    st.markdown('## 🏗️ ObraVision')
    st.caption('CONTROLADORIA • BUSINESS INTELLIGENCE')
    st.divider()

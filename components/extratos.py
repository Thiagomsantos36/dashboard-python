import dash
from dash.dependencies import Input, Output
from dash import dash_table
from dash.dash_table.Format import Group
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app import app
from dash_bootstrap_templates import template_from_url, ThemeChangerAIO

# =========  Layout  =========== #
layout = dbc.Col([
    dbc.Row([
        html.Legend("Tabela de despesas"),
        html.Div(id="tabela-despesas", className="dbc"),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-graph', style={"margin-right": "20px"}),
        ], width=9),
        
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Despesas"),
                    html.Legend("R$ -", id="valor_despesa_card", style={'font-size': '60px'}),
                    html.H6("Total de despesas"),
                ], style={'text-align': 'center', 'padding-top': '30px'}))
        ], width=3),
    ]),
], style={"padding": "10px"})

# =========  Callbacks  =========== #
# Tabela
@app.callback(
    Output('tabela-despesas', 'children'),
    Input('store-despesas', 'data')
)
def imprimir_tabela (data):
    df = pd.DataFrame(data)
    df['Data'] = pd.to_datetime(df['Data']).dt.date

    df.loc[df['Efetuado'] == 0, 'Efetuado'] = 'Não'
    df.loc[df['Efetuado'] == 1, 'Efetuado'] = 'Sim'

    df.loc[df['Fixo'] == 0, 'Fixo'] = 'Não'
    df.loc[df['Fixo'] == 1, 'Fixo'] = 'Sim'

    df = df.fillna('-')

    df.sort_values(by='Data', ascending=False)

    tabela = dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": False, "hideable": True}
            if i == "Descrição" or i == "Fixo" or i == "Efetuado"
            else {"name": i, "id": i, "deletable": False, "selectable": False}
            for i in df.columns
        ],

        data=df.to_dict('records'),
        filter_action="native",    
        sort_action="native",       
        sort_mode="single",  
        selected_columns=[],        
        selected_rows=[],          
        page_action="native",      
        page_current=0,             
        page_size=10,                        
    ),

    return tabela

# Bar Graph            
@app.callback(
    Output('bar-graph', 'figure'),
    [Input('store-despesas', 'data'),
    Input(ThemeChangerAIO.ids.radio("theme"), "value")]
)
def bar_chart(data, theme):
    df = pd.DataFrame(data)   
    df_grouped = df.groupby("Categoria").sum()[["Valor"]].reset_index()
    graph = px.bar(df_grouped, x='Categoria', y='Valor', title="Despesas Gerais")
    graph.update_layout(template=template_from_url(theme))
    graph.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return graph

# Simple card
@app.callback(
    Output('valor_despesa_card', 'children'),
    Input('store-despesas', 'data')
)
def display_desp(data):
    df = pd.DataFrame(data)
    
    valor = df['Valor'].sum()

    # Chamar a função para enviar o e-mail
    destinatario = "thiaguinho.cascao@gmail.com"
    assunto = "Relatório diário das despesas"
    conteudo = "Olá, segue o relatório do dia conforme solicitado."
    enviar_email(destinatario, assunto, conteudo, data)  # Adicione o argumento 'data' aqui

    return f"R$ {valor}"


def enviar_email(destinatario, assunto, conteudo, dados_despesas):
    remetente = "thiaguinho.msantos@hotmail.com"
    senha = "bsjhyqzgejrkxaae"

    # Criar um DataFrame com os dados das despesas
    df_despesas = pd.DataFrame(dados_despesas)

    # Converter o DataFrame em uma string CSV
    dados_despesas_csv = df_despesas.to_csv(index=False)

    # Configurar mensagem de e-mail
    mensagem = MIMEMultipart()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto

    # Adicionar conteúdo ao corpo do e-mail
    mensagem.attach(MIMEText(conteudo, "plain"))

    # Anexar os dados das despesas ao e-mail
    anexo = MIMEText(dados_despesas_csv)
    anexo.add_header("Content-Disposition", "attachment", filename="df_despesas.csv")
    mensagem.attach(anexo)

    # Configurar servidor SMTP e enviar e-mail
    servidor_smtp = smtplib.SMTP("smtp.office365.com", 587)
    servidor_smtp.starttls()
    servidor_smtp.login(remetente, senha)
    servidor_smtp.sendmail(remetente, destinatario, mensagem.as_string())
    servidor_smtp.quit()


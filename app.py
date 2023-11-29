import streamlit as st
import pandas as pd
import geopandas as gpd
import streamlit.components.v1 as components
from PIL import Image
st.sidebar.title("ImedData")
st.subheader('Análise de Dados Segurança Pública')
st.sidebar.image("imed.png", width=300)

# Carregue a imagem
image = Image.open("logo.jpeg")

# Redimensione a imagem para 120x150
resized_image = image.resize((180, 180))

# Exiba a imagem redimensionada
st.image(resized_image, caption="Segurança Pública")

# Lista de nomes de arquivos
files = [
    "feminicidio_2018.csv",
    "feminicidio_2019.csv",
    "feminicidio_2020.csv",
    "feminicidio_2021.csv",
    "feminicidio_2022.csv",
    "feminicidio_2023.csv"
]

# Inicialize um DataFrame vazio para armazenar os dados
merged_df = pd.DataFrame()

# Loop pelos arquivos e concatene-os no DataFrame
for file in files:
    # Carregue o arquivo CSV em um DataFrame temporário com o separador correto ";"
    temp_df = pd.read_csv(file, sep=";")
    
    # Concatene o DataFrame temporário com o DataFrame principal
    merged_df = pd.concat([merged_df, temp_df], ignore_index=True)

# Converta a coluna "data_fato" para o formato de data
merged_df["data_fato"] = pd.to_datetime(merged_df["data_fato"])

# Crie um intervalo de datas mínimo e máximo


# Crie widgets para permitir ao usuário escolher um intervalo de datas

selected_option_tentado = st.radio("Selecione TENTADO ou CONSUMADO (Tentado):", ("TENTADO", "CONSUMADO"), key="tentado")
#selected_option = st.radio("Selecione TENTADO ou CONSUMADO:", ("TENTADO", "CONSUMADO"))
# Verifique se há valores NaT na coluna "data_fato"
if merged_df["data_fato"].notna().any():
    min_date = merged_df["data_fato"].min().date()
    max_date = merged_df["data_fato"].max().date()
else:
    # Caso não haja datas válidas, defina valores padrão
    min_date = max_date = pd.Timestamp.now().date()

# Crie widgets para permitir ao usuário escolher um intervalo de datas
start_date = st.date_input("Selecione a data inicial:", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("Selecione a data final:", min_value=min_date, max_value=max_date, value=max_date)
# Filtre o DataFrame com base nas datas e na coluna "tentado_consumado" selecionadas pelo usuário
filtered_df = merged_df[
    (merged_df["data_fato"].dt.date >= start_date) & 
    (merged_df["data_fato"].dt.date <= end_date) &
    (merged_df["tentado_consumado"] == selected_option_tentado)
]

# Converta a coluna "municipio_cod" para o tipo string e, em seguida, remova a vírgula
filtered_df["municipio_cod"] = filtered_df["municipio_cod"].astype(str).str.replace(",", "")

# Crie um novo DataFrame que exiba a soma da coluna "qtde_vitimas" por "municipio_cod"
#sum_by_municipio = filtered_df.groupby("municipio_cod")["qtde_vitimas"].sum().reset_index()
# Crie um novo DataFrame que exiba a soma da coluna "qtde_vitimas" e a primeira ocorrência da coluna "name" por "municipio_cod"
sum_by_municipio = filtered_df.groupby("municipio_cod").agg({"qtde_vitimas": "sum", "municipio_fato": "first"}).reset_index()
# Renomeie as colunas do DataFrame e reorganize a ordem das colunas
sum_by_municipio = sum_by_municipio.rename(columns={
    "municipio_cod": "Código Município",
    "qtde_vitimas": "Vítimas",
    "municipio_fato": "Município"
})[['Código Município', 'Município', 'Vítimas']]

# Exiba o DataFrame com as colunas renomeadas e reorganizadas

df_municipios = pd.read_csv('municipios.csv')
def extrair_cod(codigo_ibge):
    return int(str(codigo_ibge)[:-1])
df_municipios['cod'] = df_municipios['codigo_ibge'].apply(extrair_cod)
filtered_df["municipio_cod"] = filtered_df["municipio_cod"].astype(int)
df_municipios ["cod"] = df_municipios ["cod"].astype(int)
df_merged = pd.merge(filtered_df, df_municipios, left_on='municipio_cod', right_on='cod', how='inner')
# Agrupar por 'municipio_cod' e somar 'qtde_vitimas'
# Agrupar por 'municipio_cod' e somar 'qtde_vitimas', mantendo as colunas 'municipio_fato', 'latitude', 'longitude' e 'codigo_ibge'
total_vitimas_por_municipio = df_merged.groupby('municipio_cod', as_index=False).agg({
    'qtde_vitimas': 'sum',
    'municipio_fato': 'first',
    'latitude': 'first',
    'longitude': 'first',
    'codigo_ibge': 'first'
})

# Renomear as colunas resultantes
total_vitimas_por_municipio = total_vitimas_por_municipio.rename(columns={
    'qtde_vitimas': 'Total de Vítimas',
    'municipio_fato': 'Município',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'codigo_ibge': 'Código IBGE'
})

# Exibir o DataFrame com o total de vítimas, município, latitude, longitude e código IBGE
st.write(total_vitimas_por_municipio)
#st.write(df_merged )
geojson_path = 'municipios.geojson.json'

# Carregue o arquivo GeoJSON em um DataFrame geográfico
gdf = gpd.read_file(geojson_path)
gdf["id"] = gdf["id"].astype(int)
gdfj = gdf.merge(total_vitimas_por_municipio, left_on='id', right_on='Código IBGE', how='inner')
# Use o Streamlit para exibir o DataFrame com a soma das vítimas por município
#st.write(gdfj)
# Calcule a soma da coluna "qtde_vitimas"
total_vitimas = filtered_df["qtde_vitimas"].sum()

# Exiba a soma das vítimas com uma mensagem personalizada
st.write(f"Total de vítimas'{selected_option_tentado}': {total_vitimas}")
import folium
import geopandas as gpd
import numpy as np  # Importe numpy para usar a função logarítmica

# Crie um mapa Folium
m = folium.Map(
    location=[-18.235, -45.925],  # Coordenadas aproximadas do Brasil
    zoom_start=6,
    tiles='cartodb positron'  # Estilo do mapa
)
# Faça o merge entre os DataFrames
#gdf = gdf.merge(df_merged, left_on='id', right_on='codigo_ibge', how='inner')

# Aplique o logaritmo à coluna de proporção
gdfj ['log_proporcao_vitimas'] = np.log1p(gdfj ['Total de Vítimas'])  # Use log1p para evitar problemas com valores zero

# Crie a sobreposição de municípios preenchidos com base na coluna de proporção logarítmica
folium.Choropleth(
    geo_data=gdfj,
    name='choropleth',
    data=gdfj ,
    columns=['Código IBGE', 'log_proporcao_vitimas'],  # Use a coluna logarítmica aqui
    key_on='feature.properties.Código IBGE',
    fill_color='YlOrRd',  # Esquema de cores (YlOrRd é um exemplo)
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Proporção de Vítimas (log)'
).add_to(m)

# Adicione um controle de camadas (layers control) ao mapa
folium.LayerControl().add_to(m)

# Salve o mapa em um arquivo HTML
m.save('municipios_com_proporcao_log.html')

HtmlFile = open("municipios_com_proporcao_log.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
st.subheader('Mapa da violência/ Feminicídios em Minas')
#components.html(source_code,height = 600)


components.html(source_code,height = 600)
from folium import plugins

# Crie um mapa Folium
m = folium.Map(
    location=[-18.235, -45.925],  # Coordenadas aproximadas do Brasil
    zoom_start=6,
    tiles='cartodb positron'  # Estilo do mapa
)

# Converta a coluna 'proporcao_vitimas' em uma lista de coordenadas (latitude, longitude)
heat_data = [[row['latitude'], row['longitude'], row['Total de Vítimas']] for _, row in gdfj.iterrows()]

# Crie um mapa de calor (heatmap) com base nos dados de densidade
plugins.HeatMap(heat_data, gradient={0.2: 'lightgreen', 0.4: 'yellow', 0.6: 'orange', 0.8: 'red', 1.0: 'darkred'}, radius=10.5).add_to(m)

# Adicione o mapa de calor ao mapa Folium
# Salve o mapa em um arquivo HTML
m.save('municipios_com_proporcao_log2.html')


HtmlFile = open("municipios_com_proporcao_log2.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
st.subheader('Mapa de calor em relação ao Total de Vítimas/Feminicídio')
components.html(source_code,height = 600)

files2 = [
    "violencia_domestica_2014.csv",
    "violencia_domestica_2015.csv",
    "violencia_domestica_2016.csv",
    "violencia_domestica_2017.csv",
    "violencia_domestica_2018.csv",
    "violencia_domestica_2019.csv",
    "violencia_domestica_2020.csv",
    "violencia_domestica_2021.csv",
    "violencia_domestica_2022.csv",
    "violencia_domestica_2023.csv"
]
st.subheader('Violência contra Mulher')
# Inicialize um DataFrame vazio para armazenar os dados
merged_df2 = pd.DataFrame()

# Loop pelos arquivos e concatene-os no DataFrame
for file in files2:
    # Carregue o arquivo CSV em um DataFrame temporário com o separador correto ";"
    temp_df2 = pd.read_csv(file, sep=";")
    
    # Concatene o DataFrame temporário com o DataFrame principal
    merged_df2  = pd.concat([merged_df2, temp_df2], ignore_index=True)
# Visualize o mapa de calor no Jupyter Notebook
# Lista de valores únicos para "natureza_delito" e "tentado_consumado"
unique_natureza_delito = merged_df2["natureza_delito"].unique()
unique_tentado_consumado = merged_df2["tentado_consumado"].unique()

import streamlit as st
import pandas as pd

# Lista de valores únicos para "natureza_delito" e "tentado_consumado"
unique_natureza_delito = merged_df2["natureza_delito"].unique()
unique_tentado_consumado = merged_df2["tentado_consumado"].unique()

# Ordene a lista de "unique_natureza_delito" em ordem alfabética
unique_natureza_delito_sorted = sorted(unique_natureza_delito)

# Criar um seletor para "natureza_delito" com opções ordenadas
selected_natureza_delito = st.selectbox("Selecione a Natureza do Delito", unique_natureza_delito_sorted, index=unique_natureza_delito_sorted.index("ESTUPRO DE VULNERAVEL"))

# Criar uma lista de seleção para "tentado_consumado"
#selected_tentado_consumado = st.multiselect("Selecione Tentado/Consumado", unique_tentado_consumado)

#selected_option_consumado = st.radio("Selecione TENTADO ou CONSUMADO (Consumado):", ("TENTADO", "CONSUMADO"), key="consumado")
selected_option_consumado = st.radio("Selecione TENTADO ou CONSUMADO (CONSUMADO):", ("TENTADO", "CONSUMADO"), index=1, key="consumado")

# Filtrar o DataFrame com base nas seleções do usuário
filtered_df = merged_df2[
    (merged_df2["natureza_delito"] == selected_natureza_delito) &
    (merged_df2["tentado_consumado"]==(selected_option_consumado))
]

# Exibir o DataFrame filtrado
st.write("DataFrame Filtrado:")
#st.write(filtered_df)

# Converta a coluna "data_fato" para o formato de data, permitindo erros ("coerce")
filtered_df["data_fato"] = pd.to_datetime(filtered_df["data_fato"], errors="coerce")

# Remova as linhas com datas inválidas (NaT)
filtered_df = filtered_df.dropna(subset=["data_fato"])

# Verifique se há valores NaT na coluna "data_fato"
if filtered_df["data_fato"].notna().any():
    min_date = filtered_df["data_fato"].min().date()
    max_date = filtered_df["data_fato"].max().date()
else:
    # Caso não haja datas válidas, defina valores padrão
    min_date = max_date = pd.Timestamp.now().date()

# Crie widgets para permitir ao usuário escolher um intervalo de datas
start_date = st.date_input("Selecione a data inicial:", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("Selecione a data final:", min_value=min_date, max_value=max_date, value=max_date)

# Filtre o DataFrame com base nas datas selecionadas pelo usuário
filtered_df = filtered_df[
    (filtered_df["data_fato"].dt.date >= start_date) &
    (filtered_df["data_fato"].dt.date <= end_date)
]

# Exiba o DataFrame filtrado
st.write("DataFrame Filtrado por Data:")

total_vitimas = filtered_df["qtde_vitimas"].sum()

# Exibir a soma das vítimas com uma mensagem personalizada
st.write(f"Total de vítimas de {selected_natureza_delito}: {total_vitimas}")
diferenca_em_dias = (end_date - start_date).days

# Calcular a taxa de vítimas por dia
taxa_vitimas_por_dia = total_vitimas / diferenca_em_dias
sum_by_municipio2 = filtered_df.groupby("municipio_cod").agg({"qtde_vitimas": "sum", "municipio_fato": "first"}).reset_index()

# Renomeie as colunas
sum_by_municipio2 = sum_by_municipio2.rename(columns={
    "municipio_cod": "Código IBGE",
    "qtde_vitimas": "Total de Vítimas",
    "municipio_fato": "Município"
})

# Reorganize as colunas na ordem desejada
sum_by_municipio2 = sum_by_municipio2[["Código IBGE", "Município", "Total de Vítimas"]]



df_merged2 = pd.merge(sum_by_municipio2, df_municipios, left_on='Código IBGE', right_on='cod', how='inner')
gdfj2 = gdf.merge(df_merged2, left_on='id', right_on='codigo_ibge', how='inner')
st.write(sum_by_municipio2)
# Exibir a diferença em dias e a taxa de vítimas por dia com mensagens personalizadas
#st.write(f"Diferença em dias: {diferenca_em_dias}")
from folium import plugins

# Crie um mapa Folium
m = folium.Map(
    location=[-18.235, -45.925],  # Coordenadas aproximadas do Brasil
    zoom_start=6,
    tiles='cartodb positron'  # Estilo do mapa
)

# Converta a coluna 'proporcao_vitimas' em uma lista de coordenadas (latitude, longitude)
heat_data = [[row['latitude'], row['longitude'], row['Total de Vítimas']] for _, row in gdfj2.iterrows()]

# Crie um mapa de calor (heatmap) com base nos dados de densidade
plugins.HeatMap(heat_data, gradient={0.2: 'lightgreen', 0.4: 'yellow', 0.6: 'orange', 0.8: 'red', 1.0: 'darkred'}, radius=10.5).add_to(m)

# Adicione o mapa de calor ao mapa Folium
# Salve o mapa em um arquivo HTML
m.save('municipios_com_proporcao_log3.html')


HtmlFile = open("municipios_com_proporcao_log3.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
st.subheader(f'Mapa de calor em relação a {selected_natureza_delito}')
components.html(source_code,height = 600)
st.write(f"Média {selected_natureza_delito} por dia: {round(taxa_vitimas_por_dia,2)}")


# Crie um mapa Folium
m = folium.Map(
    location=[-18.235, -45.925],  # Coordenadas aproximadas do Brasil
    zoom_start=6,
    tiles='cartodb positron'  # Estilo do mapa
)

# Aplique o logaritmo à coluna de proporção
gdfj2['log_proporcao_vitimas'] = np.log1p(gdfj2['Total de Vítimas'])  # Use log1p para evitar problemas com valores zero

# Verifique se a lista 'features' no GeoJSON não está vazia
if len(gdfj2['Total de Vítimas']) > 0:
    # Crie a sobreposição de municípios preenchidos com base na coluna de proporção logarítmica
    folium.Choropleth(
        geo_data=gdfj2,
        name='choropleth',
        data=gdfj2,
        columns=['Código IBGE', 'log_proporcao_vitimas'],  # Use a coluna logarítmica aqui
        key_on='feature.properties.Código IBGE',
        fill_color='YlOrRd',  # Esquema de cores (YlOrRd é um exemplo)
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Proporção de Vítimas (log)'
    ).add_to(m)

    # Adicione um controle de camadas (layers control) ao mapa
    folium.LayerControl().add_to(m)

    # Salve o mapa em um arquivo HTML
    m.save('municipios_com_proporcao_log5.html')

    HtmlFile = open("municipios_com_proporcao_log5.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    st.subheader(f'Mapa da violência/{selected_natureza_delito}')
    components.html(source_code, height=600)
else:
    st.warning('Não há dados disponíveis para exibição no mapa.')


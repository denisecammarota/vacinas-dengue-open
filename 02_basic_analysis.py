from pathlib import Path
import pandas as pd
import numpy as np
from epiweeks import Week
import seaborn as sns
import matplotlib.pyplot as plt 
import geopandas as gpd
from matplotlib.colors import LogNorm

# Loading all dengue vaccines in 2026 #########################################

folder = Path("dengue_all")

files = sorted(folder.glob("*.parquet"))

df = pd.concat(
    (pd.read_parquet(f) for f in files),
    ignore_index=True
)

print(df.shape) # 2.839.916 total counts 

# Which vaccine names? ########################################################
# Vacina dengue (atenuada) codigo 104, 2.784.982 doses
# Vacina dengue codigo 82, 54.934 doses

df['co_vacina'].value_counts()
df['ds_vacina'].value_counts()


# Which are the manufacturers? ################################################
# Not as straightforward as TAKEDA/BUTANTAN

df['ds_vacina_fabricante'].value_counts()

print(df["ds_vacina_fabricante"].value_counts().to_string())


# Which are Butantan Vaccines #################################################
# Assuming that codigo is FUNDACAO BUTANTAN is only for BUTANTAN

df_butantan = df[df['ds_vacina_fabricante'] == 'FUNDACAO BUTANTAN']


# Butantan - epidemiological analysis #########################################

## Tempo/Time #################################################################

df_butantan["dt_vacina"] = pd.to_datetime(df_butantan["dt_vacina"])
df_butantan['dt_vacina']

df_butantan["epiyear"] = df_butantan["dt_vacina"].apply(lambda d: Week.fromdate(d).year)
df_butantan["epiweek"] = df_butantan["dt_vacina"].apply(lambda d: Week.fromdate(d).week)

df_plot = df_butantan.groupby(['epiyear', 'epiweek', 'ds_dose_vacina']).size().reset_index(name='count')

df_plot['time'] = df_plot['epiyear'] + (df_plot['epiweek']/52)

plt.figure(figsize=(12, 6))

sns.lineplot(
    data=df_plot, 
    x='time', 
    y='count', 
    hue='ds_dose_vacina', 
    marker='o'
)

labels_df = df_plot[['time', 'epiweek', 'epiyear']].drop_duplicates().sort_values('time')
subset = labels_df.iloc[::5] 
formatted_labels = [f"{int(w)}-{int(y)}" for w, y in zip(subset['epiweek'], subset['epiyear'])]
plt.xticks(ticks=subset['time'], labels=formatted_labels, rotation=45)

plt.legend(title='Dose Type', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.ylabel('Number of Doses')
plt.xlabel('Epidemiological week')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

## Doses applied ##############################################################
counts = df_butantan['ds_dose_vacina'].value_counts()

ax = counts.plot(kind='bar', figsize=(10, 8))

ax.bar_label(ax.containers[0], fmt='%d', padding=3)

ax.set_xlabel("Dose Type")
ax.set_ylabel("Number of Doses")

plt.tight_layout()
plt.show()


# Lugar/Place #################################################################

df_butantan['co_municipio_paciente'].value_counts()
df_plot = df_butantan.groupby(['co_municipio_paciente']).size().reset_index(name = 'doses')
df_plot['co_municipio_paciente'] = df_plot['co_municipio_paciente'].astype(int).astype(str)

gdf = gpd.read_file("BR_Municipios_2025/BR_Municipios_2025.shp")
gdf["CD_MUN"] = gdf["CD_MUN"].str[:6]

gdf_plot = gdf.merge(
    df_plot,
    left_on="CD_MUN",
    right_on="co_municipio_paciente",
    how="left"
)

gdf_plot["doses"] = gdf_plot["doses"].fillna(0).astype(int)

gdf_plot = pd.DataFrame(gdf_plot)
gdf_plot = gdf_plot[['CD_MUN', 'NM_MUN', 'doses']]


## Nova Lima (MG)
df_plot[df_plot['co_municipio_paciente'] == '314480']
df_nova_lima = df_butantan[df_butantan['co_municipio_paciente'] == 314480]
df_nova_lima['ds_vacina_categoria_atendimento'].value_counts()

## Botocatu (SP)
df_plot[df_plot['co_municipio_paciente'] == '350750']
df_botucatu = df_butantan[df_butantan['co_municipio_paciente'] == 350750]
df_botucatu['ds_vacina_categoria_atendimento'].value_counts()


## Maranguape (CE) - 230770
df_plot[df_plot['co_municipio_paciente'] == '230770']
df_maranguape = df_butantan[df_butantan['co_municipio_paciente'] == 230770]
df_maranguape['ds_vacina_categoria_atendimento'].value_counts()


## Sao Paulo (SP) - 355030
df_plot[df_plot['co_municipio_paciente'] == '355030']
df_sp = df_butantan[df_butantan['co_municipio_paciente'] == 355030]
df_sp['ds_vacina_categoria_atendimento'].value_counts()

## Araguaina - 170210
df_plot[df_plot['co_municipio_paciente'] == '170210']
df_ar = df_butantan[df_butantan['co_municipio_paciente'] == 170210]
df_ar['ds_vacina_categoria_atendimento'].value_counts()


## People/Pessoa ##############################################################

### Grupos de atendimento #####################################################
df_butantan['ds_vacina_grupo_atendimento'].value_counts()
df_butantan['ds_vacina_categoria_atendimento'].value_counts()

counts = df_butantan['ds_vacina_categoria_atendimento'].value_counts()

ax = counts.plot(kind='bar', figsize=(10, 8))

ax.bar_label(ax.containers[0], fmt='%d', padding=3)

ax.set_xlabel("Dose Type")
ax.set_ylabel("Number of Doses")

plt.tight_layout()
plt.show()

### Idade dos pacientes #######################################################

min(df_butantan['nu_idade_paciente'])
max(df_butantan['nu_idade_paciente'])
np.mean(df_butantan['nu_idade_paciente'])

plt.figure(figsize=(12, 6))
plt.hist(df_butantan['nu_idade_paciente'])
plt.xlabel('Patient age')
plt.ylabel('Frequency')
plt.show()

### Tem pessoas que vacinaram duas vezes (codigo)? ############################

counts = df_butantan["co_paciente"].value_counts(dropna=False)
summary = counts.value_counts().sort_index()
print(summary)









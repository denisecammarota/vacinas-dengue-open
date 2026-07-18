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

df['dt_vacina'] = pd.to_datetime(df['dt_vacina'])

# Filtering out Butantan ######################################################

df = df[df['ds_vacina_fabricante'] != 'FUNDACAO BUTANTAN']
df = df.reset_index()


# Calculating partial coverage ################################################
# That is, only with the first vaccine dose

df_partial = df.copy()
df_partial = df_partial.sort_values(['co_paciente', 'dt_vacina'])
df_partial = df_partial.groupby(
    'co_paciente'
    ).agg(mun_primeiro = ('co_municipio_paciente', 'first'),
          idade_primeira = ('nu_idade_paciente', 'first'),
          dt_primeira = ('dt_vacina', 'first')).reset_index()

df_partial["epiyear"] = df_partial["dt_primeira"].apply(lambda d: Week.fromdate(d).year)
df_partial["epiweek"] = df_partial["dt_primeira"].apply(lambda d: Week.fromdate(d).week)
          

bins = [0, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, np.inf]

labels = [
    "0–4",
    "5–9",
    "10–14",
    "15–19",
    "20–29",
    "30–39",
    "40–49",
    "50–59",
    "60–69",
    "70–79",
    "80+"
]

df_partial["faixa_etaria"] = pd.cut(
    df_partial["idade_primeira"],
    bins=bins,
    labels=labels,
    right=False,      # left-inclusive: [0,5), [5,10), ...
    include_lowest=True
)        

df_backup = df_partial.copy()

df_partial = df_partial.groupby(
    by = ['epiyear', 'epiweek', 'mun_primeiro', 'faixa_etaria']
    ).size().reset_index(name='sem_vacinados')
          
df_partial["acc_vacinados"] = (
    df_partial.groupby(
        ['epiyear', 'epiweek', 'mun_primeiro', 'faixa_etaria']
    )["sem_vacinados"]
    .cumsum()
)

# Saving results ##############################################################
df_save = df_partial[['epiyear', 'epiweek', 'mun_primeiro', 'faixa_etaria', 'sem_vacinados', 'acc_vacinados']]
df_save.to_csv('partially_immunized.csv')

df_total = df_partial.copy()
df_total['tplot'] = df_total['epiyear'] + (df_total['epiweek']/52)

a = df_total.groupby(['epiyear', 'epiweek', 'faixa_etaria']).size()

# Barplot of faixa etaria #####################################################

df_plot = df_total.groupby('faixa_etaria')['sem_vacinados'].sum().reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(
    data=df_plot, 
    x='faixa_etaria', 
    y='sem_vacinados', 
    palette='viridis'
)

plt.title('Partially Vaccinated Individuals by Age Group - QDenga', fontsize=14)
plt.xlabel('Age Group', fontsize=12)
plt.ylabel('Total Count', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Timeseries of doses #########################################################

df_clean = df_total.groupby(['tplot', 'faixa_etaria'])['sem_vacinados'].sum().reset_index()
df_clean = df_clean.sort_values(['faixa_etaria', 'tplot'])
df_clean['acc_vacinados'] = df_clean.groupby('faixa_etaria')['sem_vacinados'].cumsum()

plt.figure(figsize=(12, 6))
sns.lineplot(data=df_clean, x='tplot', y='acc_vacinados', hue='faixa_etaria', errorbar=None, linewidth = 3)
plt.title('Partially Vaccinated Individuals by Age Group - QDenga', fontsize=16)
plt.xlabel('Epidemiological week', fontsize=16)
plt.ylabel('Total Count', fontsize=16)
plt.xticks(rotation=45)
plt.legend(fontsize = 14)
plt.tight_layout()
plt.show()

# Population ##################################################################
pop_per_age = [12674414,	14303619,	14606009,	14763017,	31959248,	32538091,	31954707,	25251034,	19379378,	11035313,	4956207]
labels = [
    "0–4",
    "5–9",
    "10–14",
    "15–19",
    "20–29",
    "30–39",
    "40–49",
    "50–59",
    "60–69",
    "70–79",
    "80+"
]

df_pop = pd.DataFrame({'faixa_etaria': labels,
                       'pop': pop_per_age})

df_clean = df_clean.merge(df_pop, on = 'faixa_etaria', how = 'left')
df_clean['acc_cov'] = 100*df_clean['acc_vacinados']/df_clean['pop']


plt.figure(figsize=(12, 6))
sns.lineplot(data=df_clean, x='tplot', y='acc_cov', hue='faixa_etaria', errorbar=None, linewidth = 3)
plt.title('Partial Coverage by Age Group - QDenga', fontsize=16)
plt.xlabel('Epidemiological week', fontsize=16)
plt.ylabel('Coverage', fontsize=16)
plt.xticks(rotation=45)
plt.legend(fontsize = 14)
plt.tight_layout()
plt.show()

          
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

# Doses and full coverage of the Qdenga vaccine ###############################
# This is, we consider fully immunized = two doses ############################

# Counting doses: first doses of duplicated people ############################

df_dup = df.copy()
df_dup = df_dup.groupby(
    by = 'co_paciente'
    ).agg(n_paciente = ('co_paciente', 'count')).reset_index()
df_dup = df_dup[df_dup['n_paciente'] >= 2]

df_vac_1 = df.copy()
df_vac_1 = df_vac_1[df_vac_1['co_paciente'].isin(np.unique(df_dup['co_paciente']))]
df_vac_1['dt_vacina'] = pd.to_datetime(df_vac_1['dt_vacina'])
df_vac_1 = df_vac_1.sort_values(['co_paciente','dt_vacina'])

df_doses_1 = (
    df_vac_1
    .groupby('co_paciente')
    .agg(
        dt_primeira=('dt_vacina', 'first'),
        dt_ultima=('dt_vacina', 'last'),
        idade_primeira = ('nu_idade_paciente', 'first'),
        idade_ultima = ('nu_idade_paciente', 'last'),
        mun_primeira = ('co_municipio_paciente', 'first'),
        mun_ultimo = ('co_municipio_paciente', 'last')
    )
    .reset_index()
)

df_doses_1['int_vacinas'] = (
    df_doses_1['dt_ultima'] - df_doses_1['dt_primeira']
).dt.days

df_doses_1 = df_doses_1[df_doses_1['int_vacinas'] >= 90]
df_doses_1 = df_doses_1[['dt_ultima','idade_ultima', 'mun_ultimo']]

# Counting doses: only second doses with no duplicated people #################

df_doses_2 = df.copy()
df_doses_2 = df_doses_2[~df_doses_2['co_paciente'].isin(np.unique(df_dup['co_paciente']))]
df_doses_2 = df_doses_2[df_doses_2['ds_dose_vacina'] == '2ª Dose']
df_doses_2 = df_doses_2.groupby(
    'co_paciente'
    ).agg(
        dt_ultima = ('dt_vacina', 'last'),
        idade_ultima = ('nu_idade_paciente', 'last'),
        mun_ultimo = ('co_municipio_paciente', 'last')
    ).reset_index()# Counting doses: only second doses with no duplicated people #################

df_doses_2 = df.copy()
df_doses_2 = df_doses_2[~df_doses_2['co_paciente'].isin(np.unique(df_dup['co_paciente']))]
df_doses_2 = df_doses_2[df_doses_2['ds_dose_vacina'] == '2ª Dose']
df_doses_2 = df_doses_2.groupby(
    'co_paciente'
    ).agg(
        dt_ultima = ('dt_vacina', 'last'),
        idade_ultima = ('nu_idade_paciente', 'last'),
        mun_ultimo = ('co_municipio_paciente', 'last')
    ).reset_index()
df_doses_2 = df_doses_2.drop(columns = ['co_paciente'])
        
# Total of all doses ##########################################################

df_total = pd.concat([df_doses_1, df_doses_2], axis = 0, ignore_index=True)

df_total["epiyear"] = df_total["dt_ultima"].apply(lambda d: Week.fromdate(d).year)
df_total["epiweek"] = df_total["dt_ultima"].apply(lambda d: Week.fromdate(d).week)

df_total = df_total.groupby(
    by = ['epiyear', 'epiweek', 'mun_ultimo', 'idade_ultima']
    ).size().reset_index(name='sem_vacinados')

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

df_total["faixa_etaria"] = pd.cut(
    df_total["idade_ultima"],
    bins=bins,
    labels=labels,
    right=False,      # left-inclusive: [0,5), [5,10), ...
    include_lowest=True
)

df_total = df_total.groupby(
    by = ['epiyear', 'epiweek', 'mun_ultimo', 'faixa_etaria']
    ).agg(
        sem_vacinados = ('sem_vacinados', 'sum')
        ).reset_index()
        
df_total["acc_vacinados"] = (
    df_total.groupby(
        ['epiyear', 'epiweek', 'mun_ultimo', 'faixa_etaria']
    )["sem_vacinados"]
    .cumsum()
)
        
df_total = df_total.sort_values(['epiyear', 'epiweek', 'mun_ultimo', 'faixa_etaria'])

df_total['tplot'] = df_total['epiyear'] + (df_total['epiweek']/52)

# Saving results ##############################################################
df_save = df_total[['epiyear', 'epiweek', 'mun_ultimo', 'faixa_etaria', 'sem_vacinados', 'acc_vacinados']]
df_save.to_csv('totally_immunized.csv')

# Barplot of faixa etaria #####################################################

df_plot = df_total.groupby('faixa_etaria')['sem_vacinados'].sum().reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(
    data=df_plot, 
    x='faixa_etaria', 
    y='sem_vacinados', 
    palette='viridis'
)

plt.title('Totally Vaccinated Individuals by Age Group - QDenga', fontsize=14)
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
plt.title('Totally Vaccinated Individuals by Age Group - QDenga', fontsize=16)
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
plt.title('Coverage by Age Group - QDenga', fontsize=16)
plt.xlabel('Epidemiological week', fontsize=16)
plt.ylabel('Coverage', fontsize=16)
plt.xticks(rotation=45)
plt.legend(fontsize = 14)
plt.tight_layout()
plt.show()




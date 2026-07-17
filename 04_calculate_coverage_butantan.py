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

# Filtering Butantan exclusively ##############################################

df = df[df['ds_vacina_fabricante'] == 'FUNDACAO BUTANTAN']

# Filtering target municipalities only ########################################
df = df[df['co_municipio_paciente'].isin([314480, 350750, 230770, 170210])]

# Filtering the age range 15-59 ###############################################
df = df[df['nu_idade_paciente'] >= 15]
df = df[df['nu_idade_paciente'] <= 59]

# Calculating epiyear/epiweek #################################################
df["dt_vacina"] = pd.to_datetime(df["dt_vacina"])
df['dt_vacina']

df["epiyear"] = df["dt_vacina"].apply(lambda d: Week.fromdate(d).year)
df["epiweek"] = df["dt_vacina"].apply(lambda d: Week.fromdate(d).week)

# Removing co_paciente duplicates #############################################
df = df.sort_values('dt_vacina')
df = df.drop_duplicates(subset = 'co_paciente', keep = 'last')


# Grouping by: epiyear, epiweek, co_municipio_paciente, nu_idade_paciente #####
df_sum = df.groupby(
    by = ['epiyear', 'epiweek', 'co_municipio_paciente', 'nu_idade_paciente']
    ).agg(n = ('co_paciente', 'count')).reset_index()

df_sum = df_sum.rename(columns = {'n': 'sem_vacinados'})

# Filtering from 2026 onwards #################################################
df_sum = df_sum[df_sum['epiyear'] >= 2026]

# Padding to get a better sense of things #####################################

all_combinations = pd.MultiIndex.from_product(
    [
        df_sum["epiyear"].unique(),
        df_sum["epiweek"].unique(),
        df_sum["co_municipio_paciente"].unique(),
        df_sum["nu_idade_paciente"].unique(),
    ],
    names=[
        "epiyear",
        "epiweek",
        "co_municipio_paciente",
        "nu_idade_paciente",
    ],
).to_frame(index=False)

df_sum = (
    all_combinations
    .merge(
        df_sum,
        on=[
            "epiyear",
            "epiweek",
            "co_municipio_paciente",
            "nu_idade_paciente",
        ],
        how="left",
    )
)

df_sum["sem_vacinados"] = df_sum["sem_vacinados"].fillna(0).astype(int)

df_sum = df_sum.sort_values(
    ["epiyear", "co_municipio_paciente", "nu_idade_paciente", "epiweek"]
)


df_sum["acc_vacinados"] = (
    df_sum.groupby(
        ["epiyear", "co_municipio_paciente", "nu_idade_paciente"]
    )["sem_vacinados"]
    .cumsum()
)


# Calculating doses and coverage ##############################################

mun_list = [314480, 350750, 230770, 170210]
name_list = ['Nova Lima', 'Botucatu', 'Maranguape', 'Araguaina']
pop_list = [77871, 95753,71338,120599] # 15-59 years old

df_doses = df_sum.groupby(
    by = ['epiyear', 'epiweek', 'co_municipio_paciente']
    ).agg(sem_vacinados = ('sem_vacinados', 'sum'),
          acc_vacinados = ('acc_vacinados', 'sum')).reset_index()

df_pop = pd.DataFrame({'mun': mun_list,
                      'name': name_list,
                      'pop': pop_list})
    
df_doses = df_doses.merge(df_pop, left_on = 'co_municipio_paciente',
                    right_on = 'mun', how = 'left')

plt.figure(figsize=(12, 6))

sns.lineplot(
    data=df_doses,
    x="epiweek",
    y="acc_vacinados",
    hue="name",
    palette = 'tab10',
    linewidth = 3
)

plt.xlabel("Epidemiological week", fontsize = 16)
plt.ylabel("Cumulative vaccinated", fontsize = 16)
plt.legend(fontsize = 14, loc = 'upper right')
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.tight_layout()
plt.savefig('butantan_cum_doses.pdf')
plt.show()


df_doses['acc_cov'] = 100*df_doses['acc_vacinados']/df_doses['pop']

plt.figure(figsize=(12, 6))

sns.lineplot(
    data=df_doses,
    x="epiweek",
    y="acc_cov",
    hue="name",
    palette = 'tab10',
    linewidth = 3
)

plt.xlabel("Epidemiological week", fontsize = 16)
plt.ylabel("Cumulative coverage", fontsize = 16)
plt.legend(fontsize = 14, loc = 'upper right')
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.tight_layout()
plt.savefig('butantan_cum_cov.pdf')
plt.show()









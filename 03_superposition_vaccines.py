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

# Did some people vaccine with both vaccines? #################################

df['butantan'] = (df['ds_vacina_fabricante'] == 'FUNDACAO BUTANTAN')
df['outras'] = (df['ds_vacina_fabricante'] != 'FUNDACAO BUTANTAN')

df_sup = df.groupby(['co_paciente']).agg(
    doses_but=("butantan", "sum"),
    doses_outras=("outras", "sum")
).reset_index()

filt_1 = (df_sup['doses_but'] >= 1)
filt_2 = (df_sup['doses_outras'] >= 1)

df_sup = df_sup[filt_1 & filt_2]

# Where are these people from? ################################################

df_double = df[df["co_paciente"].isin(df_sup["co_paciente"])]
df_double['sg_uf_paciente'].value_counts()


## Are they in our priority municipalities? ###################################
## I mean, those who were target for Butantan vaccination

mun_changes = (
    df_double.groupby("co_paciente")["co_municipio_paciente"]
      .nunique()
)

mun_changes = mun_changes[mun_changes > 1] # only 697 change municipality for vaccination
                                           # i will consider the last one due to history

df_double = df_double.sort_values('dt_vacina')
df_double_mun = df_double.groupby(['co_paciente']).agg(
    co_municipio_paciente = ('co_municipio_paciente', 'last')).reset_index()
# 60762 registries of doses involving duplicate patients
# in total, 29467 patients vaccinated with different vaccines 

### Nova Lima #################################################################
df_nova_lima = df_double_mun[df_double_mun['co_municipio_paciente'] == 314480]
# 75 pacientes

### Botucatu ##################################################################
df_botucatu = df_double_mun[df_double_mun['co_municipio_paciente'] == 350750]
# 88 pacientes

### Maranguape ################################################################
df_maranguape = df_double_mun[df_double_mun['co_municipio_paciente'] == 230770]
# 25 pacientes

### Araguaina #################################################################
df_araguaina = df_double_mun[df_double_mun['co_municipio_paciente'] == 170210]
# 58 pacientes 

# How many doses of not butantan in butantan municipalities? ##################
df_sup_vaccines = df[df['co_municipio_paciente'].isin([314480, 350750, 230770, 170210])]
df_sup_vaccines = df_sup_vaccines.groupby([
    'co_municipio_paciente']
    ).agg(doses_butantan = ('butantan', 'sum'),
          doses_outras = ('outras', 'sum'))
          
# In which age groups #########################################################'

mun_list = [314480, 350750, 230770, 170210]
name_list = ['Nova Lima', 'Botucatu', 'Maranguape', 'Araguaina']

fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
axes = axes.flatten()  # Flatten the 2D array to easily iterate through 4 axes

for i, mun in enumerate(mun_list):
    name = name_list[i]
    # Filter your data
    df_aux = df[df['co_municipio_paciente'] == mun].copy()
    
    # Map the labels
    df_aux["Manufacturer"] = df_aux["butantan"].map({
        True: "Butantan",
        False: "Other"
    })
    
    # Plot on the specific axis (axes[i])
    sns.histplot(
        data=df_aux,
        x="nu_idade_paciente",
        hue="Manufacturer",
        bins=20,
        multiple="dodge",
        palette={"Butantan": "tab:blue", "Other": "tab:orange"},
        ax=axes[i], # Assign to this subplot
        shrink=0.8  # Adds a small gap between side-by-side bars
    )
    
    # Labels and Titles in English
    axes[i].set_title(f"{name}")
    axes[i].set_xlabel("Patient Age")
    axes[i].set_ylabel("Doses")

plt.tight_layout()
plt.savefig('hist_butantan_doses.pdf')
plt.show()
















from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import re

#years_list = [2024, 2025, 2026]
#years_list = [2026] READY
#years_list = [2024]
years_list = [2025]

col_names_2024 = [
    "co_documento", # 0
    "co_paciente", # 1
    "tp_sexo_paciente", # 2
    "co_raca_cor_paciente", # 3
    "no_raca_cor_paciente", # 4
    "co_municipio_paciente", # 5
    "co_pais_paciente", # 6
    "no_municipio_paciente", # 7
    "no_pais_paciente", # 8
    "sg_uf_paciente", # 9
    "nu_cep_paciente", # 10
    "ds_nacionalidade_paciente", # 11
    #"no_etnia_indigena_paciente",
    #"co_etnia_indigena_paciente",
    "co_cnes_estabelecimento", # 12
    "no_razao_social_estabelecimento", # 13
    "no_fantasia_estalecimento", # 14
    "co_municipio_estabelecimento", # 15
    "no_municipio_estabelecimento", # 16
    "sg_uf_estabelecimento", # 17
    # "co_troca_documento",
    "co_vacina", # 18
    "sg_vacina", # 19
    "dt_vacina", # 20
    "co_dose_vacina", # 21
    "ds_dose_vacina", # 22
    "co_local_aplicacao", # 23
    "ds_local_aplicacao", # 24
    "co_via_administracao", # 25
    "ds_via_administracao", # 26
    "co_lote_vacina", # 27
    "ds_vacina_fabricante", # 28
    "dt_entrada_rnds", # 29
    "co_sistema_origem",# 30
    "ds_sistema_origem", # 31
    "st_documento", # 32
    "co_estrategia_vacinacao", # 33
    "ds_estrategia_vacinacao", # 34
    #"co_origem_registro",
    #"ds_origem_registro",
    "co_vacina_grupo_atendimento", # 35
    "ds_vacina_grupo_atendimento", # 36
    "co_vacina_categoria_atendimento", # 37
    "ds_vacina_categoria_atendimento", # 38
    "co_vacina_fabricante", # 39 
    "ds_vacina", # 40
    #"ds_condicao_maternal", 
    "co_tipo_estabelecimento", # 41
    "ds_tipo_estabelecimento", # 42
    "co_natureza_estabelecimento", # 43
    "ds_natureza_estabelecimento", # 44
    "nu_idade_paciente", # 45
    #"co_condicao_maternal", 
    "no_uf_paciente", # 46
    "no_uf_estabelecimento", # 47
    #"dt_deletado_rnds" # 48
]

col_names_2025 = [
    "co_documento",
    "co_paciente",
    "tp_sexo_paciente",
    "co_raca_cor_paciente",
    "no_raca_cor_paciente",
    "co_municipio_paciente",
    "co_pais_paciente",
    "no_municipio_paciente",
    "no_pais_paciente",
    "sg_uf_paciente",
    "nu_cep_paciente",
    "ds_nacionalidade_paciente",
    "no_etnia_indigena_paciente",
    "co_etnia_indigena_paciente",
    "co_cnes_estabelecimento",
    "no_razao_social_estabelecimento",
    "no_fantasia_estalecimento",
    "co_municipio_estabelecimento",
    "no_municipio_estabelecimento",
    "sg_uf_estabelecimento",
    "co_troca_documento",
    "co_vacina",
    "sg_vacina",
    "dt_vacina",
    "co_dose_vacina",
    "ds_dose_vacina",
    "co_local_aplicacao",
    "ds_local_aplicacao",
    "co_via_administracao",
    "ds_via_administracao",
    "co_lote_vacina",
    "ds_vacina_fabricante",
    "dt_entrada_rnds",
    "co_sistema_origem",
    "ds_sistema_origem",
    "st_documento",
    "co_estrategia_vacinacao",
    "ds_estrategia_vacinacao",
    "co_origem_registro",
    "ds_origem_registro",
    "co_vacina_grupo_atendimento",
    "ds_vacina_grupo_atendimento",
    "co_vacina_categoria_atendimento",
    "ds_vacina_categoria_atendimento",
    "co_vacina_fabricante",
    "ds_vacina",
    "ds_condicao_maternal",
    "co_tipo_estabelecimento",
    "ds_tipo_estabelecimento",
    "co_natureza_estabelecimento",
    "ds_natureza_estabelecimento",
    "nu_idade_paciente",
    "co_condicao_maternal",
    "no_uf_paciente",
    "no_uf_estabelecimento",
    "dt_deletado_rnds"
]


for year_list in years_list:
    
    print('Processing year '+str(year_list))
    
    input_folder = Path(r"D:\sipni-"+str(year_list))
    output_folder = Path("dengue_all")
    output_folder.mkdir(exist_ok=True)
    
    files = sorted(input_folder.glob("vacinacao_*_*_csv.zip"))
    
    cols_to_sel = ['co_paciente', 
                    'nu_idade_paciente',
                    'co_municipio_paciente', 'sg_uf_paciente', 
                    'co_vacina', 'ds_vacina',
                    'co_vacina_fabricante', 'ds_vacina_fabricante', 
                    'ds_dose_vacina',
                    'ds_estrategia_vacinacao', 
                    'ds_vacina_grupo_atendimento', 'ds_vacina_categoria_atendimento',
                    'dt_vacina']
    
    schema = pa.schema([
        ("co_paciente", pa.string()),
        ("nu_idade_paciente", pa.int64()),
        ("co_municipio_paciente", pa.int64()),
        ("sg_uf_paciente", pa.string()),
        ("co_vacina", pa.int64()),
        ("ds_vacina", pa.string()),
        ("co_vacina_fabricante", pa.int64()),
        ("ds_vacina_fabricante", pa.string()),
        ("ds_dose_vacina", pa.string()),
        ("ds_estrategia_vacinacao", pa.string()),
        ("ds_vacina_grupo_atendimento", pa.string()),
        ("ds_vacina_categoria_atendimento", pa.string()),
        ("dt_vacina", pa.string()),
    ])
    
    for file in files:
        
        m = re.match(r"vacinacao_(.+)_(\d{4})_csv\.zip", file.name)
    
        if m is None:
            continue
    
        month, year = m.groups()
    
        outfile = output_folder / f"{year}_{month}.parquet"
        
        print(f"Processing {file.name}...")
        
        writer = None
        
        if(year_list == 2024):

            chunks = pd.read_csv(
                file,
                compression="zip",
                chunksize=100000,
                encoding="latin1",
                sep=";",
                header = None, 
                names = col_names_2024,
                usecols = cols_to_sel
            )
            
        elif (year_list == 2025):
            
            chunks = pd.read_csv(
                file,
                compression="zip",
                chunksize=100000,
                encoding="latin1",
                sep=";",
                header = None, 
                names = col_names_2025,
                usecols = cols_to_sel
            ) 
            
        else:
            
            chunks = pd.read_csv(
                file,
                compression="zip",
                chunksize=100000,
                encoding="latin1",
                sep=";",
                usecols = cols_to_sel,
            )
    
        for chunk in chunks:
    
            chunk = chunk[chunk["co_vacina"].isin([104, 82])]
    
            if chunk.empty:
                continue
    
            table = pa.Table.from_pandas(
                    chunk,
                    schema=schema,
                    preserve_index=False
                )
    
            if writer is None:
                writer = pq.ParquetWriter(outfile, table.schema)
    
            writer.write_table(table)
    
        if writer is not None:
            writer.close()
    
    print("Done with year"+str(year_list)+'!')

    
    
    
    

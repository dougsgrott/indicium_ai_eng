# sars_lens/internal/data_retrieval/adapters/csv/datasus_loader.py
import pandas as pd
from ..ports.clinical_data import ClinicalDataPort

class DatasusCsvAdapter(ClinicalDataPort):
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def get_raw_srag_data(self) -> pd.DataFrame:
        # 1. Load Data
        df = pd.read_csv(self.csv_path, sep=';', encoding='latin1')
        
        # 2. Select pertinent columns (as requested in prompt)
        cols = ['DT_NOTIFIC', 'EVOLUCAO', 'DT_INTERNA', 'UTI', 'VACINA']
        df = df[cols]
        
        # 3. Clean Data (Handle missing values)
        df['UTI'] = df['UTI'].fillna(9) # Assuming 9 is 'Ignored'
        return df
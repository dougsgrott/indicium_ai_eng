# src/workflows/agents/metrics_analyst/config.py

# Column mappings for Open DATASUS SRAG 2024/2025
COL_DATE = 'DT_NOTIFIC'
COL_EVOLUTION = 'EVOLUCAO' # 1=Cure, 2=Death, 3=Death other causes
COL_ICU = 'UTI'            # 1=Yes, 2=No, 9=Ignored
COL_VACCINE = 'VACINA'     # 1=Yes, 2=No, 9=Ignored

# Value Codes
VAL_DEATH = 2
VAL_ICU_YES = 1
VAL_VAC_YES = 1
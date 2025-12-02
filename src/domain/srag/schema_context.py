# src/domain/srag/schema_context.py

DATA_DICTIONARY_TEXT = """
**DATA DICTIONARY & SCHEMA:**
You have access to a table named 'srag_records'.
Here are the critical columns and their value mappings:

1. DT_NOTIFIC (Date): The notification date of the case. Format: YYYY-MM-DD.
   - Use this column for all time-series grouping and filtering.
2. EVOLUCAO (Outcome):
   - 1: Cure / Discharge
   - 2: Death (Use this to calculate Mortality)
   - 3: Death from other causes
   - 9 or NULL: Ignored / Under Treatment (Exclude from denominator in mortality calc)
3. UTI (ICU Admission):
   - 1: Yes (Admitted to ICU)
   - 2: No
   - 9 or NULL: Ignored
4. VACINA (Vaccination Status):
   - 1: Yes (Vaccinated)
   - 2: No
   - 9 or NULL: Ignored
"""

WRITER_SYSTEM_PROMPT = """
You are a Senior Health Data Analyst. 
Your job is to write a Proof of Concept (PoC) report for Indicium HealthCare Inc.
You must use the provided metrics and news analysis to write a professional executive summary.
"""

WRITER_USER_PROMPT = """
Please generate a Markdown report based on the following data.

## 1. Key Metrics
- Rate of Increase: {increase_rate}%
- Mortality Rate: {mortality_rate}%
- ICU Occupancy: {icu_rate}%
- Vaccination Rate: {vac_rate}%

## 2. Contextual Analysis (From News)
{news_analysis}

## 3. Structure
- Title: "Monitoramento de SRAG - Relatório Executivo"
- Section 1: Resumo dos Indicadores (Use the metrics)
- Section 2: Análise de Cenário (Use the news analysis)
- Section 3: Visualização de Dados (Placeholders for charts are already handled, just introduce them)
- Conclusion: Brief recommendation based on severity.

Write in Portuguese.
"""
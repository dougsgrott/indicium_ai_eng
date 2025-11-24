# Formação em AI Engineering - Indicium

Work in Progress

## Contexto

A Indicium HealthCare Inc. está interessada em criar uma solução baseada em dados que possa ajudar profissionais da área da saúde a ter um entendimento em tempo real sobre a severidade e o avanço de surtos de doenças. Para tanto, irá realizar uma Prova de Conceito (Proof of Concept - PoC) para avaliar a viabilidade de tal solução e você foi contratado para ser o analista responsável por desenvolver a solução.

 
Para a PoC escolheu-se criar uma solução que forneça métricas através de um relatório gerado por um agente que consiga consultar o banco de dados e trazer os valores das métricas, além disso usando outras ferramentas, este agente deve consultar notícias sobre Síndrome Respiratória Aguda Grave (SRAG) em tempo real para embasar as métricas apresentadas e fornecer explicações/comentários sobre o cenário relatado. Será utilizado o conjunto real sobre internações por SRAG disponível no Open DATASUS.

As métricas que devem constar no relatório são:
- taxa de aumento de casos
- taxa de mortalidade
- taxa de ocupação de UTI
- taxa de vacinação da população

Além das métricas citadas o relatório deve possuir dois gráficos, um representando o número diário de casos dos últimos 30 dias e outro mostrando o número mensal de casos dos últimos 12 meses.

## Descrição dos dados

Os dados, o dicionário de dados e demais informações podem ser obtidos no site do Open DATASUS. Os dados estão num arquivo no formato CSV que contém aproximadamente 100 colunas e 165.000 linhas. Por se tratarem de dados reais temos muitos problemas de preenchimento incorreto e dados ausentes. Por conta disso, você deve selecionar as colunas que achar pertinentes e aplicar os tratamentos que achar necessários.

## Entrega

Link para um repositório do GitHub contendo a solução desenvolvida. O repositório deve estar público e todas as explicações e documentações do projeto devem ser colocadas no README do repositório e/ou relatórios pertencentes ao repositório.

 
O repositório também deve incluir um PDF com o diagrama conceitual que ilustre a arquitetura da solução, mostrando o Agente Principal (Orquestrador), as Ferramentas (Tools) que ele utilizará, as interações com o LLM, banco de dados e fontes de notícias.

## Avaliação 

A nota atribuída considerando:
Escolha da arquitetura
Governança e Transparência (mecanismos de auditoria e registro de decisões dos agentes)
Guardrails
Tratamento de Dados Sensíveis
Clean Code














### 1\. Data Engineering Strategy

The Open DATASUS dataset (likely the **SRAG**—Severe Acute Respiratory Syndrome—database) is notorious for its complexity. You cannot simply feed raw CSV data to an LLM; it is too large and contains PII (Personally Identifiable Information).

#### **A. Preprocessing & Cleaning (The ETL Layer)**

Before the agent touches the data, you must build a Python preprocessing pipeline (using Pandas or Polars).

  * **Column Selection:** Map the 100+ columns to only what is needed.
      * *Dates:* `DT_SIN_PRI` (Date of first symptoms), `DT_NOTIFIC` (Notification date).
      * *Demographics (for context only):* `NU_IDADE_N` (Age).
      * *Clinical:* `UTI` (ICU usage), `EVOLUCAO` (Outcome: Discharge/Death), `VACINA` (Vaccination status).
  * **Handling Missing Data:**
      * **Categorical:** Map numeric codes (e.g., `1=Yes`, `2=No`, `9=Ignored`) to human-readable strings. Treat `9` or `NaN` as "Unknown" to avoid skewing stats.
      * **Dates:** Drop rows where critical timestamps (like notification date) are missing, as they break time-series analysis.
  * **The Vaccination Caveat:** The DATASUS SRAG dataset tracks *hospitalized* patients. Calculating a "population vaccination rate" solely from this file is statistically impossible (you only have the sick population).
      * *Strategic Move:* You must incorporate an external static variable (Total Population) or acknowledge that the metric represents "Vaccination rate among hospitalized cases." For this PoC, I recommend creating a mock "Total Population" table or fetching it via the agent to calculate the rate correctly:
        $$\text{Vaccination Rate} = \frac{\text{Total Vaccinated}}{\text{Total Population}} \times 100$$

#### **B. Storage for the Agent**

Do not keep the data in CSV for the live agent. Load the cleaned data into a lightweight SQL engine like **DuckDB** or **SQLite**.

  * **Why?** It allows the Agent to write SQL queries (deterministic, fast, verifiable) rather than trying to interpret 165k rows of text.

-----

### 2\. Proposed Architecture

This architecture utilizes a **ReAct (Reason + Act)** pattern or a **LangGraph** state machine.

#### **The Components**

1.  **User Interface:** A Streamlit or Chainlit dashboard to request the report.
2.  **The Orchestrator (Main Agent):** A LangChain/LangGraph agent. It holds the "State" (the current plan).
3.  **Tool A: SQL Database (DuckDB):**
      * *Function:* Calculates the metrics.
      * *Input:* SQL Query generated by the LLM.
      * *Output:* Aggregated numbers (Safety: The LLM never sees individual patient names).
4.  **Tool B: News Search (Tavily/Serper/DuckDuckGo):**
      * *Function:* Searches for "SARS outbreak current news," "ICU occupancy trends."
      * *Input:* Search query strings.
      * *Output:* Text summaries of recent articles.
5.  **Tool C: Python REPL (Visualization):**
      * *Function:* Generates the charts.
      * *Input:* Python code (Matplotlib/Plotly) using the aggregated data from Tool A.
      * *Output:* Image files or base64 strings.

-----

### 3\. Evaluation Checklist & Implementation Guide

Here is how to specifically address the grading criteria:

#### **A. Governance & Transparency**

  * **Audit Trails:** You must log the "thought process" of the agent.
      * *Suggestion:* Use **LangSmith** (if allowed) or a local logger that saves a JSON file for every run. This JSON should contain: `Prompt`, `Tool Used`, `Tool Output`, and `Final Answer`.
  * **Explanation:** The final report should not just show a number (e.g., "Mortality 5%"); it should show the SQL query used to derive it. This proves the number wasn't hallucinated.

#### **B. Guardrails**

  * **Topic Control:** Ensure the agent refuses to answer questions about non-health topics (e.g., "Who won the football game?").
      * *Implementation:* System prompt instruction: *"You are a specialized healthcare analyst. If the user asks about anything other than SARS or health metrics, politely decline."*
  * **Hallucination Check:** Add a validation step. If the Agent queries the News Tool, the URL must be cited. If the Agent queries the DB, the code must execute without syntax errors.

#### **C. Handling Sensitive Data (Privacy)**

This is the most critical part for healthcare.

  * **Technique:** **Local Execution & Aggregation.**
      * The LLM (e.g., GPT-4 or generic model) should **never** see the row-level data.
      * *Workflow:* The LLM writes SQL $\rightarrow$ The SQL executes locally on the DuckDB $\rightarrow$ Only the *result* (e.g., "500 cases") is sent back to the LLM.
      * *Anonymization:* Ensure columns like Patient Name or specific Address are dropped during the initial ETL phase.

#### **D. Clean Code**

  * **Structure:**
    ```text
    /src
      /agents       # Logic for the Orchestrator
      /tools        # Wrapper classes for SQL, Search, Plotting
      /data         # ETL scripts
    /notebooks      # EDA (Exploratory Data Analysis)
    /tests          # Unit tests for the metrics calculations
    README.md
    architecture.pdf
    requirements.txt
    ```
  * **Type Hinting:** Use Python type hints (`def get_metric(data: pd.DataFrame) -> float:`) extensively.
  * **Configuration:** Use `.env` files for API keys (OpenAI, Tavily, etc.). **Never commit keys to GitHub.**

-----

### 4\. Calculating the Metrics (Technical Details)

To assist your implementation, here are the logic definitions you should code into your Agent's instructions or SQL logic:

1.  **Rate of Increase (Cases):**
    $$\text{Increase Rate} = \frac{\text{Cases}_{\text{Current Period}} - \text{Cases}_{\text{Previous Period}}}{\text{Cases}_{\text{Previous Period}}}$$

      * *Tip:* Define "Current" as the last 7 days vs the 7 days prior.

2.  **Mortality Rate:**
    $$\text{Mortality Rate} = \frac{\text{Total Deaths (EVOLUCAO = Death)}}{\text{Total Closed Cases}}$$

      * *Tip:* Filter out cases where `EVOLUCAO` is "Under treatment" or "Ignored".

3.  **ICU Occupancy Rate:**

      * *Context:* Since you don't have total ICU beds (capacity) in the SRAG file, you must calculate **"ICU Utilization among Severe Cases."**
        $$\text{ICU Rate} = \frac{\text{Cases admitted to ICU (UTI=1)}}{\text{Total Hospitalized Cases}}$$

4.  **Graphs:**

      * **Daily Cases (30 days):** `SELECT DT_NOTIFIC, COUNT(*) FROM srag WHERE DT_NOTIFIC >= DATE('now', '-30 days') GROUP BY DT_NOTIFIC`
      * **Monthly Cases (12 months):** Group by `strftime('%Y-%m', DT_NOTIFIC)`.

-----

### 5\. Immediate Next Step

Would you like me to generate the **ETL Python script** to clean the DATASUS columns and prepare the `duckdb` database, or would you prefer I write the **System Prompt** for the Orchestrator Agent?
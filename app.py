
import streamlit as st
import openai
import psycopg2
import pandas as pd
import os

st.set_page_config(page_title="QuickBI Chat", layout="wide")

st.title("💬 QuickBI Financial Assistant")

# Inputs del usuario
question = st.text_input("Haz una pregunta sobre los datos financieros:", "")

# Cargar la API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Definir la función que llama a OpenAI para generar SQL
def generate_sql_from_question(question, table_schema):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        functions=[
            {
                "name": "run_sql_query",
                "description": "Genera una consulta SQL basada en una pregunta financiera.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "La consulta SQL a ejecutar en PostgreSQL"
                        }
                    },
                    "required": ["query"]
                }
            }
        ],
        function_call={"name": "run_sql_query"},
        messages=[
            {"role": "system", "content": "Eres un asistente financiero que responde preguntas generando SQL para una base de datos PostgreSQL. Usa las tablas pl_ledger y budget."},
            {"role": "user", "content": f"La estructura de las tablas es:
{table_schema}"},
            {"role": "user", "content": question}
        ]
    )
    return response["choices"][0]["message"]["function_call"]["arguments"]

# Definir función para ejecutar SQL
def execute_sql_query(sql_query):
    conn = psycopg2.connect(
        host="quickbipostgres.postgres.database.azure.com",
        port=5432,
        database="company_vicio",
        user="ecabanas",
        password="gkOMy47d7EJ5WKKXmiq"
    )
    df = pd.read_sql_query(sql_query, conn)
    conn.close()
    return df

# Mostrar resultados
if question:
    with st.spinner("Generando respuesta..."):
        schema = '''
        Tabla pl_ledger:
        - acctnumber (texto)
        - end_of_month (fecha)
        - location (entero)
        - total_balance (decimal)
        - subsidiary (entero)
        - isrevenues (0 o 1)
        - iscogs (0 o 1)

        Tabla budget:
        - end_of_month (fecha)
        - location (entero)
        - total_budget (decimal)
        - isrevenues (0 o 1)
        - iscogs (0 o 1)
        '''
        try:
            result = generate_sql_from_question(question, schema)
            query = eval(result)["query"]
            if not query.lower().strip().startswith("select"):
                st.error("❌ Solo se permiten consultas SELECT.")
            else:
                df = execute_sql_query(query)
                st.success("✅ Consulta ejecutada correctamente.")
                st.dataframe(df)
        except Exception as e:
            st.error(f"⚠️ Error procesando tu pregunta: {str(e)}")

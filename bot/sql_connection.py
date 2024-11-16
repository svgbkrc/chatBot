import pandas as pd
from sqlalchemy import create_engine

# Connection string
connection_string = 'mssql+pyodbc://localhost/Dbo_eTicaret?driver=ODBC+Driver+17+for+SQL+Server'

# Create engine
engine = create_engine(connection_string)

# SQL query
query = 'SELECT * FROM Products'  # Modify as per your query

# Execute query and get result in a DataFrame
df = pd.read_sql(query, engine)

# Display results
print(df)

from imports import *


class DatabaseConfig:
    def __init__(self, server, database_name):
        self.server = server
        self.database_name = database_name

    def create_engine_connection(self):
        try:
            params = urllib.parse.quote_plus(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database_name};Trusted_Connection=yes;"
            )
            engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
            return engine
        except Exception as e:
            messagebox.showerror("Database Connection Error", f"Could not connect to the database:\n{e}")
            return None

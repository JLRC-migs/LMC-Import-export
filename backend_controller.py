from db_config import DatabaseConfig
from imports import *

class BackendController:
    def __init__(self):
        self.db_config = None
        self.engine = None
    def connect_to_database(self):
        if not self.engine:
            server = 'DESKTOP-EQR4UHR\\SQLEXPRESS01'
            
            while True:  # Loop until a valid database name is entered
                database_name = simpledialog.askstring("Database Selection", "Enter the database name you want to access:")

                if not database_name:
                    messagebox.showwarning("Database Name Missing", "No database name provided.")
                    return None
                
                # Initialize temporary DatabaseConfig to check if database exists
                temp_db_config = DatabaseConfig(server, 'master')
                temp_engine = temp_db_config.create_engine_connection()
                
                if temp_engine:
                    with temp_engine.connect() as conn:
                        # Query system databases to see if user-provided database exists
                        db_exists = conn.execute(
                            text(f"SELECT name FROM sys.databases WHERE name = :name"), {'name': database_name}
                        ).fetchone()

                    temp_engine.dispose()

                    if db_exists:
                        # If the database exists, initialize the actual DatabaseConfig and engine
                        self.db_config = DatabaseConfig(server, database_name)
                        self.engine = self.db_config.create_engine_connection()
                        return self.engine
                    else:
                        messagebox.showwarning("Invalid Database", f"No database named '{database_name}' found. Please try again.")
                else:
                    messagebox.showerror("Connection Error", "Could not connect to the server.")
                    return None
      
    def check_table_exists(self, engine, table_name):
        inspector = inspect(engine)
        return inspector.has_table(table_name)
    
    def import_excel_to_sql(self):
        engine = self.connect_to_database()
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        table_name = simpledialog.askstring("Table Name", "Enter the table name:")
        if not table_name:
            messagebox.showwarning("Table Name", "No table name provided.")
            return

        try:
            df = pd.read_excel(file_path)
            engine = self.db_config.create_engine_connection()
            if not engine:
                return

            table_exists = self.check_table_exists(engine, table_name)
            
            if table_exists:
                existing_df = pd.read_sql(f"SELECT TOP 0 * FROM {table_name}", engine)
                if not all(column in existing_df.columns for column in df.columns):
                    messagebox.showerror("Schema Mismatch", "The structure of the Excel file does not match the existing table.")
                    return

                action = messagebox.askquestion("Table Exists", 
                                                f"Table '{table_name}' already exists. Do you want to overwrite the data (Yes) or append (No)?",
                                                icon='question')
                if action == 'yes':
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    messagebox.showinfo("Success", "Data imported and table overwritten successfully.")
                elif action == 'no':
                    df.to_sql(table_name, engine, if_exists='append', index=False)
                    messagebox.showinfo("Success", "Data appended successfully.")
            else:
                create_table = messagebox.askyesno("Table Not Found", 
                                                   f"Table '{table_name}' does not exist. Do you want to create a new table?")
                if create_table:
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    messagebox.showinfo("Success", f"Table '{table_name}' created and data imported successfully.")
                else:
                    messagebox.showinfo("Cancelled", "Operation cancelled by user.")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data:\n{e}")

    def export_db_to_excel(self):
        engine = self.connect_to_database()
        while True:
            table_name = simpledialog.askstring("Delete Data", "Enter the name of the table to delete data from:")
            if not table_name:
                return  # Cancel if no input

            engine = self.db_config.create_engine_connection()
            if not engine:
                messagebox.showwarning("Database connection error")
                return
    
            inspector = inspect(engine)
            if table_name in inspector.get_table_names():
                break  # Valid table name
            else:
                messagebox.showwarning("Invalid Table", f"Table '{table_name}' does not exist. Please try again.")
        try:

            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, engine)

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
                title="Save Excel File"
            )
            if not save_path:
                return  # User canceled the save dialog

            df.to_excel(save_path, index=False)
            messagebox.showinfo("Success", f"Table '{table_name}' exported successfully to '{save_path}'.")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{e}")
    
    def delete_table(self):
        engine = self.connect_to_database()
        """Deletes an entire table from the database based on user input."""
        while True:
            table_name = simpledialog.askstring("Delete Data", "Enter the name of the table to delete data from:")
            if not table_name:
                return  # Cancel if no input

            engine = self.db_config.create_engine_connection()
            if not engine:
                messagebox.showwarning("Database connection error")
                return

            inspector = inspect(engine)
            if table_name in inspector.get_table_names():
                break  # Valid table name
            else:
                messagebox.showwarning("Invalid Table", f"Table '{table_name}' does not exist. Please try again.")

        # Delete table
        try:
            with engine.begin() as connection:
                connection.execute(text(f"DROP TABLE {table_name}"))
            messagebox.showinfo("Success", f"Table '{table_name}' has been deleted.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete table '{table_name}':\n{e}")

    def delete_data(self):
        engine = self.connect_to_database()
        # Prompt user for table name and validate existence
        while True:
            table_name = simpledialog.askstring("Delete Data", "Enter the name of the table to delete data from:")
            if not table_name:
                return  # Cancel if no input

            engine = self.db_config.create_engine_connection()
            if not engine:
                messagebox.showwarning("Database connection error")
                return

            inspector = inspect(engine)
            if table_name in inspector.get_table_names():
                break  # Valid table name
            else:
                messagebox.showwarning("Invalid Table", f"Table '{table_name}' does not exist. Please try again.")

        # Prompt for column and value to delete specific rows
        column_name = simpledialog.askstring("Column Name", f"Enter the column name in '{table_name}' to check:")
        if not column_name:
            return

        value = simpledialog.askstring("Value", f"Enter the value in '{column_name}' to delete matching rows:")
        if not value:
            return

        # Execute deletion of rows matching column/value
        try:
            with engine.begin() as connection:
                delete_query = text(f"DELETE FROM {table_name} WHERE {column_name} = :value")
                connection.execute(delete_query, {"value": value})
            messagebox.showinfo("Success", f"Rows with '{column_name} = {value}' have been deleted from '{table_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete data from '{table_name}':\n{e}")
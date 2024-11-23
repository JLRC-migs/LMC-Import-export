from db_config import DatabaseConfig
from imports import *

class BackendController:
    def __init__(self):
        self.server = 'MIGS-LAPTOP\\SQLEXPRESS'
        self.database_name = 'SampleDB'  # Automatically set to SampleDB
        self.db_config = DatabaseConfig(self.server, self.database_name)
        self.engine = self.db_config.create_engine_connection()

    def check_table_exists(self, engine, table_name):
        inspector = inspect(engine)
        return inspector.has_table(table_name)

    def get_table_list(self, engine):
        """
        Fetches a list of available tables in the connected database.
        """
        inspector = inspect(engine)
        return inspector.get_table_names()

    def select_table(self, engine):
        """
        Presents the user with a dropdown or input dialog to select a table from the database.
        """
        table_list = self.get_table_list(engine)
        if not table_list:
            messagebox.showinfo("No Tables", "No tables found in the database.")
            return None
        table_name = simpledialog.askstring(
            "Select Table",
            f"Available Tables:\n{', '.join(table_list)}\nEnter your choice:",
        )
        if table_name not in table_list:
            messagebox.showerror("Invalid Selection", f"'{table_name}' is not a valid table name.")
            return None
        return table_name

    def import_excel_to_sql(self):
        if not self.engine:
            messagebox.showerror("Database Error", "Failed to connect to the database.")
            return

        # Prompt for Excel file
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        # Prompt for table name from available tables
        table_name = self.select_table(self.engine)
        if not table_name:
            return

        try:
            # Load Excel data
            df = pd.read_excel(file_path)
            staging_table_name = f"{table_name}_staging"

            with self.engine.begin() as connection:
                try:
                    # Load data into staging table
                    df.to_sql(staging_table_name, self.engine, if_exists="replace", index=False)
                    messagebox.showinfo("Success", f"Staging table '{staging_table_name}' created.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create staging table:\n{e}")
                    return

                # Check if the main table exists
                table_exists = self.check_table_exists(self.engine, table_name)

                # Prompt user for action
                action = simpledialog.askstring(
                    "Choose Action",
                    "Choose an option:\n1: Overwrite\n2: Append\n3: Merge by 'keyno'"
                )

                if action == "1":
                    # Overwrite: Drop and rename staging table
                    try:
                        if table_exists:
                            connection.execute(text(f"DROP TABLE {table_name}"))
                        connection.execute(text(f"EXEC sp_rename '{staging_table_name}', '{table_name}'"))
                        messagebox.showinfo("Success", "Table overwritten successfully.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to overwrite table:\n{e}")
                        return

                elif action == "2":
                    # Append: Insert all rows from staging table into the main table
                    try:
                        if table_exists:
                            insert_query = text(f"INSERT INTO {table_name} SELECT * FROM {staging_table_name}")
                            connection.execute(insert_query)
                        else:
                            connection.execute(text(f"EXEC sp_rename '{staging_table_name}', '{table_name}'"))
                        messagebox.showinfo("Success", "Data appended successfully.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to append data:\n{e}")
                        return

                elif action == "3":
                    # Merge: Remove duplicates based on primary key 'keyno' and append
                    try:
                        primary_key_column = "keyno"
                        if primary_key_column not in df.columns:
                            messagebox.showerror("Error", f"Primary key '{primary_key_column}' not found in the data.")
                            return

                        merge_query = text(f"""
                            DELETE FROM {table_name}
                            WHERE {primary_key_column} IN (SELECT {primary_key_column} FROM {staging_table_name});
                            INSERT INTO {table_name} SELECT * FROM {staging_table_name};
                        """)
                        connection.execute(merge_query)
                        messagebox.showinfo("Success", "Data merged successfully.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to merge data:\n{e}")
                        return
                else:
                    messagebox.showinfo("Cancelled", "Operation cancelled by user.")
                    return

                # Drop the staging table after processing
                try:
                    connection.execute(text(f"DROP TABLE {staging_table_name}"))
                    messagebox.showinfo("Cleanup", "Staging table dropped successfully.")
                except Exception as e:
                    messagebox.showerror("Cleanup Error", f"Failed to drop staging table:\n{e}")

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
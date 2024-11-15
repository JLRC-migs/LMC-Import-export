from imports import *
from backend_controller import BackendController

class ExcelToSQLAppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Import/Export to MS SQL")
        self.root.geometry("300x300")  # Set window size

        # Initialize backend controller
        self.controller = BackendController()

        # Create buttons
        self.create_widgets()

    def create_widgets(self):
        # Import Button
        import_button = tk.Button(self.root, text="Import Excel to DB", bg = '#0bed2f',command=self.import_excel_to_db)
        import_button.pack(pady=20)

        # Export Button
        export_button = tk.Button(self.root, text="Export DB to Excel", bg = '#3fb7f0',command=self.export_db_to_excel)
        export_button.pack(pady=20)

        # Delete Table Button
        delete_table_button = tk.Button(self.root, text="Delete Table", bg = '#f51a1a', command=self.controller.delete_table)
        delete_table_button.pack(pady=20)
        
        # Delete Data Button
        delete_data_button = tk.Button(self.root, text="Delete Data", bg = '#ff7f12',command=self.controller.delete_data)
        delete_data_button.pack(pady=20)

    def import_excel_to_db(self):
        self.controller.import_excel_to_sql()

    def export_db_to_excel(self):
        self.controller.export_db_to_excel()
    

# GUI Setup
if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToSQLAppUI(root)
    root.mainloop()

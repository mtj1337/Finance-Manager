import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- Database Initialization ---
def initialize_database():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# --- Database Operations ---
def add_transaction_to_db(amount, category, description, date):
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (amount, category, description, date)
        VALUES (?, ?, ?, ?)
    """, (amount, category, description, date))
    conn.commit()
    conn.close()

def fetch_transactions():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- Export Function ---
def export_to_csv(filepath):
    data = fetch_transactions()
    df = pd.DataFrame(data, columns=["ID", "Amount", "Category", "Description", "Date"])
    df.to_csv(filepath, index=False)

# --- Visualization ---
def plot_expenses_by_category():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
    data = cursor.fetchall()
    conn.close()

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(8, 5))
    plt.bar(categories, amounts, color='skyblue')
    plt.title("Expenses by Category")
    plt.xlabel("Category")
    plt.ylabel("Total Amount")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# --- Delete Transaction Function ---
def delete_transaction(transaction_id):
    """Deletes a transaction from the database by ID."""
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()

# --- GUI ---
class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Manager")
        self.root.geometry("800x600")

        # Tab Control
        self.tab_control = ttk.Notebook(root)
        self.tab_add = ttk.Frame(self.tab_control)
        self.tab_view = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_add, text="Add Transaction")
        self.tab_control.add(self.tab_view, text="View Transactions")
        self.tab_control.pack(expand=1, fill="both")

        # --- Tab 1: Add Transaction ---
        self.add_tab()

        # --- Tab 2: View Transactions ---
        self.view_tab()

    def add_tab(self):
        # Create a frame to center the content
        frame = tk.Frame(self.tab_add)
        frame.place(relx=0.5, rely=0.5, anchor="center")  # Center the frame in the tab

        # Amount field
        tk.Label(frame, text="Amount:").grid(row=0, column=0, padx=10, pady=10)
        self.amount_entry = tk.Entry(frame)
        self.amount_entry.grid(row=0, column=1, padx=10, pady=10)

        # Category field
        tk.Label(frame, text="Category:").grid(row=1, column=0, padx=10, pady=10)
        self.category_entry = ttk.Combobox(frame, values=["Food", "Housing", "Transport", "Entertainment", "Other"])
        self.category_entry.grid(row=1, column=1, padx=10, pady=10)

        # Description field
        tk.Label(frame, text="Description:").grid(row=2, column=0, padx=10, pady=10)
        self.description_entry = tk.Entry(frame)
        self.description_entry.grid(row=2, column=1, padx=10, pady=10)

        # Date field
        tk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=10)
        self.date_entry = tk.Entry(frame)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=3, column=1, padx=10, pady=10)

        # Add Transaction Button
        tk.Button(frame, text="Add Transaction", command=self.add_transaction).grid(row=4, column=0, columnspan=2, pady=20)

    def add_transaction(self):
        try:
            amount = float(self.amount_entry.get())
            category = self.category_entry.get()
            description = self.description_entry.get()
            date = self.date_entry.get()

            if not category or not date:
                raise ValueError("Category and date are required!")

            add_transaction_to_db(amount, category, description, date)
            messagebox.showinfo("Success", "Transaction added successfully.")
            self.clear_entries()

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def clear_entries(self):
        self.amount_entry.delete(0, tk.END)
        self.category_entry.set("")
        self.description_entry.delete(0, tk.END)

    def view_tab(self):
        # Treeview to display transactions
        self.tree = ttk.Treeview(self.tab_view, columns=("ID", "Amount", "Category", "Description", "Date"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Date", text="Date")
        self.tree.column("ID", width=50)  # Make the ID column narrower
        self.tree.pack(fill="both", expand=True)

        # Buttons
        tk.Button(self.tab_view, text="Refresh", command=self.refresh_transactions).pack(pady=10)
        tk.Button(self.tab_view, text="Export to CSV", command=self.export_csv).pack(pady=10)
        tk.Button(self.tab_view, text="Show Chart", command=plot_expenses_by_category).pack(pady=10)
        tk.Button(self.tab_view, text="Remove Transaction", command=self.remove_transaction).pack(pady=10)

        # Refresh the table initially
        self.refresh_transactions()

    def refresh_transactions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        transactions = fetch_transactions()
        for transaction in transactions:
            # Insert transaction data, including the ID in the Treeview
            self.tree.insert("", "end", values=(transaction[0], transaction[1], transaction[2], transaction[3], transaction[4]))

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv")])
        if filepath:
            export_to_csv(filepath)
            messagebox.showinfo("Success", "Data exported.")

    def remove_transaction(self):
        """Removes the selected transaction from the database and updates the view."""
        selected_item = self.tree.selection()  # Get the selected item(s)
        if not selected_item:
            messagebox.showerror("Error", "No transaction selected.")
            return

        # Get the ID of the selected transaction
        transaction_id = self.tree.item(selected_item, "values")[0]

        # Confirm deletion
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this transaction?")
        if confirm:
            delete_transaction(transaction_id)  # Remove from the database
            self.refresh_transactions()  # Refresh the treeview
            messagebox.showinfo("Success", "Transaction removed.")

# --- Application Execution ---
if __name__ == "__main__":
    initialize_database()
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()

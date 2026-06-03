import sqlite3

class Database:
    def __init__(self, db_path: str = "profit_system.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity_sold INTEGER NOT NULL,
                revenue REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cost_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fixed_cost REAL NOT NULL,
                variable_cost REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def insert_transaction(self, product_name, price, quantity_sold, revenue):
        self.conn.execute(
            "INSERT INTO transactions (product_name, price, quantity_sold, revenue) VALUES (?,?,?,?)",
            (product_name, price, quantity_sold, revenue)
        )
        self.conn.commit()

    def insert_cost_center(self, name, fixed_cost, variable_cost):
        self.conn.execute(
            "INSERT INTO cost_centers (name, fixed_cost, variable_cost) VALUES (?,?,?)",
            (name, fixed_cost, variable_cost)
        )
        self.conn.commit()

    def get_all_transactions(self):
        cursor = self.conn.execute(
            "SELECT id, product_name, price, quantity_sold, revenue, created_at FROM transactions ORDER BY created_at"
        )
        return cursor.fetchall()

    def get_all_cost_centers(self):
        cursor = self.conn.execute(
            "SELECT id, name, fixed_cost, variable_cost, created_at FROM cost_centers ORDER BY created_at"
        )
        return cursor.fetchall()

    def delete_transaction(self, record_id):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (record_id,))
        self.conn.commit()

    def delete_cost_center(self, record_id):
        self.conn.execute("DELETE FROM cost_centers WHERE id=?", (record_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_total_units_sold(self):
        cursor = self.conn.execute("SELECT SUM(quantity_sold) FROM transactions")
        result = cursor.fetchone()[0]
        return result or 0
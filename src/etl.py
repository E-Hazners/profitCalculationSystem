import pandas as pd
import sqlite3
from tkinter import filedialog, messagebox


class ETLPipeline:
    """
    Reads a CSV file, validates and cleans it, 
    then loads it into the database (Extract → Transform → Load).
    
    Expected CSV columns:
        product_name, price, quantity_sold
    """

    REQUIRED_COLUMNS = {"product_name", "price", "quantity_sold"}

    def __init__(self, db):
        self.db = db
        self.log = []

    def run(self, filepath: str) -> dict:
        self.log = []
        try:
            raw = self._extract(filepath)
            cleaned = self._transform(raw)
            count = self._load(cleaned)
            return {"success": True, "rows_loaded": count, "log": self.log}
        except Exception as e:
            return {"success": False, "rows_loaded": 0, "log": self.log + [f"ERROR: {e}"]}

    def _extract(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        self.log.append(f"✔ Extracted {len(df)} rows from file")
        missing = self.REQUIRED_COLUMNS - set(df.columns.str.strip().str.lower())
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        df.columns = df.columns.str.strip().str.lower()
        return df

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        original_len = len(df)

        # Drop rows with missing values
        df = df.dropna(subset=["product_name", "price", "quantity_sold"])

        # Strip whitespace from product names
        df["product_name"] = df["product_name"].astype(str).str.strip()

        # Coerce numeric types, drop invalid
        df["price"]         = pd.to_numeric(df["price"], errors="coerce")
        df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce")
        df = df.dropna(subset=["price", "quantity_sold"])

        # Drop negative or zero values
        df = df[(df["price"] > 0) & (df["quantity_sold"] > 0)]

        # Calculate revenue
        df["revenue"] = df["price"] * df["quantity_sold"]

        dropped = original_len - len(df)
        if dropped > 0:
            self.log.append(f"⚠  Dropped {dropped} invalid/incomplete rows")
        self.log.append(f"✔ Transformed: {len(df)} clean rows ready to load")
        return df

    def _load(self, df: pd.DataFrame) -> int:
        count = 0
        for _, row in df.iterrows():
            self.db.insert_transaction(
                row["product_name"],
                float(row["price"]),
                int(row["quantity_sold"]),
                float(row["revenue"])
            )
            count += 1
        self.log.append(f"✔ Loaded {count} rows into database")
        return count
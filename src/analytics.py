import pandas as pd


class Analytics:
    """Computes summary statistics, funnel metrics, and sensitivity analysis."""

    def __init__(self, calculator):
        self.calculator = calculator

    # Summary statistics 
    def get_summary_stats(self) -> dict:
        transactions = self.calculator.transactions
        if not transactions:
            return {}

        df = pd.DataFrame(transactions, columns=[
            "id", "product_name", "price", "quantity_sold", "revenue", "created_at"
        ])

        return {
            "total_transactions": len(df),
            "total_units_sold":   int(df["quantity_sold"].sum()),
            "avg_revenue":        df["revenue"].mean(),
            "median_revenue":     df["revenue"].median(),
            "std_revenue":        df["revenue"].std(),
            "max_revenue":        df["revenue"].max(),
            "min_revenue":        df["revenue"].min(),
            "avg_price":          df["price"].mean(),
            "top_product":        df.loc[df["revenue"].idxmax(), "product_name"],
            "revenue_per_unit":   df["revenue"].sum() / df["quantity_sold"].sum()
        }

    # Funnel analysis
    def get_funnel(self) -> list:
        """
        Simulates a conversion funnel:
        Products listed → Products with sales → Profitable products → High-margin products
        """
        transactions = self.calculator.transactions
        cost_centers = self.calculator.cost_centers
        total_units  = self.calculator.total_units_sold

        if not transactions:
            return []

        avg_var_cost = sum(r[3] for r in cost_centers) if cost_centers else 0

        df = pd.DataFrame(transactions, columns=[
            "id", "product_name", "price", "quantity_sold", "revenue", "created_at"
        ])

        product_groups = df.groupby("product_name").agg(
            total_revenue=("revenue", "sum"),
            avg_price=("price", "mean"),
            total_qty=("quantity_sold", "sum")
        ).reset_index()

        total_fixed = self.calculator.get_total_fixed_costs()
        fixed_share = total_fixed / len(product_groups) if len(product_groups) > 0 else 0

        all_products      = len(product_groups)
        with_sales        = len(product_groups[product_groups["total_qty"] > 0])
        contribution      = product_groups["avg_price"] - avg_var_cost
        profitable        = len(product_groups[contribution > 0])
        high_margin       = len(product_groups[contribution > (product_groups["avg_price"] * 0.3)])

        return [
            ("Products listed",         all_products),
            ("Products with sales",      with_sales),
            ("Profitable products",      profitable),
            ("High-margin products",     high_margin),
        ]

    # Sensitivity analysis
    def get_sensitivity(self, price_change_pct: float, cost_change_pct: float) -> dict:
        """
        What-if simulator: recalculates revenue, costs, and profit
        given % changes in price and variable cost.
        """
        transactions = self.calculator.transactions
        cost_centers = self.calculator.cost_centers
        total_units  = self.calculator.total_units_sold

        base_revenue  = self.calculator.get_total_revenue()
        base_fixed    = self.calculator.get_total_fixed_costs()
        base_variable = self.calculator.get_total_variable_costs()
        base_profit   = self.calculator.get_profit()

        new_revenue  = base_revenue  * (1 + price_change_pct / 100)
        new_variable = base_variable * (1 + cost_change_pct  / 100)
        new_costs    = base_fixed + new_variable
        new_profit   = new_revenue - new_costs

        return {
            "base_revenue":  base_revenue,
            "new_revenue":   new_revenue,
            "base_costs":    base_fixed + base_variable,
            "new_costs":     new_costs,
            "base_profit":   base_profit,
            "new_profit":    new_profit,
            "profit_change": new_profit - base_profit,
            "margin_change": (
                (new_profit / new_revenue * 100) - (base_profit / base_revenue * 100)
                if base_revenue > 0 and new_revenue > 0 else 0
            )
        }

    # Export
    def export_to_csv(self, filepath: str):
        transactions = self.calculator.transactions
        cost_centers = self.calculator.cost_centers
        total_units  = self.calculator.total_units_sold

        t_df = pd.DataFrame(transactions, columns=[
            "id", "product_name", "price", "quantity_sold", "revenue", "created_at"
        ])

        c_df = pd.DataFrame(cost_centers, columns=[
            "id", "name", "fixed_cost", "variable_cost_per_unit", "created_at"
        ])
        c_df["total_cost"] = c_df["fixed_cost"] + c_df["variable_cost_per_unit"] * total_units

        stats = self.get_summary_stats()

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            t_df.to_excel(writer, sheet_name="Transactions",  index=False)
            c_df.to_excel(writer, sheet_name="Cost Centers",  index=False)
            pd.DataFrame([stats]).T.rename(columns={0: "Value"}).to_excel(
                writer, sheet_name="Summary Stats"
            )
        return True
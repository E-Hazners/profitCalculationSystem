class ProfitCalculator:
    def __init__(self):
        self.transactions = []
        self.cost_centers = []
        self.total_units_sold = 0

    def load_from_db(self, transactions, cost_centers, total_units_sold=0):
        self.transactions = transactions
        self.cost_centers = cost_centers
        self.total_units_sold = total_units_sold

    def get_total_revenue(self) -> float:
        return sum(row[4] for row in self.transactions)

    def get_total_fixed_costs(self) -> float:
        return sum(row[2] for row in self.cost_centers)

    def get_total_variable_costs(self) -> float:
        return sum(row[3] for row in self.cost_centers) * self.total_units_sold

    def get_total_costs(self) -> float:
        return self.get_total_fixed_costs() + self.get_total_variable_costs()

    def get_profit(self) -> float:
        return self.get_total_revenue() - self.get_total_costs()
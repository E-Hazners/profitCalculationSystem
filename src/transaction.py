from src.product import Product

class Transaction:
    def __init__(self, product: Product, quantity_sold: int):
        self.product = product
        self.quantity_sold = quantity_sold

    def get_revenue(self) -> float:
        return self.product.price * self.quantity_sold

    def __repr__(self) -> str:
        return f"Transaction(product={self.product.name}, revenue={self.get_revenue()})"
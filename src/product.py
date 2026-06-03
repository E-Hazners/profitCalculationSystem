class Product:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

    def get_total_value(self) -> float:
        return self.price * self.quantity

    def __repr__(self) -> str:
        return f"Product(name={self.name}, price={self.price}, quantity={self.quantity})"
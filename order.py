import copy
from abc import ABC, abstractmethod

# 1) Заказ сам по себе — тоже компонент, у него будет get_price()
class OrderComponent(ABC):
    @abstractmethod
    def get_price(self):
        pass

# 2) Конкретный заказ хранит в себе логику total() и реализует get_price()
class ConcreteOrder(OrderComponent):
    def __init__(self, items, is_vip=False):
        self.items = list(items)
        self.is_vip = is_vip
        self.discount_strategy = None

    def total(self):
        total = sum(item['price'] for item in self.items)
        if self.discount_strategy:
            total -= self.discount_strategy.calculate(total, self)
        return total

    def set_discount_strategy(self, strategy):
        self.discount_strategy = strategy

    # просто перенаправляем
    def get_price(self):
        return self.total()

    # для Prototype
    def clone(self):
        return copy.deepcopy(self)

# 3) Стратегии скидок остаются без изменений
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount, order):
        pass

class VolumeDiscount(DiscountStrategy):
    def calculate(self, amount, order):
        return amount * 0.1 if amount > 1000 else 0

class VIPDiscount(DiscountStrategy):
    def calculate(self, amount, order):
        return amount * 0.05 if order.is_vip else 0

# 4) Общий декоратор — тоже компонент, и он оборачивает любой другой компонент
class OrderDecorator(OrderComponent):
    def __init__(self, wrapped: OrderComponent):
        self.wrapped = wrapped

    def get_price(self):
        return self.wrapped.get_price()

# 5) Конкретные декораторы услуг
class InsuranceDecorator(OrderDecorator):
    def get_price(self):
        price = self.wrapped.get_price()
        print("Добавлена страховка: +50")
        return price + 50

class PriorityShippingDecorator(OrderDecorator):
    def get_price(self):
        price = self.wrapped.get_price()
        print("Добавлена приоритетная доставка: +100")
        return price + 100

# --- пример использования ---
if __name__ == "__main__":
    # исходный заказ
    order = ConcreteOrder(items=[{'price': 600}, {'price': 700}], is_vip=True)
    order.set_discount_strategy(VolumeDiscount())
    print("Итог с учётом скидки:", order.get_price())

    # клонирование (Prototype)
    copy_order = order.clone()
    copy_order.is_vip = False
    print("Скопированный заказ (не VIP):", copy_order.get_price())

    # декораторы
    decorated = InsuranceDecorator(order)                 # сначала страховка
    fully_decorated = PriorityShippingDecorator(decorated)  # затем приоритетная доставка
    print("Итог с доп. услугами:", fully_decorated.get_price())

# payment.py: Адаптеры для интеграции со Stripe и PayPal
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """Общий интерфейс для платежей."""
    @abstractmethod
    def pay(self, amount):
        pass

class StripeAPI:
    """Внешняя библиотека Stripe с собственным методом оплаты."""
    def stripe_pay(self, amount):
        print(f"Stripe: проведён платёж на сумму {amount}")

class PayPalAPI:
    """Внешняя библиотека PayPal с собственным методом оплаты."""
    def send_payment(self, amount):
        print(f"PayPal: проведена транзакция на сумму {amount}")

class StripeAdapter(PaymentProcessor):
    """Адаптер для StripeAPI."""
    def __init__(self, stripe_api: StripeAPI):
        self.stripe_api = stripe_api
    def pay(self, amount):
        self.stripe_api.stripe_pay(amount)

class PayPalAdapter(PaymentProcessor):
    """Адаптер для PayPalAPI."""
    def __init__(self, paypal_api: PayPalAPI):
        self.paypal_api = paypal_api
    def pay(self, amount):
        self.paypal_api.send_payment(amount)

# Пример использования адаптеров
if __name__ == "__main__":
    stripe = StripeAPI()
    paypal = PayPalAPI()
    processors = [StripeAdapter(stripe), PayPalAdapter(paypal)]
    for processor in processors:
        processor.pay(100)  # единый интерфейс pay()

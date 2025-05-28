# notification.py: Наблюдатель – оповещение о статусе заказа
from abc import ABC, abstractmethod

class OrderSubject:
    """Издатель: хранит статус заказа и список подписчиков."""
    def __init__(self):
        self._observers = []
        self.status = "Создан"

    def attach(self, observer):
        self._observers.append(observer)
    def detach(self, observer):
        self._observers.remove(observer)
    def notify(self):
        for observer in self._observers:
            observer.update(self)

    def update_status(self, status):
        self.status = status
        print(f"Заказ: статус изменён на «{self.status}»")
        self.notify()

class Observer(ABC):
    """Интерфейс наблюдателя."""
    @abstractmethod
    def update(self, subject: OrderSubject):
        pass

class ClientObserver(Observer):
    def update(self, subject: OrderSubject):
        print(f"Клиент: уведомлён о статусе заказа «{subject.status}»")

class ManagerObserver(Observer):
    def update(self, subject: OrderSubject):
        print(f"Менеджер: уведомлён о статусе заказа «{subject.status}»")

# Пример использования паттерна Наблюдатель
if __name__ == "__main__":
    order = OrderSubject()
    client_obs = ClientObserver()
    manager_obs = ManagerObserver()
    order.attach(client_obs)
    order.attach(manager_obs)
    order.update_status("В обработке")
    order.update_status("Отправлен")

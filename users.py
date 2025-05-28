# users.py: Factory Method для создания различных типов пользователей
from abc import ABC, abstractmethod

class User(ABC):
    """Базовый класс пользователя."""
    def __init__(self, name, email):
        self.name = name
        self.email = email

    @abstractmethod
    def role(self):
        pass

class Manager(User):
    def role(self):
        return "Менеджер"

class Client(User):
    def role(self):
        return "Клиент"

class Admin(User):
    def role(self):
        return "Администратор"

class UserFactory(ABC):
    """Интерфейс Фабрики пользователей."""
    @abstractmethod
    def create_user(self, name, email):
        pass

class ManagerFactory(UserFactory):
    def create_user(self, name, email):
        return Manager(name, email)

class ClientFactory(UserFactory):
    def create_user(self, name, email):
        return Client(name, email)

class AdminFactory(UserFactory):
    def create_user(self, name, email):
        return Admin(name, email)

# Пример использования фабричного метода
if __name__ == "__main__":
    factories = [ManagerFactory(), ClientFactory(), AdminFactory()]
    for factory in factories:
        user = factory.create_user("Иван Иванов", f"{factory.__class__.__name__}@example.com")
        print(f"Создан пользователь: {user.name}, роль: {user.role()}")

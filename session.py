# session.py: Singleton – глобальный менеджер сессий пользователей
class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Создание нового менеджера сессий.")
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.active_sessions = {}
        return cls._instance

    def login(self, user):
        self.active_sessions[user.email] = user
        print(f"Пользователь {user.name} вошел в систему.")

    def logout(self, user):
        if user.email in self.active_sessions:
            del self.active_sessions[user.email]
            print(f"Пользователь {user.name} вышел из системы.")

# Пример использования Одиночки
if __name__ == "__main__":
    manager = SessionManager()
    manager2 = SessionManager()
    print("Singleton одинаковый экземпляр:", manager is manager2)
    # Output:
    # Создание нового менеджера сессий.
    # Singleton одинаковый экземпляр: True

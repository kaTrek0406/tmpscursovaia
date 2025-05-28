# reports.py
from abc import ABC, abstractmethod

# Базовые классы отчетов
class SummaryReport:
    def __init__(self):
        self.content = ""

class DetailedReport:
    def __init__(self):
        self.content = ""

# Абстрактная фабрика
class ReportFactory(ABC):
    @abstractmethod
    def create_summary(self) -> SummaryReport: ...
    @abstractmethod
    def create_detailed(self) -> DetailedReport: ...

# Финансовые отчеты
class FinancialReportFactory(ReportFactory):
    def create_summary(self):
        r = SummaryReport()
        r.content = (
            "=== Финансовый Сводный Отчет ===\n"
            "- Доходы: 100 000\n"
            "- Расходы: 60 000\n"
            "- Прибыль: 40 000\n"
        )
        return r
    def create_detailed(self):
        r = DetailedReport()
        r.content = (
            "=== Финансовый Детальный Отчет ===\n"
            "• Январь: прибыль 5 000\n"
            "• Февраль: прибыль 6 000\n"
            "• …\n"
        )
        return r

# Аналитические отчеты
class AnalyticalReportFactory(ReportFactory):
    def create_summary(self):
        r = SummaryReport()
        r.content = (
            "=== Аналитический Сводный Отчет ===\n"
            "- Тренд продаж: ↑ 12%\n"
            "- Средний чек: 250\n"
        )
        return r
    def create_detailed(self):
        r = DetailedReport()
        r.content = (
            "=== Аналитический Детальный Отчет ===\n"
            "• Топ‑3 товара по продажам\n"
            "• Поведение клиентов по сегментам\n"
        )
        return r

# Логистические отчеты
class LogisticsReportFactory(ReportFactory):
    def create_summary(self):
        r = SummaryReport()
        r.content = (
            "=== Логистический Сводный Отчет ===\n"
            "- Всего доставок: 320\n"
            "- Среднее время доставки: 2.5 ч\n"
        )
        return r
    def create_detailed(self):
        r = DetailedReport()
        r.content = (
            "=== Логистический Детальный Отчет ===\n"
            "• Маршрут A–B: 120 доставок\n"
            "• Маршрут B–C: 80 доставок\n"
        )
        return r

# Builder для фильтров и периода (ваш существующий код)
class ReportBuilder:
    def __init__(self, factory: ReportFactory):
        self.factory = factory
        self.date_range = None
        self.filters = []
    def set_date_range(self, start, end):
        self.date_range = (start, end)
        return self
    def add_filter(self, f):
        self.filters.append(f)
        return self
    def build_summary(self):
        r = self.factory.create_summary()
        r.content += f"Период: {self.date_range}\n"
        if self.filters:
            r.content += f"Фильтры: {self.filters}\n"
        return r
    def build_detailed(self):
        r = self.factory.create_detailed()
        r.content += f"Период: {self.date_range}\n"
        if self.filters:
            r.content += f"Фильтры: {self.filters}\n"
        return r

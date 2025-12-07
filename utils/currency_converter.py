"""
Конвертер валют для перевода BYN <-> RUB
Использует API для получения актуального курса
"""
import requests
import logging
from typing import Optional
from utils.logger import get_logger

logger = get_logger('currency_converter')

# Примерный курс (будет обновляться через API)
# 1 BYN ≈ 30 RUB (примерно)
DEFAULT_BYN_TO_RUB = 30.0
DEFAULT_RUB_TO_BYN = 1.0 / DEFAULT_BYN_TO_RUB


class CurrencyConverter:
    """Конвертер валют"""
    
    def __init__(self):
        self.byn_to_rub_rate = DEFAULT_BYN_TO_RUB
        self.rub_to_byn_rate = DEFAULT_RUB_TO_BYN
        self.last_update = None
    
    def update_rates(self) -> bool:
        """Обновить курсы валют через API"""
        try:
            # Используем бесплатный API для курса валют
            # Можно использовать exchangerate-api.com или другой бесплатный сервис
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/BYN',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'RUB' in data['rates']:
                    self.byn_to_rub_rate = data['rates']['RUB']
                    self.rub_to_byn_rate = 1.0 / self.byn_to_rub_rate
                    self.last_update = data.get('date')
                    logger.info(f"Курсы валют обновлены: 1 BYN = {self.byn_to_rub_rate:.2f} RUB")
                    return True
        except Exception as e:
            logger.warning(f"Не удалось обновить курсы валют через API: {e}. Используем значения по умолчанию")
        
        return False
    
    def byn_to_rub(self, amount: float) -> float:
        """Конвертировать BYN в RUB"""
        return round(amount * self.byn_to_rub_rate, 2)
    
    def rub_to_byn(self, amount: float) -> float:
        """Конвертировать RUB в BYN"""
        return round(amount * self.rub_to_byn_rate, 2)
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Получить курс валют"""
        if from_currency.upper() == 'BYN' and to_currency.upper() == 'RUB':
            return self.byn_to_rub_rate
        elif from_currency.upper() == 'RUB' and to_currency.upper() == 'BYN':
            return self.rub_to_byn_rate
        return None


# Глобальный экземпляр конвертера
_converter = CurrencyConverter()

def convert_byn_to_rub(amount: float) -> float:
    """Конвертировать BYN в RUB (глобальная функция)"""
    return _converter.byn_to_rub(amount)

def convert_rub_to_byn(amount: float) -> float:
    """Конвертировать RUB в BYN (глобальная функция)"""
    return _converter.rub_to_byn(amount)

def update_currency_rates() -> bool:
    """Обновить курсы валют (глобальная функция)"""
    return _converter.update_rates()


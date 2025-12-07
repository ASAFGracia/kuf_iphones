"""
Модуль для извлечения модели iPhone из текста
Поддерживает различные варианты написания: iphone11, айфон11, iPhone 11 и т.д.
"""
import re
from typing import Optional

# Полный список моделей iPhone (от новых к старым для правильного распознавания)
IPHONE_MODELS_PATTERNS = {
    # iPhone 17 серия (самые новые - проверяем первыми)
    'iPhone 17 Pro Max': [
        r'iphone\s*17\s*pro\s*max',
        r'айфон\s*17\s*про\s*макс',
        r'17\s*pro\s*max',
        r'17\s*про\s*макс',
    ],
    'iPhone 17 Pro': [
        r'iphone\s*17\s*pro(?!\s*max)',
        r'айфон\s*17\s*про(?!\s*макс)',
        r'17\s*pro(?!\s*max)',
        r'17\s*про(?!\s*макс)',
    ],
    'iPhone 17': [
        r'iphone\s*17(?!\s*(pro|plus|max|air))',
        r'айфон\s*17(?!\s*(про|плюс|макс|эйр))',
        r'\b17\b(?!\s*(pro|plus|max|air|про|плюс|макс|эйр))',
    ],
    'iPhone Air': [
        r'iphone\s*air',
        r'айфон\s*эйр',
        r'\bair\b',
    ],
    # iPhone 16 серия
    'iPhone 16 Pro Max': [
        r'iphone\s*16\s*pro\s*max',
        r'айфон\s*16\s*про\s*макс',
        r'16\s*pro\s*max',
        r'16\s*про\s*макс',
    ],
    'iPhone 16 Pro': [
        r'iphone\s*16\s*pro(?!\s*max)',
        r'айфон\s*16\s*про(?!\s*макс)',
        r'16\s*pro(?!\s*max)',
        r'16\s*про(?!\s*макс)',
    ],
    'iPhone 16 Plus': [
        r'iphone\s*16\s*plus',
        r'айфон\s*16\s*плюс',
        r'16\s*plus',
        r'16\s*плюс',
    ],
    'iPhone 16e': [
        r'iphone\s*16\s*e\b',
        r'айфон\s*16\s*е\b',
        r'16\s*e\b',
        r'16\s*е\b',
        r'iphone\s*16e',
        r'айфон\s*16е',
    ],
    'iPhone 16': [
        r'iphone\s*16(?!\s*(pro|plus|max|e))',
        r'айфон\s*16(?!\s*(про|плюс|макс|е))',
        r'\b16\b(?!\s*(pro|plus|max|e|про|плюс|макс|е))',
    ],
    # iPhone 15 серия
    'iPhone 15 Pro Max': [
        r'iphone\s*15\s*pro\s*max',
        r'айфон\s*15\s*про\s*макс',
        r'15\s*pro\s*max',
        r'15\s*про\s*макс',
    ],
    'iPhone 15 Pro': [
        r'iphone\s*15\s*pro(?!\s*max)',
        r'айфон\s*15\s*про(?!\s*макс)',
        r'15\s*pro(?!\s*max)',
        r'15\s*про(?!\s*макс)',
    ],
    'iPhone 15 Plus': [
        r'iphone\s*15\s*plus',
        r'айфон\s*15\s*плюс',
        r'15\s*plus',
        r'15\s*плюс',
    ],
    'iPhone 15': [
        r'iphone\s*15(?!\s*(pro|plus|max))',
        r'айфон\s*15(?!\s*(про|плюс|макс))',
        r'\b15\b(?!\s*(pro|plus|max|про|плюс|макс))',
    ],
    # iPhone 14 серия
    'iPhone 14 Pro Max': [
        r'iphone\s*14\s*pro\s*max',
        r'айфон\s*14\s*про\s*макс',
        r'14\s*pro\s*max',
        r'14\s*про\s*макс',
    ],
    'iPhone 14 Pro': [
        r'iphone\s*14\s*pro(?!\s*max)',
        r'айфон\s*14\s*про(?!\s*макс)',
        r'14\s*pro(?!\s*max)',
        r'14\s*про(?!\s*макс)',
    ],
    'iPhone 14 Plus': [
        r'iphone\s*14\s*plus',
        r'айфон\s*14\s*плюс',
        r'14\s*plus',
        r'14\s*плюс',
    ],
    'iPhone 14': [
        r'iphone\s*14(?!\s*(pro|plus|max))',
        r'айфон\s*14(?!\s*(про|плюс|макс))',
        r'\b14\b(?!\s*(pro|plus|max|про|плюс|макс))',
    ],
    # iPhone 13 серия
    'iPhone 13 Pro Max': [
        r'iphone\s*13\s*pro\s*max',
        r'айфон\s*13\s*про\s*макс',
        r'13\s*pro\s*max',
        r'13\s*про\s*макс',
    ],
    'iPhone 13 Pro': [
        r'iphone\s*13\s*pro(?!\s*max)',
        r'айфон\s*13\s*про(?!\s*макс)',
        r'13\s*pro(?!\s*max)',
        r'13\s*про(?!\s*макс)',
    ],
    'iPhone 13 mini': [
        r'iphone\s*13\s*mini',
        r'айфон\s*13\s*мини',
        r'13\s*mini',
        r'13\s*мини',
    ],
    'iPhone 13': [
        r'iphone\s*13(?!\s*(pro|mini|max))',
        r'айфон\s*13(?!\s*(про|мини|макс))',
        r'\b13\b(?!\s*(pro|mini|max|про|мини|макс))',
    ],
    # iPhone 12 серия
    'iPhone 12 Pro Max': [
        r'iphone\s*12\s*pro\s*max',
        r'айфон\s*12\s*про\s*макс',
        r'12\s*pro\s*max',
        r'12\s*про\s*макс',
    ],
    'iPhone 12 Pro': [
        r'iphone\s*12\s*pro(?!\s*max)',
        r'айфон\s*12\s*про(?!\s*макс)',
        r'12\s*pro(?!\s*max)',
        r'12\s*про(?!\s*макс)',
    ],
    'iPhone 12 mini': [
        r'iphone\s*12\s*mini',
        r'айфон\s*12\s*мини',
        r'12\s*mini',
        r'12\s*мини',
    ],
    'iPhone 12': [
        r'iphone\s*12(?!\s*(pro|mini|max))',
        r'айфон\s*12(?!\s*(про|мини|макс))',
        r'\b12\b(?!\s*(pro|mini|max|про|мини|макс))',
    ],
    # iPhone 11 серия
    'iPhone 11 Pro Max': [
        r'iphone\s*11\s*pro\s*max',
        r'айфон\s*11\s*про\s*макс',
        r'11\s*pro\s*max',
        r'11\s*про\s*макс',
    ],
    'iPhone 11 Pro': [
        r'iphone\s*11\s*pro(?!\s*max)',
        r'айфон\s*11\s*про(?!\s*макс)',
        r'11\s*pro(?!\s*max)',
        r'11\s*про(?!\s*макс)',
    ],
    'iPhone 11': [
        r'iphone\s*11(?!\s*pro)',
        r'айфон\s*11(?!\s*про)',
        r'\b11\b(?!\s*(pro|про))',
        # Также поддерживаем слитное написание: iphone11, айфон11
        r'iphone11(?!\s*pro)',
        r'айфон11(?!\s*про)',
        r'iphone\s*11\s*$',  # В конце строки
    ],
    # iPhone SE
    'iPhone SE (2-го поколения)': [
        r'iphone\s*se\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го)\s*(?:поколения|gen|generation)',
        r'айфон\s*се\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го)\s*(?:поколения|gen|generation)',
        r'se\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го)\s*(?:поколения|gen|generation)',
        r'iphone\s*se\s*3',
        r'айфон\s*се\s*3',
        r'se\s*3',
    ],
    'iPhone SE': [
        r'iphone\s*se(?!\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го))',
        r'айфон\s*се(?!\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го))',
        r'\bse\b(?!\s*(?:2|второго|2го|2-го|3|третьего|3го|3-го))',
    ],
    # iPhone X серия
    'iPhone XS Max': [
        r'iphone\s*xs\s*max',
        r'айфон\s*кс\s*макс',
        r'xs\s*max',
        r'кс\s*макс',
    ],
    'iPhone XS': [
        r'iphone\s*xs(?!\s*max)',
        r'айфон\s*кс(?!\s*макс)',
        r'\bxs\b(?!\s*max)',
        r'\bкс\b(?!\s*макс)',
    ],
    'iPhone XR': [
        r'iphone\s*xr',
        r'айфон\s*кср',
        r'\bxr\b',
        r'\bкср\b',
    ],
    'iPhone X': [
        r'iphone\s*x(?!\s*(s|r|s\s*max|кс|кср))',
        r'айфон\s*икс(?!\s*(s|r|s\s*max|кс|кср))',
        r'\bx\b(?!\s*(s|r|s\s*max|кс|кср))',
    ],
}


def extract_iphone_model(text: str) -> Optional[str]:
    """
    Извлечь модель iPhone из текста
    Поддерживает различные варианты написания:
    - iphone11, айфон11, iPhone 11
    - iphone 13 pro, айфон 13 про
    - и т.д.
    
    Args:
        text: Текст для анализа (заголовок, описание)
    
    Returns:
        Название модели или None
    """
    if not text:
        return None
    
    # Нормализуем текст: приводим к нижнему регистру, убираем лишние пробелы
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    
    # Проверяем каждую модель (от новых к старым)
    for model, patterns in IPHONE_MODELS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return model
    
    return None


def extract_memory(text: str) -> Optional[str]:
    """
    Извлечь объем памяти из текста
    Поддерживает различные форматы:
    - 64gb, 64 гб, 64гб
    - 128GB, 128 ГБ
    - 256gb и т.д.
    
    Args:
        text: Текст для анализа
    
    Returns:
        Объем памяти в формате "64 ГБ" или None
    """
    if not text:
        return None
    
    # Нормализуем текст
    normalized = text.lower()
    
    # Паттерны для поиска памяти (различные варианты написания)
    patterns = [
        # Стандартные форматы с пробелом
        (r'(\d+)\s*(?:gb|гб)', 'ГБ'),
        (r'(\d+)\s*(?:tb|тб)', 'ТБ'),
        (r'(\d+)\s*(?:mb|мб)', 'МБ'),
        # Без пробела: 64гб, 128гб, 64gb
        (r'(\d+)(?:гб|gb)', 'ГБ'),
        (r'(\d+)(?:тб|tb)', 'ТБ'),
        (r'(\d+)(?:мб|mb)', 'МБ'),
        # С дефисом или другими разделителями
        (r'(\d+)[\s\-/]*(?:gb|гб)', 'ГБ'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            try:
                memory_value = int(match.group(1))
                # Проверяем разумные значения для iPhone
                if 8 <= memory_value <= 2048:  # От 8 ГБ до 2 ТБ
                    return f"{memory_value} {unit}"
            except (ValueError, IndexError):
                continue
    
    return None


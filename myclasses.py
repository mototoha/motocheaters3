"""
Тут расположены различные классы и методы для работы бота,
    которые не относятся напрямую к другим модулям или используются в нескольких.
"""
from dataclasses import dataclass, field


@dataclass
class Cheater:
    """
    Тип данных - кидала.
    """
    vk_id: str = None
    fifty: bool = False
    screen_name: str = None
    telephone: List[str] = field(default_factory=list)
    card: List[str] = field(default_factory=list)
    proof_link: List[str] = field(default_factory=list)

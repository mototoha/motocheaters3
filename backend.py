"""
Тут находится бекэнд проекта.
"""
from dataclasses import dataclass, field, fields
from typing import List


@dataclass
class Cheater:
    """
    Тип данных - кидала.
      vk_id: str = None
        id
      fifty: bool = False
        полтинник
      screen_name: str = None
        красивый адрес страницы
      telephone: List[str] = field(default_factory=list)
        список телефонов кидалы
      card: List[str] = field(default_factory=list)
        список карт кидалы
      proof_link: List[str] = field(default_factory=list)
        ссылки на доказательства деятельности
    """
    vk_id: str = None
    fifty: bool = False
    screen_name: str = None
    telephones: List[str] = field(default_factory=list)
    cards: List[str] = field(default_factory=list)
    proof_links: List[str] = field(default_factory=list)

    def __str__(self):
        """
        Переопределим вывод строки.

        :return: Значения словарем.
        """
        result = {}
        for f in fields(self):
            result[f.name] = self.__getattribute__(f.name)
        return str(result)


"""
Тут находится бекэнд проекта.
"""
from dataclasses import dataclass, field, fields
from typing import List

from database import DBCheaters


REGEXP_MAIN = (
    r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<screen_name>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)'
    r'|(?P<card>\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(\s\n)?)'
    r'|\+?(?P<telephone>\d{10,15}(\s\n)?)'
)

REGEXP_ADMIN = (
    r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<screen_name>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<proof_link>wall-\d*_\d*)'
    r'|(?P<card>\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(\s\n)?)'
    r'|\+?(?P<telephone>\d{10,15}(\s\n)?)'
    r'|(?P<fifty>50|fifty)'
)


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


class Backend:
    """
    Класс занимается обработкой бекэнда.
    """
    def __init__(self, db_params: dict):
        """
        Инициализация. В ней будет создан объект для взаимодействия с БД.
        Сейчас это только Sqlite.
            sqlite: {
            'type': 'sqlite',
            'filename': 'db_filename',
            }

        :param db_params: Словарь с параметрами БД.
        """
        db_type = db_params.get('type')
        if db_type == 'sqlite':
            db_filename = db_params.get('filename')
            self.db = DBCheaters(db_filename)

    def get_cheater_full_info(self,
                              vk_id: str = None,
                              screen_name: str = None,
                              telephone: str = None,
                              card: str = None,
                              proof_link: str = None,
                              ) -> Cheater:
        """
        Метод возвращает инфу про кидалу, которая есть в БД. На вход подаётся один из параметров.
        Корректно работать будет только с одним параметром. Приоритет - по порядку в заголовке.

        :param vk_id: id VK
        :param screen_name: отображаемое имя
        :param telephone: телефон
        :param card: номер карты
        :param proof_link: ссылка на пруф
        :return: объект Cheater или None, если ничего не нашел.
        """
        result = Cheater()
        if vk_id:
            db_result = self.db.get_dict_from_table(table='screen_names',
                                                 rows=['screen_name', 'vk_id'],
                                                 condition_dict={'vk_id': vk_id, 'changed': 'False'})
            if db_result:
                result.vk_id = db_result['vk_id']
                result.screen_name = db_result['screen_name']
            else:
                result = None
        return result

    def screen_name_is_changed(self, vk_id: str, screen_name: str):
        """
        Изменяет параметр changed для screen_name в БД.

        :param vk_id: id, который поменял имя.
        :param screen_name: screen_name, который больше не используется.
        """
        self.db.update_table('screen_names', 'changed', 'True', 'vk_id', cheater_db.vk_id)
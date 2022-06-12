"""
Тут находится бекэнд проекта.
"""
from dataclasses import dataclass, field, fields
from typing import (
    Any,
    List,
)

from database import DBCheaters


REGEXP_MAIN = (
    r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<screen_name>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)'
    r'|(?P<card>\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(\s\n)?)'
    r'|\+?(?P<telephone>\d{10,15}(\s\n)?)'
)

REGEXP_ADMIN = (
    r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<proof_link_user>wall\d*_\d*)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<proof_link>wall-\d*_\d*)'
    r'|((https://|http://)?(m\.)?vk.com/){1}(?P<screen_name>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)'
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
    telephone: List[str] = field(default_factory=list)
    card: List[str] = field(default_factory=list)
    proof_link: List[str] = field(default_factory=list)

    def __str__(self):
        """
        Переопределим вывод строки.

        :return: Значения словарем.
        """
        result = {}
        for f in fields(self):
            result[f.name] = self.__getattribute__(f.name)
        return str(result)

    def get(self, value: str) -> Any:
        """
        Метод возвращает значение параметра Value кидалы.
        Если спрашивают непонятно что - возвращает None.
        :param value: Атрибут, который хочешь получить.
        :return: Значение или None.
        """
        for f in fields(self):
            if f.name == value:
                return self.__getattribute__(f.name)
        return None


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
        db_result = None
        if screen_name:
            db_result = self.db.get_dict_from_table(table='screen_names',
                                                    columns=['screen_name', 'vk_id'],
                                                    condition_dict={'screen_name': screen_name, 'changed': 'False'})
        if db_result:
            vk_id = db_result['vk_id']

        if vk_id:
            result = Cheater()
            result.vk_id = vk_id

            # TODO Сделать запрос через join'ы
            db_result = self.db.get_dict_from_table(table='vk_id',
                                                    columns=['vk_id', 'fifty'])
            result.fifty = db_result[0]['fifty']

            db_result = self.db.get_dict_from_table(table='screen_names',
                                                    columns=['screen_name'],
                                                    condition_dict={'changed': 'False'})
            result.screen_name = db_result[0]['screen_name']

            db_result = self.db.get_dict_from_table(table='telephones',
                                                    columns=['telephone'])
            result.telephone = db_result['telephones']

            db_result = self.db.get_dict_from_table(table='cards',
                                                    columns=['card'])
            result.card = db_result['card']

            db_result = self.db.get_dict_from_table(table='proof_links',
                                                    columns=['proof_link'])
            result.card = db_result['proof_link']
        else:
            result = None
        return result

    def screen_name_is_changed(self, vk_id: str, screen_name: str) -> None:
        """
        Изменяет параметр changed на True для screen_name в БД.

        :param vk_id: id, который поменял имя.
        :param screen_name: screen_name, который больше не используется.
        """
        set_params = {'changed': 'True'}
        where = {'vk_id': vk_id, 'screen_name': screen_name}
        self.db.update_table('screen_names', {'changed': 'True'}, {'vk_id': vk_id, 'screen_name': screen_name})

    def new_screen_name(self, vk_id: str, screen_name: str) -> None:
        """
        Метод записывает в БД новую строчку про screen_name.

        :param vk_id: ID ВК.
        :param screen_name: Имя ВК.
        :return: ID ВК.
        """
        self.db.add_screen_name(screen_name=screen_name, vk_id=vk_id)

    def check_existence(self, check_values: dict) -> bool:
        """
        Метод проверяет наличие записи в БД.
        Берем первую пару. И ищем по соответствующей таблице.

        :param check_values: Словарь 'что ищем': 'значение'
        :return: Да или Нет.
        """
        if list(check_values.keys())[0] == 'vk_id':
            table = 'vk_id'
        elif list(check_values.keys())[0] == 'screen_name':
            table = 'screen_names'
        elif list(check_values.keys())[0] == 'telephone':
            table = 'telephones'
        elif list(check_values.keys())[0] == 'card':
            table = 'cards'
        elif list(check_values.keys())[0] == 'proof_link':
            table = 'proof_links'
        else:
            return False
        return self.db.check_the_existence(table, check_values)

    def add_cheater(self, cheater: Cheater, cheater_db: Cheater = None) -> Cheater:
        """
        Метод добавляет (обновляет) данные в БД.
        Добавляется разница между cheater и cheater_db.

        :param cheater: Что вводил пользователь.
        :param cheater_db:  Что найдено в БД.
        :return : Что добавлено в читерах.
        """
        cheater_update = Cheater()
        if not cheater_db:
            cheater_update = cheater
        else:
            if cheater.fifty != cheater_db.fifty:
                cheater_update.fifty = cheater.fifty
            else:
                cheater_update.fifty = None
            if cheater.screen_name != cheater_db.screen_name:
                cheater_update.screen_name = cheater.screen_name

            cheater_update.telephone = list(set(cheater.telephone)-set(cheater_db.telephone))
            cheater_update.card = list(set(cheater.card) - set(cheater_db.card))
            cheater_update.proof_link = list(set(cheater.proof_link) - set(cheater_db.proof_link))

        if cheater_update.screen_name:
            self.db.add_screen_name(cheater_update.screen_name, cheater.vk_id)
        if cheater_update.telephone:
            self.db.add_telephones(cheater_update.telephone, cheater.vk_id)
        if cheater_update.card:
            self.db.add_cards(cheater_update.card, cheater.vk_id)
        if cheater_update.proof_link:
            self.db.add_proof_links(cheater_update.proof_link, cheater.vk_id)

        return cheater_update

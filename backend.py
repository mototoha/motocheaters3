"""
Тут находится бекэнд проекта.
Все методы, что не пользуют vk_api и db.
"""
from dataclasses import dataclass, field, fields
from typing import (
    Any,
    List,
    Optional,
    Union,
    Literal,
    Tuple,
)

from database import DBCheaters

REGEXP_CHEATER = {
    'vk_id': r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)',
    'proof_link':  r'((https://|http://)?(m\.)?vk.com/){1}(?P<proof_link>wall-\d*_\d*)',
    'screen_name': r'((https://|http://)?(m\.)?vk.com/){1}(?P<screen_name>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)',
    'card': r'(?P<card>\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(\s\n)?)',
    'telephone': r'\+?(?P<telephone>\d{10,15}(\s\n)?)',
    'fifty': r'(?P<fifty>50|fifty)'
}


def merge_list(l1: list, l2: list):
    """
    Функция сливает два списка, исключая повторы.

    :param l1: Первый список.
    :param l2: Второй список. Добавится в конец первого без повторов.
    :return: Суммарный список.
    """
    result = l1
    set_l1 = set(l1)
    for el in l2:
        if el not in set_l1:
            result.append(l2)
    return result


def get_regexp(*args: 'str') -> str:
    """
    Возвращает регулярку с нужными строками для парсинга. В качестве аргументов принимает значения регулярок,
    которые надо использовать. Если ничего не передали - берется все.\n
    Можно передать ключевые слова:\n
    all -все;\n
    main, search - vk_id, screen_name, card, telephone;\n
    add - vk_id, screen_name, card, telephone, proof_link, fifty;\n
    del - vk_id, screen_name, card, telephone, proof_link.

    Либо перечисляем группы регулярок.\n
    Если сначала идут ключевые слова - остальное игнорируется.\n
    Если идут группы - ключевые слова игнорируются.

    :param args: Указываем параметры, которые хотим парсить регуляркой.
    :return: Регулярка.
    """
    result = ''
    # Группы регулярок.
    regexp_group_list = tuple(REGEXP_CHEATER.keys())
    # Запрошенные группы регулярок.
    request_group_list: tuple
    if args[0] == 'all':
        request_group_list = tuple(REGEXP_CHEATER.keys())
    elif args[0] in ('main', 'search'):
        request_group_list = tuple(['vk_id', 'screen_name', 'card', 'telephone'])
    elif args[0] == 'add':
        request_group_list = tuple(['vk_id', 'screen_name', 'card', 'telephone', 'proof_link', 'fifty'])
    elif args[0] == 'del':
        request_group_list = tuple(['vk_id', 'screen_name', 'card', 'telephone', 'proof_link'])
    elif args:
        request_group_list = args
    else:
        request_group_list = tuple(REGEXP_CHEATER.keys())
    for group in request_group_list:
        if group in regexp_group_list:
            if result:
                # Если регулярка уже есть, добавляем или |
                result += r'|'
            result += REGEXP_CHEATER[group]
    return result


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
        result = ''
        for f in fields(self):
            result += str(f.name) + ': ' + str(self.__getattribute__(f.name)) + '\n'
        return result

    def __bool__(self):
        """
        Переопределен метод bool.
        Если все значения пустые - вернет False.

        :return: bool
        """
        result = False
        for f in fields(self):
            result |= bool(self.__getattribute__(f.name))
        return result

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

    def str_csv(self, sep: str = ';') -> str:
        """
        Метод возвращает строку для вставки в csv файл. Параметр fifty опускается.
        :return: параметры через разделитель (по-умолчанию - запятая)
        """
        result = ''
        for f in fields(self):
            if f.name != 'fifty':
                result += str(self.__getattribute__(f.name)) + sep
        result += '\n'
        return result

    def update(self,
               vk_id: str = None,
               screen_name: str = None,
               fifty: bool = None,
               telephone: List[str] = None,
               card: List[str] = None,
               proof_link: List[str] = None):
        """
        Метод позволяет обновить поля объекта в меньшее количество строк.
        Ничего не удаляет

        :param vk_id: Новый ID.
        :param screen_name: Новое имя.
        :param fifty: Новое значение полтинника.
        :param telephone: Добавляются новые телефоны.
        :param card: Добавляются новые карты.
        :param proof_link:  Добавляются новые пруфлинки.
        """
        if vk_id:
            self.vk_id = vk_id
        if screen_name:
            self.screen_name = screen_name
        if fifty:
            self.fifty = fifty
        if telephone:
            merge_list(self.telephone, telephone)
        if card:
            merge_list(self.card, card)
        if proof_link:
            merge_list(self.proof_link, proof_link)


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

    def get_cheater_info(self,
                         id_name: Optional[str] = None,
                         telephone: Optional[str] = None,
                         card: Optional[str] = None,
                         proof_link: Optional[str] = None,
                         return_fields: Optional[Union[str, List[str]]] = None,
                         ) -> Optional[Union[Cheater, List[Cheater]]]:
        """
        Метод возвращает всю инфу про кидалу, которая есть в БД. На вход подаются параметры, по которым надо его найти.
        Сейчас используется только первый по порядку.\n
        В результате вернется либо Cheater(), лио список Cheater()'ов, либо None.

        :param id_name: id или screen_name VK,
        :param telephone: телефон,
        :param card: номер карт,
        :param proof_link: ссылка на пруф,
        :param return_fields: поля, которые требуется вернуть,
        :return: объект (список объектов) Cheater или None, если ничего не нашел.
        """
        sql_result = []
        vk_id = ''
        # Сначала определяемся, по какому vk_id искать.
        if id_name:
            if id_name.startswith(('id', 'club', 'public', 'event')):
                vk_id = id_name
            else:
                sql_result = self.db.get_dict_from_table(table='screen_names',
                                                         columns=['vk_id'],
                                                         condition_dict={'screen_name': id_name,
                                                                         'changed': 'False'})
                id_name = sql_result['vk_id']
        else:
            if telephone:
                sql_result = self.db.get_dict_from_table(table='telephones',
                                                         columns=['vk_id'],
                                                         condition_dict={'telephone': telephone})
            elif card:
                sql_result = self.db.get_dict_from_table(table='cards',
                                                         columns=['vk_id'],
                                                         condition_dict={'card': card})
            elif proof_link:
                sql_result = self.db.get_dict_from_table(table='proof_links',
                                                         columns=['vk_id'],
                                                         condition_dict={'proof_link': proof_link})
            if sql_result:
                vk_id = sql_result[0].get('vk_id')

        # Если нашелся или передан vk_id.
        if vk_id:
            cheater_info = Cheater()
            # Обращаемся к БД за остальными параметрами.
            sql_result = self.db.get_dict_from_table(table='vk_ids',
                                                     columns=['vk_id', 'fifty'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                cheater_info.vk_id = sql_result[0]['vk_id']
                cheater_info.fifty = sql_result[0]['fifty']

            sql_result = self.db.get_dict_from_table(table='screen_names',
                                                     columns=['screen_name'],
                                                     condition_dict={'vk_id': vk_id, 'changed': 'False'})
            if sql_result:
                cheater_info.screen_name = sql_result[0]['screen_name']

            sql_result = self.db.get_dict_from_table(table='telephones',
                                                     columns=['telephone'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.proof_link = items_list

            sql_result = self.db.get_dict_from_table(table='cards',
                                                     columns=['card'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.proof_link = items_list

            sql_result = self.db.get_dict_from_table(table='proof_links',
                                                     columns=['proof_link'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.proof_link = items_list
            if not cheater_info:
                result = None
            else:
                result = cheater_info
        else:
            result = None
        return result

    def new_screen_name(self, vk_id: str, screen_name: str) -> None:
        """
        Метод записывает в БД новую строчку про screen_name.

        :param vk_id: ID ВК.
        :param screen_name: Имя ВК.
        :return: ID ВК.
        """
        # Помечаем старые имена как changed=True.
        self.db.update_table(table='screen_names',
                             set_params={'changed': True},
                             where={'vk_id': vk_id})
        # Добавляем новое имя.
        self.db.add_screen_name(screen_name=screen_name, vk_id=vk_id)

    def check_existence(self, check_values: dict) -> bool:
        """
        Метод проверяет наличие записи в БД.
        Берем первую пару. И ищем по соответствующей таблице.\n
        'vk_id' -> 'vk_ids'\n
        'screen_name' -> 'screen_names'\n
        telephone' -> 'telephones'\n
        'card' -> 'cards'\n
        'proof_link' -> 'proof_links'\n

        :param check_values: Словарь 'что ищем': 'значение'
        :return: Да или Нет.
        """
        if list(check_values.keys())[0] == 'vk_id':
            table = 'vk_ids'
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
        cheater_update = Cheater()  # Что добавлять в БД.
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

        if cheater_update.vk_id:
            self.db.add_vk_id(cheater_update.vk_id, cheater.fifty)
        if cheater_update.screen_name:
            self.db.add_screen_name(cheater_update.screen_name, cheater.vk_id)
        if cheater_update.telephone:
            self.db.add_telephones(cheater_update.telephone, cheater.vk_id)
        if cheater_update.card:
            self.db.add_cards(cheater_update.card, cheater.vk_id)
        if cheater_update.proof_link:
            self.db.add_proof_links(cheater_update.proof_link, cheater.vk_id)

        return cheater_update

    def get_id_screen_name(self, param: Literal['vk_id', 'screen_name'] = None, value: str = None) -> Tuple[str, str]:
        """
        Метод возвращает действующую запись о соответствии vk_id и screen_name.\n
        Screen_name с параметром changed=True игнорятся.

        :param param: str 'vk_id' или 'screen_name'
        :param value: id '1231231' или screen_name 'sample'
        :return: {'id': '', 'screen_name': ''}
        """
        result = {}
        if param in ('vk_id', 'screen_name'):
            sql = self.db.get_dict_from_table('screen_names',
                                              ['screen_name', 'vk_id'],
                                              {param: value, 'changed': False})
            if sql:
                # На всякий случай, если вернется несколько строк из БД.
                result['vk_id'] = sql[0][1]
                result['screen_name'] = sql[0][0]
        return result['vk_id'], result['screen_name']

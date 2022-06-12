"""
Classes for VKBot
"""
import re
import requests
import time
from typing import List
from dataclasses import dataclass, field

from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.exception_factory import VKAPIError

import database
import dialogs

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
    """
    vk_id: str = None
    fifty: bool = False
    screen_name: str = None
    telephone: List[str] = field(default_factory=list)
    card: List[str] = field(default_factory=list)
    proof_link: List[str] = field(default_factory=list)


class DialogStates(BaseStateGroup):
    """
    Уровни диалога.
    """
    TELL_ABOUT_CHEATER_STATE = 'tell_about_cheater'


class AdminStates(BaseStateGroup):
    """
    Уровни админского меню.
    """
    MAIN = 'admin'
    SPAM = 'admin_spam'
    ADD_CHEATER = 'add_cheater'
    ADD_CHEATER_ID = 'add_cheater_id'
    ADD_CHEATER_TEL = 'add_cheater_tel'
    ADD_CHEATER_CARD = 'add_cheater_card'
    ADMIN_DEL_CHEATER = 'del_cheater'


class VKBot(Bot):
    """
    Main bot class.
    """

    dialog_states = DialogStates

    def __init__(self, vk_token: str, db_filename: str, cheaters_filename: str):
        self.vk_token = vk_token
        self.db_filename = db_filename
        self.cheaters_filename = cheaters_filename

        super().__init__(vk_token)
        self.labeler.vbml_ignore_case = True

        self.db = database.DBCheaters(self.db_filename)
        self.vk_admin_id = self.db.get_admins()
        self.group_info = self.api.groups.get_by_id

    async def update_cheaters_from_file(self, url: str):
        """
        Функция возьмет текстовый файл по ссылке, распарсит его, перенесет все данные в БД.

        :param url: ссылка на файл ВК
        :return: Ответ
        """
        print('Сейчас начнем парсить файл', url)
        content = requests.get(url).content.decode()
        cheaters_list = await self._get_cheaters_list_from_file(content)  # Список кидал
        if cheaters_list:
            result = await self._update_database_from_list(cheaters_list)  # Update DB
            return result
        else:  # если результат пустой
            return dialogs.no_data_in_file

    async def _get_cheaters_list_from_file(self, content: str) -> list:
        """
        Функция получает на вход текст из файла и возвращает списком кидал.
        Если по дороге возникает исключение, не позволяющее нормально продолжить работу - возвращает текст.

        :param content: Текст из файла.
        :return: List кидал.
        """
        # TODO Неправильно привязались карты, надо рассмотреть
        fifty = False  # Идентификатор "Полтинников" - кто иногда кидает
        cheater = {'vk_id': '', 'fifty': fifty, 'screen_name': '', 'telephone': [], 'card': []}  # Запись про кидалу
        cheaters_list = []  # Список кидал
        for line in content.split('\n'):
            print('Строка : \n', line)
            if re.search(r'vk\.com', line):
                subline = line
            else:
                # Если это не vk_id, все символы в строке делаем слитно, надеясь, что получится последовательность цифр.
                subline = re.sub(r'[- +\r]', '', str(line))
            match = re.search(REGEXP_MAIN, subline)
            if match:
                print("Найдено совпадение из регулярки: \n", match.groupdict())
                if match.lastgroup in ['vk_id', 'screen_name']:
                    if cheater.get('vk_id') or cheater.get('screen_name'):
                        # Запись добавляется в список, когда встречается следующая запись про кидалу.
                        # Сделано, чтобы можно было добавлять телефоны и карты конкретного кидалы.
                        # Последняя запись добавляется после цикла.
                        print('Добавляю кидалу в список. \n', cheater)
                        cheaters_list.append(cheater)
                        cheater = {'vk_id': '', 'fifty': fifty, 'screen_name': '', 'telephone': [], 'card': []}
                    if match.lastgroup == 'vk_id':
                        # Если это vk_id - добавляем id в cheater.
                        cheater['vk_id'] = match[match.lastgroup]
                        user = None
                        try:
                            user = await self.api.users.get(user_ids=match[match.lastgroup],
                                                            fields='screen_name'
                                                            )
                            print('Запрос юзера вернул:\n', user)
                        except VKAPIError[6]:
                            print('Слишком много запросов, повтори через полчаса')
                            return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        if user:
                            if user[0].screen_name != cheater['vk_id']:
                                cheater['screen_name'] = user[0].screen_name
                    elif match.lastgroup == 'screen_name':
                        # Если имя - ищем vk_id и добавляем id и screen_name в cheater.
                        user = None
                        group = None
                        try:
                            user = await self.api.users.get(user_ids=match[match.lastgroup],
                                                            fields='screen_name'
                                                            )
                            print('Запрос юзера вернул:\n', user)
                        except VKAPIError[6]:
                            print('Слишком много запросов, повтори через полчаса')
                            return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        if user:
                            cheater['vk_id'] = 'id' + str(user[0].id)
                            if user[0].screen_name != cheater['vk_id']:
                                cheater['screen_name'] = user[0].screen_name
                        else:
                            try:
                                group = await self.api.groups.get_by_id(group_id=match[match.lastgroup],
                                                                        fields='screen_name'
                                                                        )
                                print('Запрос группы:\n', group)
                                if group[0].type.value == 'group':
                                    group_type = 'club'
                                elif group[0].type.value == 'page':
                                    group_type = 'public'
                                elif group[0].type.value == 'event':
                                    group_type = 'event'
                                else:
                                    group_type = 'club'
                                cheater['vk_id'] = group_type + str(group[0].id)
                                # VK_API возвращает screen_name=vk_id, если имени нет.
                                if group[0].screen_name != cheater['vk_id']:
                                    cheater['screen_name'] = group[0].screen_name
                            except VKAPIError[100]:
                                print('Группа', match[match.lastgroup], 'не найдена')
                            except VKAPIError[6]:
                                print('Слишком много запросов, повтори через полчаса')
                                return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        # Если не нашелся ни юзер, ни группа.
                        if not user and not group:
                            print('В файле попался неправильный идентификатор, не могу понять, кто это: ', line)
                            print('Возможно, страница удалена \n ')
                            cheater[match.lastgroup] = match[match.lastgroup]
                else:
                    # Если найдена карта или телефон - добавляем их в cheater с предыдущим vk_id.
                    print(cheater)
                    cheater.setdefault(match.lastgroup, []).append(match[match.lastgroup])
            elif subline == 'fifty':
                fifty = True
                print('Далее идут полтиники')
            else:
                print('Непонятная строка \n')
            # Пауза, чтоб ВК не банил.
            time.sleep(0.5)
        # Последний в списке
        if cheater.get('vk_id'):
            print('Добавляю кидалу в список. \n', cheater)
            cheaters_list.append(cheater)

        print('Вот итоговый список:', cheaters_list, '\n')
        return cheaters_list

    async def _update_database_from_list(self, cheaters_list: str):
        """
        Принимает на вход список кидал, обновляет базу и возвращает ответ строкой.
        :return: Ответ для пользователя
        """
        for cheater in cheaters_list:
            print('Разбираем запись ', cheater, sep='\n')
            if cheater['vk_id']:
                db_record = self.db.get_dict_from_table('vk_id',
                                                        ['vk_id', 'fifty'],
                                                        {'vk_id': cheater['vk_id']})
                if db_record:
                    print('Такой vk_id есть!')
                    if db_record['fifty'] != cheater['fifty']:
                        print('Поменялся fifty на', cheater['fifty'])
                        self.db.update_table('vk_id', 'fifty', cheater['fifty'], 'vk_id', cheater['vk_id'])
                else:
                    print('Добавляю кидалу')
                    self.db.add_vk_id(cheater['vk_id'], cheater['fifty'])

            if cheater['screen_name']:
                if self.db.check_the_existence('screen_names',
                                               {'screen_name': cheater['screen_name'],
                                                'vk_id': cheater['vk_id']
                                                }
                                               ):
                    print('Такой screen_name-id есть!')
                else:
                    print('Добавляем новый screen_name-id')
                    self.db.add_screen_name(cheater['screen_name'], cheater['vk_id'])

            if cheater['telephone']:
                if cheater['vk_id']:
                    id_tel = cheater['vk_id']
                elif cheater['screen_name']:
                    id_tel = cheater['screen_name']
                else:
                    id_tel = None
                for tel in cheater['telephone']:
                    if self.db.check_the_existence('telephones', {'telephone': tel, 'vk_id': id_tel}):
                        print('Связка телефон-id уже есть')
                    else:
                        print('Добавляем новый tel-id')
                        self.db.add_telephones([tel], cheater['vk_id'])

            if cheater['card']:
                if cheater['vk_id']:
                    id_card = cheater['vk_id']
                elif cheater['screen_name']:
                    id_card = cheater['screen_name']
                else:
                    id_card = None
                for card in cheater['card']:
                    if self.db.check_the_existence('cards', {'card': card, 'vk_id': id_card}):
                        print('Связка card-id уже есть')
                    else:
                        print('Добавляем новый card-id')
                        self.db.add_cards([card], cheater['vk_id'])

        return 'Я закончил обновлять БД!'

    def check_cheater(self, parameter: str, value: str):
        """
        Проверяем наличие кидалы в БД.
        Если возвращается пустая строка, то запрос некорректно отработал.

        :return vk_id, False.
        """
        if parameter == 'vk_id':
            check_result = self.db.get_cheater_id('vk_id', {parameter: value})
        elif parameter == 'screen_name':
            check_result = self.db.get_cheater_id('screen_names', {parameter: value})
        elif parameter == 'card':
            check_result = self.db.get_cheater_id('cards', {parameter: value})
        elif parameter == 'telephone':
            check_result = self.db.get_cheater_id('telephones', {parameter: value})
        else:
            check_result = False
        if check_result:
            return check_result[0]
        else:
            return False

    def is_user_admin(self, peer_id: int) -> bool:
        """
        Определяет, является ли пользователь админом.
        :param peer_id:
        :return:
        """
        if peer_id in self.vk_admin_id:
            return True
        else:
            return False

    def get_group_admins(self) -> List[str]:
        """
        Метод обращается к API VK и возвращает список админов группы.
        :return: list[str]
        """
        pass


if __name__ == '__main__':
    #  Тут будет тест
    pass

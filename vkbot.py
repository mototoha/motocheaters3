"""
Classes for VKBot
"""
import re
import requests
import time

from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.exception_factory import VKAPIError

import database
import dialogs


class DialogStates(BaseStateGroup):
    """
    Dialog levels.
    """
    MAIN_STATE = 0
    TELL_ABOUT_CHEATER = 1
    ADMIN_MENU = 10


class IsAdmin(BaseStateGroup):
    """
    Маркер админа. Может добавлять и удалять админов.
    Также является модератором.
    """
    ADMIN = 1


class IsModerator(BaseStateGroup):
    """
    Маркер модератора. Может получать сообщения о кидалах.
    """
    MODERATOR = 1


class VKBot(Bot):
    """
    Main bot class.
    """
    regexp_main = (
        r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+(\s\n)?)'
        r'|((https://|http://)?(m\.)?vk.com/){1}(?P<shortname>([a-z]|[A-Z]|[0-9]|_)+(\s\n)?)'
        r'|(?P<card>\d{16}(\s\n)?)'
        r'|\+?(?P<telephone>\d{10,15}(\s\n)?)'
    )

    dialog_states = DialogStates

    def __init__(self, vk_token: str, db_filename: str, cheaters_filename: str):
        self.vk_token = vk_token
        self.db_filename = db_filename
        self.cheaters_filename = cheaters_filename

        super().__init__(vk_token)
        self.labeler.vbml_ignore_case = True

        self.db = database.DBCheaters(self.db_filename)
        self.vk_admin_id = self.db.get_admins()

    async def update_cheaters_from_file(self, url: str):
        """
        Функция возьмет текстовый файл по ссылке, распарсит его, перенесет все данные в БД.

        :param url: ссылка на файл ВК
        :return: Ответ
        """
        print('Сейчас начнем парсить файл', url)
        content = requests.get(url).content.decode()
        cheaters_list = await self._get_cheaters_list_from_file(content)  # Список кидал
        if not cheaters_list:  # если результат пустой
            return dialogs.no_data_in_file
        else:
            result = await self._update_database(cheaters_list)  # Update DB
            return result

    async def _get_cheaters_list_from_file(self, content: str) -> list:
        """
        Функция получает на вход текст из файла и возвращает списком кидал.
        Если по дороге возникает исключение, не позволяющее нормально продолжить работу - возвращает текст.

        :param content: Текст из файла.
        :return: List кидал.
        """
        # TODO Неправильно привязались карты, надо рассмотреть
        fifty = False  # Идентификатор "Полтинников" - кто иногда кидает
        cheater = {'vk_id': None, 'fifty': fifty, 'shortname': None, 'telephone': [], 'card': []}  # Запись про кидалу
        cheaters_list = []  # Список кидал
        for line in content.split('\n'):
            print('Строка : \n', line)
            if re.search(r'vk\.com', line):
                subline = line
            else:
                # Если это не vk_id, все символы в строке делаем слитно, надеясь, что получится последовательность цифр.
                subline = re.sub(r'[- +\r]', '', str(line))
            match = re.search(self.regexp_main, subline)
            if match:
                print("Найдено совпадение из регулярки: \n", match.groupdict())
                if match.lastgroup in ['vk_id', 'shortname']:
                    if cheater.get('vk_id') or cheater.get('shortname'):
                        # Запись добавляется в список, когда встречается следующая запись про кидалу.
                        # Сделано, чтобы можно было добавлять телефоны и карты конкретного кидалы.
                        # Последняя запись добавляется после цикла.
                        print('Добавляю кидалу в список. \n', cheater)
                        cheaters_list.append(cheater)
                        cheater = {'vk_id': None, 'fifty': fifty, 'shortname': None, 'telephone': [], 'card': []}
                    if match.lastgroup == 'vk_id':
                        # Если это vk_id - добавляем id в cheater.
                        cheater['vk_id'] = match[match.lastgroup]
                    elif match.lastgroup == 'shortname':
                        # Если имя - ищем vk_id и добавляем id и shortname в cheater.
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
                                cheater['shortname'] = user[0].screen_name
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
                                # VK_API возвращает shortname=vk_id, если имени нет.
                                if group[0].screen_name != cheater['vk_id']:
                                    cheater['shortname'] = group[0].screen_name
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
            time.sleep(0.05)
        # Последний в списке
        if cheater.get('vk_id'):
            print('Добавляю кидалу в список. \n', cheater)
            cheaters_list.append(cheater)

        print('Вот итоговый список:', cheaters_list, '\n')
        return cheaters_list

    async def _update_database(self, cheaters_list: str):
        """
        Принимает на вход список кидал, обновляет базу и возвращает ответ строкой.
        :return: Ответ для пользователя
        """
        for cheater in cheaters_list:
            print('Разбираем запись ', cheater, sep='\n')
            if cheater['vk_id']:
                # TODO Сделать отдельные методы для проверки наличия кидал
                if self.db.check_the_existence('vk_id', {'vk_id': cheater['vk_id'], 'fifty': cheater['fifty']}):
                    print('Такой vk_id есть!')
                elif self.db.check_the_existence('vk_id', {'vk_id': cheater['vk_id']}):
                    print('Поменялся fifty на', cheater['fifty'])
                    self.db.update_table('vk_id', 'fifty', cheater['fifty'], 'vk_id', cheater['vk_id'])
                else:
                    print('Добавляем нового кидалу')
                    self.db.add_cheater(cheater['vk_id'], cheater['fifty'])

                if cheater['shortname']:
                    if self.db.check_the_existence('shortnames',
                                                   {'shortname': cheater['shortname'],
                                                    'vk_id': cheater['vk_id']
                                                    }
                                                   ):
                        print('Такой shortname-id есть!')
                    else:
                        print('Добавляем новый shortname-id')
                        self.db.add_shortname(cheater['shortname'], cheater['vk_id'])

                if cheater['telephone']:
                    for tel in cheater['telephone']:
                        if self.db.check_the_existence('telephones', {'telephone': tel, 'vk_id': cheater['vk_id']}):
                            print('Связка телефон-id уже есть')
                        else:
                            print('Добавляем новый tel-id')
                            self.db.add_telephones([tel], cheater['vk_id'])

                if cheater['card']:
                    for card in cheater['card']:
                        if self.db.check_the_existence('cards', {'card': card, 'vk_id': cheater['vk_id']}):
                            print('Связка card-id уже есть')
                        else:
                            print('Добавляем новый card-id')
                            self.db.add_cards([card], cheater['vk_id'])
            else:
                # Пока таких не рассматриваем
                # TODO Обдумать формат записи без vk_id
                print('Запись без vk_id')
                if cheater['shortname']:
                    if self.db.check_the_existence('shortnames', {'shortname': cheater['shortname']}):
                        print('Такое имя уже есть')
                    else:
                        self.db.add_shortname(cheater['shortname'])
                if cheater['telephone']:
                    pass
                if cheater['card']:
                    pass
            print('Я обновил БД!')
        return 'Я обновил БД!'

    def check_cheater(self, parameter: str, value: str):
        """
        Проверяем наличие кидалы в БД.
        Если возвращается пустая строка, то запрос некорректно отработал.

        :return vk_id, False.
        """
        if parameter == 'vk_id':
            check_result = self.db.get_cheater_id('vk_id', {parameter: value})
        elif parameter == 'shortname':
            check_result = self.db.get_cheater_id('shortnames', {parameter: value})
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


if __name__ == '__main__':
    #  Тут будет тест
    pass

"""
Classes for VKBot
"""
import re
import requests
import time
from typing import List, Tuple, Optional, Union

import vkbottle
from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.exception_factory import VKAPIError


import database
import dialogs
import vk_keyboards

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
    DEL_CHEATER = 'del_cheater'


class VKBot(Bot):
    """
    Main bot class.
    """
    dialog_states = DialogStates

    def __init__(self, vk_token: str, db_filename: str, cheaters_filename: str):
        super().__init__(vk_token)
        self.labeler.vbml_ignore_case = True
        self.db_filename = db_filename
        self.cheaters_filename = cheaters_filename
        self.db = database.DBCheaters(self.db_filename)
        self.admins_from_db = self.db.get_admins()
        self.group_info = self.api.groups.get_by_id
        self.group_id = ''

    async def get_async_params(self):
        """
        Метод получает значения для свойств объекта класса с помощью асинхронных методов.
        """
        group_info = await self.api.groups.get_by_id()
        self.group_id = group_info[0].id

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
                                                                        fields=['screen_name']
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

    async def _update_database_from_list(self, cheaters_list: list):
        """
        Принимает на вход список кидал, обновляет базу и возвращает ответ строкой.
        :return: Ответ для пользователя
        """
        for cheater in cheaters_list:
            print('Разбираем запись ', cheater, sep='\n')
            if cheater['vk_id']:
                db_record = self.db.get_dict_from_table('vk_ids',
                                                        ['vk_id', 'fifty'],
                                                        {'vk_id': cheater['vk_id']})
                if db_record:
                    print('Такой vk_id есть!')
                    if db_record[0]['fifty'] != cheater['fifty']:
                        print('Поменялся fifty на', cheater['fifty'])
                        self.db.update_table('vk_id', {'fifty': cheater['fifty']}, {'vk_id': cheater['vk_id']})
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
            check_result = self.db.get_cheater_id('vk_ids', {parameter: value})
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

    async def is_admin(self, peer_id: int) -> bool:
        """
        Определяет, является ли пользователь админом.
        :param peer_id:
        :return:
        """
        if peer_id in self.admins_from_db or peer_id in (await self.get_group_admins()):
            return True
        else:
            return False

    async def send_message_to_admins(self, message: str = 'Что-то', message_forward_id: int = None):
        """
        Метод посылает всем админам какое-то сообщение.

        :param message: Сообщение для администраторов группы.
        :param message_forward_id : пересылаемое сообщение.
        :return: None
        """
        vk_admin_ids = self.admins_from_db
        message_text = message
        await self.api.messages.send(
            message=message_text,
            user_ids=vk_admin_ids,
            forward_messages=message_forward_id,
            random_id=0,
        )

    async def update_db_screen_name(self, vk_id: str, screen_name: str = None):
        """
        Метод обновляет screen_name в БД для заданного vk_id.

        Все старые screen_name помечаются как changed=True.

        Если передано имя - берется оно, если нет - запрашивается новое имя и помещается в базу.

        :param screen_name: имя, на которое надо изменить БД.
        :param vk_id: id, который необходимо обновить.
        :return: получилось или нет
        """
        if not screen_name:
            user_info = await self.api.users.get([vk_id], fields=['screen_name'])
            screen_name = user_info[0].screen_name
        self.db.update_table('screen_names', {'changed': True}, {'screen_name': screen_name})
        self.db.add_screen_name(screen_name, vk_id)

    async def get_from_api_id_screen_name(self, id_name: str = None) -> Optional[Tuple[str, str, bool]]:
        """
        Метод возвращает id и screen_name в виде кортежа из двух значений.

        :param id_name: vk_id или screen_name
        :return: vk_id, screen_name, deleted
        """
        result_vk_id = None
        result_screen_name = None
        result_banned = False
        users_info = await self.api.users.get(id_name, fields=['screen_name'])
        if users_info:
            if users_info[0].deactivated:
                # Если пользователь забанен.
                result_banned = True
            result_vk_id = 'id' + str(users_info[0].id)
            result_screen_name = users_info[0].screen_name
        else:
            try:
                group = await self.api.groups.get_by_id(group_id=id_name,
                                                        fields=['screen_name']
                                                        )
                if group[0].type.value == 'group':
                    group_type = 'club'
                elif group[0].type.value == 'page':
                    group_type = 'public'
                elif group[0].type.value == 'event':
                    group_type = 'event'
                else:
                    group_type = 'club'
                result_vk_id = group_type + str(group[0].id)
                result_screen_name = group[0].screen_name
            except VKAPIError[100]:
                pass
        return result_vk_id, result_screen_name, result_banned

    async def get_group_admins(self, group_id: str = None) -> List[str]:
        """
        Метод возвращает список администраторов группы.
        Если имя группы не переданно - берется своя группа (от имени котрой запущен бот).

        :param group_id: id или screen_name группы.
        :return: Список администраторов.
        """
        if group_id:
            members = await self.api.groups.get_members(group_id=group_id, filter='managers')
        else:
            group_id = str((await self.group_info())[0].id)
            members = await self.api.groups.get_members(group_id=group_id, filter='managers')
        result = []
        for member in members.items:
            result.append(str(member.id))
        result.append(self.admins_from_db)
        return result

    async def answer_to_peer(self, text: str, peer_id: int, new_state: BaseStateGroup = None):
        """
        Метод отвечает за ответ пользователю. На вход принимает id пользователя, новый статус и текст сообщения.
        Изменяет StateDispenser, генерирует клавиатуру и отправляет пользователю ответ.

        :param text: Текст для ответа.
        :param new_state: Новый статус.
        :param peer_id: vk_id
        """
        if new_state:
            await self.state_dispenser.set(peer_id, new_state)
        else:
            if await self.state_dispenser.get(peer_id):
                await self.state_dispenser.delete(peer_id)
        keyboard = vk_keyboards.get_keyboard(new_state, await self.is_admin(peer_id))
        await self.api.messages.send(
            peer_id=peer_id,
            message=text,
            keyboard=keyboard,
            random_id=0,
        )


if __name__ == '__main__':
    #  Тут будет тест
    pass

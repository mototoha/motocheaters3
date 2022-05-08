"""
Classes for VKBot
"""
import re

from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import (
    AttachmentTypeRule,
    FromPeerRule,
)
from vkbottle.exception_factory import VKAPIError

import config


class VKBot(Bot):
    """
    Main bot class.
    """
    def __init__(self, bot_params: config.BotParams):
        super().__init__(bot_params.vk_token)
        self.regexp_main = (
            r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+)'
            r'|((https://|http://)?(m\.)?vk.com/){1}(?P<shortname>([a-z]|[A-Z]|[0-9]|_)+)'
            r'|(?P<card>\d{16})'
            r'|\+?(?P<telephone>\d{10,15})'
        )

    async def get_cheaters_list_from_file(self, content):
        """
        Функция получает на вход текст из файла и возвращает списком кидал.
        Если по дороге возникает исключение, не позволяющее нормально продолжить работу - возвращает текст.

        :param content: Текст из файла.
        :return: List кидал.
        """
        fifty = False  # Идентификатор "Полтинников" - кто ингода кидает
        cheater = {'vk_id': None, 'fifty': False, 'shortname': None, 'telephone': [], 'card': []}  # Запись про кидалу
        cheaters_list = []  # Список кидал
        for line in content.split('\n'):
            print('Строка : \n', line)
            subline = re.sub(r'[ +-]', '', str(line).replace('\r', ''))  # Обрезаем строку от лишних символов
            match = re.search(regexp_main, subline)  # Поиск по регулярке
            if match:
                print("Найдено совпадение из регулярки: \n", match.groupdict())
                if match.lastgroup in ['vk_id', 'shortname']:
                    if cheater.get('vk_id'):  # Если новый кидала - записываем старого и делаем новую пустую запись
                        print('Добавляю кидалу в список. \n', cheater)
                        cheaters_list.append(cheater)
                        cheater = {'vk_id': None, 'fifty': False, 'shortname': None, 'telephone': [], 'card': []}
                    user = None
                    group = None
                    try:
                        user = await self.api.users.get(user_ids=match[match.lastgroup],
                                                        fields='screen_name'
                                                        )
                        print('Запрос юзера:\n', user)
                    except VKAPIError[6]:
                        print('Слишком много запросов, повтори через полчаса')
                        return "VKAPIError_6 Слишком много запросов, повтори через полчаса"

                    if not user:
                        try:
                            group = await self.api.groups.get_by_id(group_id=match[match.lastgroup],
                                                                    fields='screen_name'
                                                                    )
                            print('Запрос группы:\n', group)
                        except VKAPIError[100]:
                            print('Группа не найдена')
                        except VKAPIError[6]:
                            print('Слишком много запросов, повтори через полчаса')
                            return "VKAPIError_6 Слишком много запросов, повтори через полчаса"

                    if user:
                        cheater['vk_id'] = 'id' + str(user[0].id)
                        if user[0].screen_name != cheater['vk_id']:
                            cheater['shortname'] = user[0].screen_name
                    elif group:
                        if group[0].type.value == 'group':
                            group_type = 'club'
                        elif group[0].type.value == 'page':
                            group_type = 'public'
                        elif group[0].type.value == 'event':
                            group_type = 'event'
                        else:
                            group_type = 'club'
                        cheater['vk_id'] = group_type + str(group[0].id)
                        if group[0].screen_name != cheater['vk_id']:
                            cheater['shortname'] = group[0].screen_name
                    else:
                        print('В файле попался неправильный идентификатор, не могу понять, кто это: ', line)
                        print('Возможно, страница удалена \n ')
                    cheater['fifty'] = fifty
                else:
                    print(cheater)
                    cheater.setdefault(match.lastgroup, []).append(match[match.lastgroup])
            elif subline == 'fifty':
                fifty = True
                print('Далее идут полтиники')
            else:
                print('Непонятная строка \n')
        # Последний в списке
        if cheater.get('vk_id'):
            print('Добавляю кидалу в список. \n', cheater)
            cheaters_list.append(cheater)

        print('Вот итоговый список:', cheaters_list, '\n')
        return cheaters_list


regexp_main = (
        r'((https://|http://)?(m\.)?vk.com/|^){1}(?P<vk_id>(id|club|public|event)\d+)'
        r'|((https://|http://)?(m\.)?vk.com/){1}(?P<shortname>([a-z]|[A-Z]|[0-9]|_)+)'
        r'|(?P<card>\d{16})'
        r'|\+?(?P<telephone>\d{10,15})'
    )


class DialogStates(BaseStateGroup):
    """
    Dialog levels.
    """
    MAIN_STATE = 0
    TELL_ABOUT_CHEATER = 1
    ADMIN_MENU = 10

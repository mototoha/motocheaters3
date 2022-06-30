"""
Кастомные правила для работы бота.
"""
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule
from vkbot import VKBot


class AdminUserRule(ABCRule[Message]):
    """
    Класс описывает правило проверки пользователя на админа.
    Пользователь должен содержаться в списке админов группы.
    """
    def __init__(self, bot: VKBot):
        self.bot = bot

    async def check(self, event: Message) -> bool:
        """
        Метод сравнивает текущего пользователя с админами группы.
        Если совпадет - возвращает True.

        :param event: Сообщение от пользователя.
        :return: bool
        """
        result = str(event.from_id) in self.bot.group_admins
        return result

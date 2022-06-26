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
        Метод запрашивает админов группы и сравнивает текущего с ними.
        Если совпадет - возвращает True.

        :param event: Сообщение от пользователя.
        :return: bool
        """
        result = await self.bot.is_admin(event.from_id)
        return result

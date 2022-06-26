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
        self.group_id = bot.group_id

    async def check(self, event: Message) -> bool:
        """
        Метод запрашивает админов группы и сравнивает текущего с ними.
        Если совпадет - возвращает True.

        :param event: Сообщение от пользователя.
        :return: bool
        """
        result = False
        members_api = await self.bot.api.groups.get_members(group_id=self.bot.group_id, filter='managers')
        members = []
        for member in members_api.items:
            members.append(str(member.id))
        members += self.bot.admins_from_db
        if event.from_id in members:
            result = True
        return result

"""
Rules for messages
"""

from typing import Union
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule

class MyRule(ABCRule[Message]):
    def __init__(self, dialog_position: str = ''):
        self.dialog_position = dialog_position

    async def check(self, event: Message) -> bool:
        return len(event.text) < self.lt
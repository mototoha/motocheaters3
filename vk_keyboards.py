"""
JSON для клавиатур
"""

from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle import BaseStateGroup
from vkbot import DialogStates, AdminStates


def get_keyboard(menu_level: BaseStateGroup = None, is_admin: bool = False) -> str:
    """
    Возвращает json клавиатуры.

    :param menu_level: для какого меню клавиатура.
    :param is_admin: Если клавиатура предусматривает опционально админские кнопки, ставить True.
    :return: json клавиатуры.
    """
    # Главная клавиатура в конце.
    # Сделано специально, чтобы пользователь не оставался без клавиатуры.
    if menu_level == DialogStates.TELL_ABOUT_CHEATER_STATE:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"tell_about_cheater": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)

    elif menu_level == AdminStates.MAIN:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Добавить кидалу", payload='{"admin": "add_cheater"}'),
                     color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("Удалить кидалу", payload='{"admin": "del_cheater"}'),
                     color=KeyboardButtonColor.NEGATIVE)
        keyboard.row()
        keyboard.add(Text("Разослать всем чо-то", payload='{"admin": "mass_sending"}'),
                     color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("Вернуться на главную", payload='{"admin": "return_to_main"}'),
                     color=KeyboardButtonColor.NEGATIVE)

    elif menu_level == AdminStates.SPAM:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"admin": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)

    elif menu_level == AdminStates.ADD_CHEATER:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Добавить", payload='{"admin": "add"}'),
                     color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("Передумал", payload='{"admin": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)

    elif menu_level == AdminStates.DEL_CHEATER:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"admin": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
    elif menu_level == AdminStates.DEL_CHEATER_COMMIT:
        keyboard = Keyboard(one_time=False, inline=True)
        keyboard.add(Text("Да", payload='{"del_cheater": "yes"}'),
                     color=KeyboardButtonColor.NEGATIVE)
        keyboard.add(Text("Нет", payload='{"del_cheater": "no"}'),
                     color=KeyboardButtonColor.POSITIVE)
    else:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Рассказать про кидалу", payload='{"main": "tell_about_cheater"}'),
                     color=KeyboardButtonColor.PRIMARY)
        keyboard.row()
        keyboard.add(Text("Помочь нам", payload='{"main": "help_us"}'),
                     color=KeyboardButtonColor.POSITIVE)
        keyboard.row()
        keyboard.add(Text("Как проверить", payload='{"main": "how_check"}'),
                     color=KeyboardButtonColor.SECONDARY)
        if is_admin:
            keyboard.row()
            keyboard.add(Text("Админ меню", payload='{"main": "admin"}'),
                         color=KeyboardButtonColor.NEGATIVE)

    return keyboard.get_json()

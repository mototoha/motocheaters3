"""
JSON для клавиатур
"""

from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbot import DialogStates


def get_keyboard(menu_level: DialogStates = None, is_admin: bool = False) -> str:
    """
    Возвращает json клавиатуры.
    :param menu_level: для какого меню клавиатура.
    :param is_admin: нужны ли админские кнопки.
    :return: json клавиатуры.
    """
    # Клавиатура главного меню в конце
    if menu_level == DialogStates.TELL_ABOUT_CHEATER_STATE:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"tell_about_cheater": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
    elif (menu_level == DialogStates.ADMIN_MENU_STATE) & is_admin:
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
    elif (menu_level == DialogStates.ADMIN_SPAM_STATE) & is_admin:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"admin": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
    elif (menu_level == DialogStates.ADMIN_ADD_CHEATER) & is_admin:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"admin": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
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

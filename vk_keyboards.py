"""
JSON для клавиатур
"""

from vkbottle import Keyboard, KeyboardButtonColor, Text


def get_keyboard(menu_level: str, is_admin: bool) -> str:
    """
    Возвращает json клавиатуры.
    :param menu_level: для какого меню клавиатура.
    :param is_admin: нужны ли админские кнопки.
    :return: json клавиатуры.
    """
    # Главная клавиатура в конце if'ов
    if menu_level == 'tell_about_cheater':
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Передумал", payload='{"tell_about_cheater": "main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
    elif (menu_level == 'admin') & is_admin:
        keyboard = Keyboard(one_time=False, inline=False)
        keyboard.add(Text("Разослать всем чо-то", payload='{"admin": "mass_sending"}'),
                     color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("Вернуться на главную", payload='{"admin": "return_to_main"}'),
                     color=KeyboardButtonColor.NEGATIVE)
    elif (menu_level == 'mass_sending') & is_admin:
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


# MAIN KB
keyboard_main = Keyboard(one_time=False, inline=False)
keyboard_main.add(Text("Рассказать про кидалу", payload='{"main": "tell_about_cheater"}'),
                  color=KeyboardButtonColor.PRIMARY)
keyboard_main.row()
keyboard_main.add(Text("Помочь нам", payload='{"main": "help_us"}'),
                  color=KeyboardButtonColor.POSITIVE)
keyboard_main.row()
keyboard_main.add(Text("Как проверить", payload='{"main": "how_check"}'),
                  color=KeyboardButtonColor.SECONDARY)
keyboard_main.get_json()

# TELL ABOUT CHEATER KB
keyboard_return_to_main = Keyboard(one_time=False, inline=False)
keyboard_return_to_main.add(Text("Передумал", payload='{"tell_about_cheater": "main"}'),
                            color=KeyboardButtonColor.NEGATIVE)
keyboard_return_to_main.get_json()

# ADMIN KB
keyboard_admin = Keyboard(one_time=False, inline=False)
keyboard_admin.add(Text("Разослать всем чо-то", payload='{"admin": "mass_sending"}'),
                   color=KeyboardButtonColor.POSITIVE)
keyboard_admin.add(Text("Вернуться на главную", payload='{"admin": "return_to_main"}'),
                   color=KeyboardButtonColor.NEGATIVE)
keyboard_admin.get_json()

keyboard_admin_spam = Keyboard(one_time=False, inline=False)
keyboard_admin_spam.add(Text("Передумал", payload='{"admin": "main"}'),
                        color=KeyboardButtonColor.NEGATIVE)
keyboard_admin_spam.get_json()

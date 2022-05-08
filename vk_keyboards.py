"""
JSON для клавиатур
"""

from vkbottle import Keyboard, KeyboardButtonColor, Text

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

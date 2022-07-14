"""
тут находятся уровни диалога
"""
from vkbottle import BaseStateGroup


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
    DEL_CHEATER_CHOICE = 'del_cheater_choice'
    DEL_CHEATER_COMMIT = 'del_cheater_commit'
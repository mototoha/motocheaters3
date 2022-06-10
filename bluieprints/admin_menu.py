"""
Blueprint для админ меню.
"""

from vkbot import (
    AdminStates,
    REGEXP_MAIN,
)

from vkbottle.bot import Blueprint, Message
from vkbottle.dispatch.rules.base import (
    AttachmentTypeRule,
    FromPeerRule,
    PayloadRule,
    CommandRule,
    StateRule,
    StateGroupRule,
)

bp = Blueprint()
bp.labeler.vbml_ignore_case = True
bp.labeler.auto_rules.append(StateGroupRule(AdminStates))


@bp.on.message(
    FromPeerRule(FromPeerRule(bp.api.groups.get_members())),
    CommandRule('Админ меню') | PayloadRule({"main": "admin"}),
    StateRule(),
)
async def admin_menu_handler(message: Message):
    """
    Переход в админское меню.
    """
    new_state = vkbot.AdminStates.MAIN
    await bot.state_dispenser.set(message.from_id, new_state)
    keyboard = vk_keyboards.get_keyboard(new_state)
    await message.answer(
        message=dialogs.admin_menu,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.MAIN),
    PayloadRule({"admin": "return_to_main"}),
)
async def return_to_main_handler(message: Message):
    """
    Возврат из админского меню.
    """
    await bot.state_dispenser.delete(message.peer_id)
    answer_message = dialogs.return_to_main
    keyboard = vk_keyboards.get_keyboard(None)
    await message.answer(
        answer_message,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    PayloadRule({"admin": "mass_sending"}),
    StateRule(vkbot.AdminStates.MAIN),
)
async def spam_handler(message: Message):
    """
    Перед рассылкой.
    """
    new_state = vkbot.AdminStates.SPAM
    await bot.state_dispenser.set(message.from_id, new_state)
    answer_message = dialogs.spam_header
    keyboard = vk_keyboards.get_keyboard(new_state)
    await message.answer(
        answer_message,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.SPAM),
)
async def spam_handler(message: Message):
    """
    Начало рассылки всем членам группы.
    """
    new_state = vkbot.AdminStates.MAIN
    group_info = await bot.api.groups.get_by_id()
    group_id = group_info[0].id
    members = await bot.api.groups.get_members(group_id=group_id)
    answer_message = dialogs.spam_send + message.text + '\n' + str(members)
    keyboard = vk_keyboards.get_keyboard(new_state)
    await bot.state_dispenser.set(message.from_id, new_state)
    await message.answer(
        answer_message,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.MAIN),
    PayloadRule({"admin": "add_cheater"}),
)
async def add_cheater_handler(message: Message):
    """
    Админ меню. Кнопка "Добавить кидалу".
    """
    new_state = vkbot.AdminStates.ADD_CHEATER_ID
    await bot.state_dispenser.set(message.peer_id, new_state)
    answer_message = dialogs.add_cheater_id
    keyboard = vk_keyboards.get_keyboard(new_state)
    await message.answer(
        message=answer_message,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.ADD_CHEATER_ID)
)
async def add_cheater_id_handler(message: Message):
    """
    Админ прислал vk_id кидалы.
    """
    match = re.search(REGEXP_MAIN, message.text)
    new_state = vkbot.AdminStates.ADD_CHEATER_ID
    if match:
        if match.lastgroup in ['vk_id', 'shortname']:
            answer_message = dialogs.add_cheater_ok
            new_state = vkbot.AdminStates.MAIN
            await bot.state_dispenser.set(message.peer_id, new_state)
        else:
            answer_message = dialogs.add_cheater_error_value
    else:
        answer_message = dialogs.add_cheater_error_value
    await message.answer(
        message=answer_message,
        keyboard=vk_keyboards.get_keyboard(new_state)
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.ADD_CHEATER),
    PayloadRule({"admin": "main"})
)
async def return_from_add_cheater_handler(message: Message):
    """
    Админ меню. Передумал добавлять кидалу.
    """
    new_state = vkbot.AdminStates.MAIN
    await bot.state_dispenser.set(message.peer_id, new_state)
    answer_message = dialogs.admin_menu
    keyboard = vk_keyboards.get_keyboard(new_state)
    await message.answer(
        message=answer_message,
        keyboard=keyboard,
    )


@bot.on.message(
    FromPeerRule(bot.vk_admin_id),
    StateRule(vkbot.AdminStates.ADD_CHEATER),
)
async def add_cheater_id(message: Message):
    """
    Добавление кидалы. Ввод ID.
    """
    new_state = vkbot.AdminStates.ADD_CHEATER_ID
    await bot.state_dispenser.set(message.from_id, new_state)
    answer_message = dialogs


@bot.on.message(StateGroupRule(vkbot.AdminStates))
async def common_admin_handler(message: Message):
    """
    Любая другая хрень в админском меню.
    """
    return dialogs.admin_common
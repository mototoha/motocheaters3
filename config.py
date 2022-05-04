"""
Global variables.
Config file check
"""

# Parameters of config file
# Config filename
config_json = 'config.json'

# Config file content
json_template = {
    'db_filename': 'str',
}

# What must contain bot_param dict to start bot
bot_params_template = {
        'db_filename': '',  # From json
        'vk_token': '',  # From DB
        'vk_group_id': '',  # From DB
        'cheaters_filename': '',  # From DB
        'vk_admin_id': [],  # From DB
    }

# From where get bot parameters
get_bot_params = {
    'json': ['db_filename'],
    'DB_params': ['vk_token', 'vk_group_id', 'cheaters_filename'],
    'DB_admins': ['vk_admin_id']
    }

# DB template
db_tables = {
    "vk_id": {
        "pk": "int",
        "id": "str",
        "fifty": "bool"
    },
    "shortnames": {
        "pk": "int",
        "shortname": "str",
        "id": "str"
    },
    "telephones": {
        "pk": "int",
        "telephone": "str",
        "id": "str"
    },
    "cards": {
        "pk": "int",
        "card": "str",
        "id": "str"
    },
    "parameters": {
        "param": "str",
        "value": "str"
    },
    "admins": {
        "pk": "int",
        "vk_id": "str"
    },
    "user_dialogs": {
        "pk": "int",
        "vk_id": "str",
        "dialog_position": "str"
    },
}

# These parameters must be in table
db_table_config_params = [
    'vk_token',
    'vk_group_id',
    'cheaters_filename',
]

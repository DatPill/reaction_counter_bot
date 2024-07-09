import ast
from dotenv import dotenv_values
from typing import Final


config = dotenv_values()

SESSION: Final[str] = str(config['SESSION'])
API_ID: Final[str] = str(config['API_ID'])
API_HASH: Final[str] = str(config['API_HASH'])
ADMINS: Final[set] = ast.literal_eval(config['ADMINS'])

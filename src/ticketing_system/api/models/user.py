from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    discord_id: str
    # avatar: Union[str, None] = None
    # banner: Union[str, None] = None
    # banner_color: Union[str, None] = None
    # banned: bool

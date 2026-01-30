import datetime
from typing import Optional

import flet as ft

from core.defs.common import AuthToken


class AuthorizationProvider:

    @classmethod
    async def authorize(cls, auth_token: AuthToken):
        await ft.SharedPreferences().set("ba-authorization", auth_token.authorization)
        await ft.SharedPreferences().set("ba-cookie", auth_token.cookie)
        await ft.SharedPreferences().set("ba-expires-in", str(auth_token.expires_in))

    @classmethod
    def validate_login(cls, value) -> Optional[AuthToken]:
        auth_token = AuthToken.from_str(value)
        return auth_token

    @classmethod
    async def get_token_valid_to(cls) -> Optional[datetime.datetime]:
        expires_in = await ft.SharedPreferences().get("ba-expires-in")
        if not expires_in:
            return None
        return datetime.datetime.fromtimestamp(int(expires_in), datetime.timezone.utc)

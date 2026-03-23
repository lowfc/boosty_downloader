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

    @classmethod
    async def get_authorization_if_valid(cls) -> Optional[AuthToken]:
        expires_in = await ft.SharedPreferences().get("ba-expires-in")
        if not expires_in:
            return None
        expires_date = datetime.datetime.fromtimestamp(
            int(expires_in), datetime.timezone.utc
        )
        if datetime.datetime.now(datetime.timezone.utc) < expires_date:
            return AuthToken(
                authorization=await ft.SharedPreferences().get("ba-authorization"),
                cookie=await ft.SharedPreferences().get("ba-cookie"),
                expires_in=int(expires_in),
            )
        return None

import logging
from functools import cached_property

from django.conf import settings
from jose import exceptions, jwt
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from app.core.utils import get_auth0_user_data, get_rsa_keys_from_auth0


class Auth0TokenAuthentication(BaseAuthentication):
    """
    Auth0 token based authentication.
    Frontend should authenticate by passing the token key in the 'Authorization':
        Authorization: Bearer <token data>
    """

    auth_prefix = "Bearer"

    @cached_property
    def jwk_keys(self):
        """Implements lazy loading of RSA keys and cache them."""
        return get_rsa_keys_from_auth0()

    def authenticate(self, request):
        """
        Check if user access token valid.
        Give access to the endpoint if token valid and user exists.
        If token is not valid or not provided - return AnonymousUser
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser

        User = get_user_model()

        access_token = self.__get_access_token_from_header(request=request)

        if not access_token:
            return AnonymousUser(), None

        decoded_token, is_valid = self.__verify_auth0_token(access_token=access_token)

        if not is_valid:
            raise exceptions.AuthenticationFailed("Provided token is not valid")

        auth0_username = decoded_token["sub"].split("|")[1]
        user = User.objects.filter(username=auth0_username).last()

        if not user:
            user_data = get_auth0_user_data(access_token=access_token)
            email = user_data.get("email")

            if not email:
                raise exceptions.AuthenticationFailed("Email was not provided")

            first_name = user_data.get("given_name")
            middle_name = user_data.get("middle_name")
            last_name = user_data.get("family_name")

            user, _ = User.objects.get_or_create(email=email, username=auth0_username)

            if change_first := first_name and not user.first_name:
                user.first_name = first_name
            if change_middle := middle_name and not user.middle_name:
                user.middle_name = middle_name
            if change_last := last_name and not user.last_name:
                user.last_name = last_name
            if any([change_first, change_last, change_middle]):
                user.save()

        return user, access_token

    def __get_access_token_from_header(self, request) -> bytes | None:
        """Check `Authorization` header and try to get access token."""
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.auth_prefix.lower().encode():
            return None

        if len(auth) == 1 or len(auth) > 2:
            raise AuthenticationFailed("Authorizarion header formed incorrectly")

        return auth[1]

    def __verify_auth0_token(self, access_token: str) -> tuple[dict, bool]:
        """Try to verify user access token accordingly to RSA key."""
        rsa_key = self.__get_auth0_rsa_key(access_token=access_token)  # type: ignore

        if rsa_key:
            try:
                return (
                    jwt.decode(
                        token=access_token,
                        key=rsa_key,
                        algorithms=settings.AUTH0_ALGORITHMS,
                        audience=settings.AUTH0_API_AUDIENCE,
                        issuer=settings.AUTH0_ISSUER,
                    ),
                    True,
                )
            except exceptions.ExpiredSignatureError as error:
                logging.error(error)
                raise AuthenticationFailed("JWT token has expired")
            except jwt.JWTClaimsError as error:
                logging.error(error)
                raise AuthenticationFailed("JWT token has invalid claims")
            except Exception as error:
                logging.error(error)
                raise AuthenticationFailed("JWT token is invalid")

        return {}, False

    def __get_auth0_rsa_key(self, access_token: str) -> dict:
        """Get auth0 RSA key."""
        try:
            unverified_header = jwt.get_unverified_header(token=access_token)
        except Exception:
            raise AuthenticationFailed("Error decoding token headers")

        rsa_key = {}

        for key in self.jwk_keys["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        return rsa_key

"""Users module."""


from typing import Protocol


class Registry(Protocol):
    """Users registry."""

    def signup(self, username: str, password: str):
        """Signup new user.

        Args:
            username: user login identificator.
            password: user auth password.
        """
        ...

    def login(self, username: str, password: str) -> str:
        """Login registered user.

        Args:
            username: user login identificator.
            password: user password to match with the one in registry.
        Returns:
            Access auth token.
        """
        ...

    def authenticate(self, token: str) -> str:
        """Authenticate user with a token.

        Args:
            token: auth token given on user login.
        Returns:
            Aunthenticated user name.
        """
        ...

    def track_activity(self, username: str):
        """Track user activity.

        Args:
            username: user login identificator.
        """
        ...

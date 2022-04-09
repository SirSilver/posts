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

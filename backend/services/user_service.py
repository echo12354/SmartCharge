"""User business service."""

from config.settings import DEFAULT_USERS
from models.user import User


class UserService:
    def __init__(self):
        self.users: dict[str, User] = {}
        for item in DEFAULT_USERS:
            self.users[item["username"]] = User(
                username=item["username"],
                password=item["password"],
                role=item["role"],
            )

    def register(self, username: str, password: str, role: str = "user"):
        if not username or not password:
            raise ValueError("username and password are required")
        if username in self.users:
            raise ValueError("username already exists")
        if role not in ("user", "admin"):
            raise ValueError("role must be user or admin")
        user = User(username=username, password=password, role=role)
        self.users[username] = user
        return user

    def login(self, username: str, password: str):
        user = self.users.get(username)
        if not user or not user.verify_password(password):
            raise ValueError("invalid username or password")
        user.mark_login()
        return user

    def get_user(self, username: str) -> User | None:
        return self.users.get(username)

    def require_admin(self, username: str):
        user = self.get_user(username)
        if not user or not user.is_admin():
            raise PermissionError("admin permission required")
        return user


user_service = UserService()


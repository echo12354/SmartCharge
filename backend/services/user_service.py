"""用户服务。

负责注册、登录和管理员权限判断，用户数据优先使用 MySQL，失败时回退默认内存用户。
"""

from config.settings import DEFAULT_USERS
from models.user import User
from repositories.user_repository import UserRepository


class UserService:
    """用户业务入口。

    `self.users` 保留内存兜底，保证数据库不可用时基础登录流程仍能演示。
    """

    def __init__(self):
        self.users: dict[str, User] = {}
        self.repository = UserRepository()
        for item in DEFAULT_USERS:
            self.users[item["username"]] = User(
                username=item["username"],
                password=item["password"],
                role=item["role"],
            )
        self._load_users_from_database()

    def register(self, username: str, password: str, role: str = "user"):
        """注册用户，用户名在内存或数据库中已存在时拒绝创建。"""
        if not username or not password:
            raise ValueError("username and password are required")
        existing = self.get_user(username)
        if existing:
            raise ValueError("username already exists")
        if role not in ("user", "admin"):
            raise ValueError("role must be user or admin")
        user = User(username=username, password=password, role=role)
        self.users[username] = user
        self._save_user_to_database(user)
        return user

    def login(self, username: str, password: str):
        """登录成功后记录最后登录时间，并尽量同步到 MySQL。"""
        user = self.get_user(username)
        if not user or not user.verify_password(password):
            raise ValueError("invalid username or password")
        user.mark_login()
        self._update_last_login_in_database(user)
        return user

    def get_user(self, username: str) -> User | None:
        if not username:
            return None
        user = self.users.get(username)
        if user:
            return user
        user = self._get_user_from_database(username)
        if user:
            self.users[user.username] = user
        return user

    def require_admin(self, username: str):
        """管理员接口调用前的角色校验。"""
        user = self.get_user(username)
        if not user or not user.is_admin():
            raise PermissionError("admin permission required")
        return user

    def _load_users_from_database(self):
        try:
            for user in self.repository.list_users():
                self.users[user.username] = user
        except Exception:
            pass

    def _get_user_from_database(self, username: str) -> User | None:
        try:
            return self.repository.get_user(username)
        except Exception:
            return None

    def _save_user_to_database(self, user: User):
        try:
            self.repository.create_user(user)
        except Exception:
            pass

    def _update_last_login_in_database(self, user: User):
        try:
            self.repository.update_last_login(user.username, user.last_login)
        except Exception:
            pass


user_service = UserService()


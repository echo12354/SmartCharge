"""用户模型。

表示系统登录主体，角色用于区分普通用户和管理员。
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """用户账号信息。

    `role` 为 `admin` 时具备管理员权限，普通用户只能操作自己的充电请求和账单。
    """

    username: str
    password: str
    role: str = "user"
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None

    def verify_password(self, password: str) -> bool:
        return self.password == password

    def mark_login(self):
        self.last_login = datetime.now()

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self):
        return {
            "username": self.username,
            "role": self.role,
            "type": self.role,
            "createdAt": self.created_at.isoformat(),
            "lastLogin": self.last_login.isoformat() if self.last_login else None,
        }


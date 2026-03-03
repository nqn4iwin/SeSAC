from typing import Dict, Any
from app.exceptions import EmailNotAllowedNameExistsError

from app.repository.user_repo import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _valid_email(self, email: str) -> bool:
        return True

    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        if not self._valid_email(email):
            raise ValueError("Invalid email format")
        if email == "admin@example.com":
            raise EmailNotAllowedNameExistsError(email)
        # save 추가
        user = self.user_repo.save(name=name, email=email)

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": str(user.created_at),
        }

    def get_user(self, user_id: int) -> Dict[str, Any]:
        user = self.user_repo.find_by_id(user_id=user_id)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": str(user.created_at),
        }

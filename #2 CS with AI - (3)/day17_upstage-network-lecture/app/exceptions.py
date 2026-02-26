class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")


class EmailNotAllowedNameExistsError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} not allowed")
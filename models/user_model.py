# Модели пользователей

class User:
    def __init__(self, user_id, username, first_name, last_name):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, first_name={self.first_name}, last_name={self.last_name})"

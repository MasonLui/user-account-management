import os
from fastlite import database, NotFoundError

os.makedirs('data', exist_ok=True)

db = database('data/accounts.db')


class User:
    username: str
    email: str
    pwd: str
    is_admin: bool
    archived: bool
    created_at: str


users = db.create(User, pk='username', transform=True)

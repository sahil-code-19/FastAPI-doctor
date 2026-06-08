import sqlite3


# Parameterized query — safe
def get_user_safe(db, user_id):
    db.execute("SELECT * FROM users WHERE id = ?", (user_id,))


# Static SQL string — safe (no interpolation)
def get_all_users(db):
    db.execute("SELECT * FROM users")


# F-string but not SQL — safe
def log_action(user_id, action):
    print(f"User {user_id} performed {action}")


# Slightly different formatting string, not SQL
def format_message(name):
    return f"Hello, {name}!"

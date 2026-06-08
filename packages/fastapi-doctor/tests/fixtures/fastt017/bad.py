# F-string SQL — injection risk
def get_user_bad(db, user_id):
    db.execute(f"SELECT * FROM users WHERE id = {user_id}")


# F-string INSERT
def create_user(db, name, email):
    db.execute(f"INSERT INTO users (name, email) VALUES ({name}, {email})")


# F-string UPDATE
def update_user(db, user_id, name):
    cursor.execute(f"UPDATE users SET name = {name} WHERE id = {user_id}")


# F-string DELETE
def delete_user(db, user_id):
    db.execute(f"DELETE FROM users WHERE id = {user_id}")


# F-string with raw connection
def raw_query(conn, table):
    conn.execute(f"SELECT * FROM {table}")

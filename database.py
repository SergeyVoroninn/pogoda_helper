import sqlite3

def init_database():
    conn = sqlite3.connect('pogoda_helper.db')
    cursor = conn.cursor()
    # Включаем поддержку Foreign Keys в SQLite (по умолчанию она выключена)
    cursor.execute("PRAGMA foreign_keys = ON;")

    user_db_query = """
    CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    sex VARCHAR(255),
    city VARCHAR(255),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP 
    )
    """

    user_dialog_query = """
    CREATE TABLE IF NOT EXISTS user_dialog (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sender VARCHAR(255) NOT NULL,
    message TEXT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
    )
    """

    cursor.execute(user_db_query)
    cursor.execute(user_dialog_query)

    conn.commit()

    cursor.close()
    conn.close()
     
def upsert_user_profile(user_id: int, name: str = None, sex: str = None, city: str = None):
    conn = sqlite3.connect('pogoda_helper.db')
    cursor = conn.cursor()
    
    query = """
    INSERT INTO user_profiles (user_id, name, sex, city, timestamp)
    VALUES (:user_id, :name, :sex, :city, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
        name = COALESCE(:name, name),
        sex = COALESCE(:sex, sex),
        city = COALESCE(:city, city),
        timestamp = CURRENT_TIMESTAMP;
    """

    data = {
        "user_id": user_id,
        "name": name,
        "sex": sex,
        "city": city
    }
    
    # Передаем запрос и словарь с данными
    cursor.execute(query, data)
    
    conn.commit()
    cursor.close()
    conn.close()

def add_dialog_message(user_id: int, sender: str, message: str):
    conn = sqlite3.connect('pogoda_helper.db')
    cursor = conn.cursor()
    
    query = """
    INSERT INTO user_dialog (user_id, sender, message, timestamp)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """
    cursor.execute(query, (user_id, sender, message))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_profile(user_id: int):
    conn = sqlite3.connect('pogoda_helper.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT *
    FROM user_profiles
    WHERE user_id == ? 
    """
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    if row:
        output = dict(row)
    else:
        output = {}
        
    cursor.close()
    conn.close()

    return output

if __name__ == '__main__':
    init_database()
    upsert_user_profile(1,'Serega', 'male', 'Novosibirsk')
    add_dialog_message(1,'user','test')
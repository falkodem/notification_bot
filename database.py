import sqlite3

from consts import db_path


def setup_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            notification_id INTEGER,
            name TEXT,
            notification_datetime DATETIME,
            periodicity TEXT
        )
    """)
    conn.commit()
    conn.close()


def db_write_notification(chat_id, name, notification_datetime, periodicity):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("BEGIN TRANSACTION")
    cursor.execute(
        "SELECT COALESCE(MAX(notification_id), 0) + 1 FROM notifications WHERE chat_id = ?",(chat_id,)
        )
    next_note_id = cursor.fetchone()[0]
    cursor.execute(
            "INSERT INTO notifications (chat_id, notification_id, name, notification_datetime, periodicity)"
            "VALUES (?, ?, ?, ?, ?)",
            (chat_id, next_note_id, name, notification_datetime, periodicity)
        )
    conn.commit()
    conn.close()


def db_update_notification(chat_id, notification_id, notification_datetime):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET notification_datetime = ? "
        "WHERE chat_id = ? AND notification_id = ?",
        (notification_datetime, chat_id, notification_id)
    )
    conn.commit()
    conn.close()


def db_read_user_notifications(chat_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications WHERE chat_id = ?", (chat_id,))
    notifications = cursor.fetchall()
    conn.close()
    return notifications


def db_delete_user_notification(chat_id, notification_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION")
    # Fetch the notification before deleting it
    cursor.execute("SELECT * FROM notifications WHERE chat_id = ? AND notification_id = ?", (chat_id, notification_id,))
    notification = cursor.fetchone()
    notification_id = notification[2] if notification else None
    if not notification:
        conn.close()
        raise ValueError("Notification not found")
    cursor.execute("DELETE FROM notifications WHERE chat_id = ? AND notification_id = ?", (chat_id, notification_id,))
    cursor.execute("UPDATE notifications SET notification_id = notification_id - 1 WHERE chat_id = ? AND notification_id > ?", (chat_id, notification_id,))
    conn.commit()
    conn.close()
    return notification


def db_read_all_notifications():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications")
    notifications = cursor.fetchall()
    conn.close()
    return notifications

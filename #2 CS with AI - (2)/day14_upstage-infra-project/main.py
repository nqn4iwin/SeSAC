import enum

import pymysql
from pymysql import cursors

from connection_pool import PymysqlConnectionPool

pool = PymysqlConnectionPool(
    maxsize=5,
    host="localhost",
    port=3306,
    user="root",
    password="password",
    database="llmagent",
)


def connection():
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            print(row)
    finally:
        pool.release_connection(conn)


def create_user(name: str, email: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                  INSERT INTO users (name, email)
                  VALUES (%s, %s)
                  """
            cursor.execute(sql, (name, email))
        conn.commit()
    finally:
        pool.release_connection(conn)


def get_user_by_email(email: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                  SELECT id, name, email, created_at
                  FROM users
                  WHERE email = %s
                  """
            cursor.execute(sql, (email,))
            return cursor.fetchone()
    finally:
        pool.release_connection(conn)


def update_user_name(user_id: int, new_name: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                  UPDATE users
                  SET name = %s
                  WHERE id = %s
                  """
            cursor.execute(sql, (new_name, user_id))
        conn.commit()
    finally:
        pool.release_connection(conn)


def delete_user_by_email(email: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM users WHERE email = %s"
            cursor.execute(sql, (email,))
        conn.commit()
    finally:
        pool.release_connection(conn)


def add_conversation(user_id: int, role: str, message: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                  INSERT INTO conversations (user_id, role, message)
                  VALUES (%s, %s, %s) 
                  """
            cursor.execute(sql, (user_id, role, message))
        conn.commit()
    finally:
        pool.release_connection(conn)


def get_recent_conversations(user_id: int, limit: int = 20):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                  SELECT id, user_id, role, message, created_at
                  FROM conversations
                  WHERE user_id = %s
                  ORDER BY created_at DESC
                      LIMIT %s 
                  """
            cursor.execute(sql, (user_id, limit))
            return cursor.fetchall()
    finally:
        pool.release_connection(conn)


def save_chat_transaction(user_id: int, user_msg: str, assistant_msg: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            # 1) 사용자 메시지 저장
            sql1 = """
                   INSERT INTO conversations (user_id, role, message)
                   VALUES (%s, 'user', %s) 
                   """
            cursor.execute(sql1, (user_id, user_msg))

            # 2) 어시스턴트 메시지 저장
            sql2 = """
                   INSERT INTO conversations (user_id, role, message)
                   VALUES (%s, 'assistant', %s) 
                   """
            cursor.execute(sql2, (user_id, assistant_msg))

        conn.commit()  # 두 개가 모두 성공한 경우에만 commit

    except Exception as e:
        conn.rollback()  # 하나라도 실패하면 전체 취소
        raise e
    finally:
        pool.release_connection(conn)


def save_chat_transaction_fail(user_id: int, user_msg: str, assistant_msg: str):
    conn = pool.get_conn()
    try:
        with conn.cursor() as cursor:
            # 1) 사용자 메시지 저장
            sql1 = """
                   INSERT INTO conversations (user_id, role, message)
                   VALUES (%s, 'user', %s) 
                   """
            cursor.execute(sql1, (user_id, user_msg))

            # 2) 어시스턴트 메시지 저장
            sql2 = """
                   INSERT INTO conversations (user_id, '아차실수', message)
                   VALUES (%s, 'assistant', %s) 
                   """
            cursor.execute(sql2, (user_id, assistant_msg))

        conn.commit()  # 두 개가 모두 성공한 경우에만 commit

    except Exception as e:
        conn.rollback()  # 하나라도 실패하면 전체 취소
        raise e
    finally:
        pool.release_connection(conn)


class Role(enum.Enum):
    user = 'user'
    assistant = 'assistant'


if __name__ == '__main__':
    # connection()
    # create_user('hak', 'ox4443@naver.com')
    # print(get_user_by_email('ox4443@naver.com'))
    # for i in range(100):
    #     print(get_user_by_email('ox4443@naver.com'))
    # user = get_user_by_email('ox4443@naver.com')
    # print(user)
    # update_user_name(user.get('id'), 'yeong')
    # replace_user = get_user_by_email('ox4443@naver.com')
    # print(replace_user)
    # delete_user_by_email('ox4443@naver.com')
    # print(get_user_by_email('ox4443@naver.com'))

    # add_conversation(1, Role.user.name, '뭐해?')
    # print(get_recent_conversations(1, 1))

    save_chat_transaction(1, '뭐해?', '그냥있어요')
    print(get_recent_conversations(1, 2))

    try:
        save_chat_transaction_fail(1, '뭐라고?', '그냥있다고요')
    except:
        pass
    print(get_recent_conversations(1, 2))

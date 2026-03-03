import pymysql
from queue import Queue

class PymysqlConnectionPool:
  def __init__(self, maxsize=5, **db_params):
    self._pool = Queue(maxsize)
    self._db_params = db_params
    for _ in range(maxsize):
      self._pool.put(self._create_conn())

  def _create_conn(self):
    return pymysql.connect(
      charset="utf8mb4",
      cursorclass=pymysql.cursors.DictCursor,
      **self._db_params,
    )

  def get_conn(self):
      # 큐에서 커넥션 하나 가져옴 (없으면 대기)
      conn = self._pool.get()
      # 혹시 끊겨 있으면 재연결
      try:
          conn.ping(reconnect=True)
      except Exception:
          conn = self._create_conn()
      return conn

  def release_connection(self, conn):
    # 풀에 커넥션 되돌려놓기
    self._pool.put(conn)

  def close_all(self):
    # 프로그램 종료 시 풀 안의 모든 커넥션 정리
    while not self._pool.empty():
      conn = self._pool.get()
      conn.close()

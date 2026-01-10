import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 接続先DBの設定
# Docker環境では /data/db/weather.sqlite3、ローカルでは data/weather.sqlite3
DB_PATH = os.getenv('DB_PATH', 'data/weather.sqlite3')
DATABASE = f'sqlite:///{DB_PATH}'

# Engine の作成
Engine = create_engine(
  DATABASE
)
Base = declarative_base()

# Sessionの作成
session = scoped_session(
  sessionmaker(
    autocommit = False,
	  autoflush = False,
	  bind = Engine
  )
)

# modelで使用する
Base = declarative_base()
Base.query = session.query_property()
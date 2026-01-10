from sqlalchemy import Column, Integer, String, Boolean, DateTime
from db_setting import Engine
from db_setting import Base
from datetime import datetime
import pytz

class Extra(Base):
    """
    EXTRAを取得した日時を記録するモデル
    """

    __tablename__ = 'extra'
    __table_args__ = {
        'comment': '最後に取得したEXTRAに関する情報のテーブル'
    }

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    last_modified = Column('last_modified', String(50))
    downloaded_at = Column('downloaded_at', DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))

class VPWW54xml(Base):
    """
    読み込んだVPWW54形式XMLファイルを記録するモデル
    XMLファイルを削除するとモデルからも削除する
    """

    __tablename__ = 'vpww54xml'
    __table_args__ = {
        'comment': '読み込んだVPWW54形式XMLファイルを記録するテーブル'
    }

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    xmlfile = Column('xmlfile', String(50))
    lmo = Column('lmo', String(50))
    created_at = Column('created_at', DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    updated_at = Column('updated_at', DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    is_delete = Column('is_delete', Boolean, default=False)

class CityReport(Base):
    """
    最新の投稿内容を記録するモデル
    """

    __tablename__ = 'city_report'
    __table_args__ = {
        'comment': '最新の投稿情報のテーブル'
    }

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    xmlfile = Column('xmlfile', String(50))
    lmo = Column('lmo', String(50))
    city = Column('city', String(50))
    kind_name = Column('kind_name', String(100))
    status = Column('status', String(100))
    created_at = Column('created_at', DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    updated_at = Column('updated_at', DateTime, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    is_delete = Column('is_delete', Boolean, default=False)

# DBを使うには最初に一度下記を実行する
if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)
"""
Weather Warning Scheduler

Pythonのscheduleライブラリを使用して、以下のタスクを定期実行します:
- 気象警報チェック: 10分おき
- データクリーンアップ: 毎日1:00 (月1回の想定だが、条件付きで毎日実行)
"""
import schedule
import time
import datetime
import traceback
import os
from weather import run_weather_check
from remove_data import run_cleanup


def initialize_database():
    """データベースの初期化を行う"""
    from db_setting import Engine, Base
    from models import Extra, VPWW54xml, CityReport

    print("Initializing database...")
    try:
        # テーブルが存在しない場合のみ作成
        Base.metadata.create_all(bind=Engine)
        print("Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        raise


def weather_check_job():
    """10分おきに実行される気象情報チェックジョブ"""
    try:
        print(f"\n{'='*60}")
        print(f"[{datetime.datetime.now()}] Starting weather check job")
        print(f"{'='*60}")
        run_weather_check()
        print(f"[{datetime.datetime.now()}] Weather check job completed")
    except Exception as e:
        print(f"[ERROR] Weather check job failed: {e}")
        traceback.print_exc()


def cleanup_job():
    """毎日1:00に実行されるデータクリーンアップジョブ

    Note: 実際のクリーンアップは内部で30日以上前のデータのみを削除するため、
          毎日実行しても問題ない
    """
    try:
        print(f"\n{'='*60}")
        print(f"[{datetime.datetime.now()}] Starting cleanup job")
        print(f"{'='*60}")
        run_cleanup(period=30)
        print(f"[{datetime.datetime.now()}] Cleanup job completed")
    except Exception as e:
        print(f"[ERROR] Cleanup job failed: {e}")
        traceback.print_exc()


def main():
    """スケジューラーのメイン処理"""
    print(f"\n{'#'*60}")
    print("Weather Warning Scheduler Started")
    print(f"Started at: {datetime.datetime.now()}")
    print(f"{'#'*60}\n")

    # データベース初期化
    initialize_database()

    # 起動時に即座に1回実行
    print("Running initial weather check...")
    weather_check_job()

    # スケジュール設定
    # 10分おきに気象警報チェック
    schedule.every(10).minutes.do(weather_check_job)

    # 毎日1:00にデータクリーンアップ
    schedule.every().day.at("01:00").do(cleanup_job)

    print(f"\nSchedule configured:")
    print(f"  - Weather check: Every 10 minutes")
    print(f"  - Cleanup: Daily at 01:00")
    print(f"\nNext scheduled runs:")
    for job in schedule.get_jobs():
        print(f"  - {job}")
    print(f"\n{'='*60}\n")

    # 無限ループでスケジュール実行
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n{'#'*60}")
        print("Scheduler stopped by user")
        print(f"Stopped at: {datetime.datetime.now()}")
        print(f"{'#'*60}")


if __name__ == '__main__':
    main()

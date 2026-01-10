import datetime
import os
import glob
from dotenv import load_dotenv
from db_setting import session
from models import CityReport, Extra, VPWW54xml

load_dotenv()
# Docker環境では /data/deleted、ローカルでは data/deleted
DELETED_DIR = os.getenv('DELETED_DIR', 'data/deleted')

def deleteFileBefore(filepath, days):
        files = glob.glob(filepath, recursive=True)
        for file in files:
            print(f"{os.path.basename(file)}:{datetime.datetime.fromtimestamp(os.stat(file).st_mtime)}")
            file_dt = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
            target_day = datetime.datetime.now() - datetime.timedelta(days=days)
            print(f"{target_day}")
            if (file_dt < target_day):  # older than target_day
                print(f"{os.path.basename(file)}:{datetime.datetime.fromtimestamp(os.stat(file).st_mtime)}:remove")
                os.remove(file)
            else:
                print(f"{os.path.basename(file)}:{datetime.datetime.fromtimestamp(os.stat(file).st_mtime)}:don't remove")

def deleteCityReportBefore(days):
    """
    CityReportテーブルから、is_deleteがTrueかつ、update_atがdays以前のデータを削除する
    """
    reports = session.query(CityReport).filter(
        CityReport.is_delete == True,
        CityReport.updated_at < datetime.datetime.now() - datetime.timedelta(days=days)
        ).all()
    for report in reports:
        print(f"**delete CR table: {report.id}, {report.lmo}, {report.xmlfile}, {report.city}, {report.kind_name}, {report.status}, {report.is_delete}")
        session.delete(report)
    session.commit()

def deleteVPWW54xmlBefore(days):
    """
    VPWW54xmlテーブルから、is_deleteがTrueかつ、update_atがdays以前のデータを削除する
    """
    vpww54xmls = session.query(VPWW54xml).filter(
        VPWW54xml.is_delete == True,
        VPWW54xml.updated_at < datetime.datetime.now() - datetime.timedelta(days=days)
        ).all()
    for xml in vpww54xmls:
        print(f"**remove xmlfile: {xml.id}, {xml.lmo}, {xml.xmlfile}, {xml.is_delete}")
        session.delete(xml)
    session.commit()

def run_cleanup(period=30):
    """データクリーンアップのメイン処理を実行

    Args:
        period (int): 削除対象とする日数（デフォルト30日）
    """
    print(f"filepath:{__file__}")
    print(f"dirname:{os.path.dirname(__file__)}")
    targetpath = os.path.join(DELETED_DIR, "*.xml")
    deleteFileBefore(targetpath, days = period)
    deleteCityReportBefore( days = period )
    deleteVPWW54xmlBefore( days = period )

if __name__ == '__main__':
    run_cleanup(period=30)

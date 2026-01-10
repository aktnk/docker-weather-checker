import datetime
import os
from dotenv import load_dotenv

from db_setting import session
from models import CityReport, Extra, VPWW54xml
#from JMAFeed import JMAFeed

load_dotenv()
# Docker環境では /data/xml、ローカルでは data
DATADIR = os.getenv('DATADIR', 'data')

def checkCityAndKindDataSameInCityReport(obs,city,kind_name):
    """
    CityReportテーブルにlmoがobs,cityがcity,kind_nameがitem.kindNameのデータあるか調べる
    """
    print(f"判定: {obs}, {city}, {kind_name}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.is_delete==False).first()
    
    if report is None:
        print("CityReportに同じ市町、同じ警報・注意報のデータなし")
        return False, report
    print("CityReportに同じ市町、同じ警報・注意報のデータあり")
    return True, report

def createCityReport(obs, city, kind_name, status, xmlfile):
    """
    CiryReportテーブルに新規にデータを登録する
    """
    print(f"create: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = CityReport()
    report.lmo = obs
    report.city = city
    report.kind_name = kind_name
    report.status = status
    report.xmlfile = xmlfile
    session.add(report)
    session.commit()

def addVPWW54xml( obs, xmlfile ):
    """
    VPWW54xmlテーブルに新規にデータを登録する
    """
    vpww54xml = session.query(VPWW54xml).filter(
        VPWW54xml.xmlfile==xmlfile,
        VPWW54xml.lmo==obs,
        VPWW54xml.is_delete==False).first()
    if vpww54xml is None:
        print(f"create: {xmlfile}")
        new_vpww54 = VPWW54xml()
        new_vpww54.xmlfile = xmlfile
        new_vpww54.lmo = obs
        session.add(new_vpww54)
    session.commit()

def updateCityReportByStatus(obs, city, kind_name, status, xmlfile):
    """
    CityReportテーブルのstatusを更新する
    xmlfileが変更されていれば、xmlfileも更新する
    """
    print(f"update: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    ret = False
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status!=status,
        CityReport.is_delete==False).first()
    report.status = status
    if report.xmlfile != xmlfile:
        print(f"xmlfile is not same:{report.xmlfile} - {xmlfile}")
        report.xmlfile = xmlfile
        ret = True
    report.updated_at = datetime.datetime.now()
    session.commit()
    return ret


def deleteCityReportByStatus(obs, city):
    """
    CityReportテーブルのその市町で記録された警報・注意報のデータを削除する
    """
    print(f"*delete: {obs}, {city}")
    reports = session.query(CityReport).filter(
        CityReport.lmo == obs,
        CityReport.city == city,
        CityReport.is_delete == False).all()
    for report in reports:
        print(f"*delete CR table: {report.id}, {report.lmo}, {report.xmlfile}, {report.city}, {report.kind_name}, {report.status}, {report.is_delete}")
        report.is_delete = True
        report.updated_at = datetime.datetime.now()
    session.commit()

def updateCityReportByXmlfile(obs, city, kind_name, status, xmlfile):
    """
    CityReportテーブルのxmlfileを更新する
    """
    print(f"update: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status==status,
        CityReport.xmlfile!=xmlfile,
        CityReport.is_delete==False).first()
    report.xmlfile=xmlfile
    report.updated_at=datetime.datetime.now()
    session.commit()

def deleteCityReportByLMO(obs):
    """
    CityReportテーブルから、lmoがobsのデータがあり、そのstatusが'解除'であれば、削除する
    """
    reports = session.query(CityReport).filter(
        CityReport.lmo == obs,
        CityReport.status == '解除',
        CityReport.is_delete == False).all()
    for report in reports:
        print(f"**delete CR table: {report.id}, {report.lmo}, {report.xmlfile}, {report.city}, {report.kind_name}, {report.status}, {report.is_delete}")
        report.is_delete = True
        report.updated_at = datetime.datetime.now()
    session.commit()

def deleteVPWW54xmlByLMO(obs):
    """
    VPWW54xmlテーブルから、lmoがobsのデータは、xmlファイルを削除し、テーブルからも削除する
    """
    vpww54xmls = session.query(VPWW54xml).filter(
        VPWW54xml.lmo == obs,
        VPWW54xml.is_delete == False).all()
    for xml in vpww54xmls:
        print(f"**remove xmlfile: {xml.id}, {xml.lmo}, {xml.xmlfile}, {xml.is_delete}")
        xml.is_delete = True
        xml.updated_at = datetime.datetime.now()
        try:
            os.rename(os.path.join(DATADIR, xml.xmlfile), os.path.join('del', xml.xmlfile))
        except FileNotFoundError:
            pass
    session.commit()

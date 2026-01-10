import logging
import requests
import xmltodict
import datetime
from pytz import timezone
import os
from dotenv import load_dotenv

from db_setting import session
from models import CityReport, Extra, VPWW54xml

from weather_DB import deleteCityReportByLMO, deleteVPWW54xmlByLMO, deleteCityReportByStatus, updateCityReportByStatus, updateCityReportByXmlfile, checkCityAndKindDataSameInCityReport, addVPWW54xml, createCityReport

logging.basicConfig(level=logging.DEBUG)
load_dotenv()
# Docker環境では /data/xml、ローカルでは data
DATADIR = os.getenv('DATADIR', 'data')

class JMAFeed:
    """
    気象庁(Japan Meteorological Agency)Feed
    """
    EXTRA = 'https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
    VPWW54_TITLE='気象警報・注意報（Ｈ２７）'
    FILENAME = os.path.join(DATADIR, EXTRA.split('/')[-1])

    def __init__(self):
        self.dict = None
        self.LMO = ""
        self.VPWW54list = []
        self.http_session = requests.Session()

    def __del__(self):
        print("request session close")
        self.http_session.close()

    def readExtraFile(self):
        """
        xmlfile で指定したXMLファイルを読み取り、文字列として返す
        xmlfile が存在しない場合は、""空文字列を返す
        """
        response = ""
        if (os.path.isfile(JMAFeed.FILENAME)):
            with open(JMAFeed.FILENAME, mode="r", encoding='utf-8') as f:
                response = f.read()
            last_modified = "file"
            #print(f"readExtraFilre()1:{response}")
        else:
            # extra.xmlファイルが存在しないとき、If-Modified-Sinceなしで取得する
            time = datetime.datetime.now()
            http_response = self.http_session.get(JMAFeed.EXTRA, timeout=10)
            print(f"readExtraFile()2:{http_response.status_code}")
            response = http_response.content
            if "Last-Modified" in http_response.headers:
                last_modified = http_response.headers['Last-Modified']
            else: # レスポンスにLast-Modifiedが含まれなかったとき
                last_modified = "na"
            with open(JMAFeed.FILENAME, mode='wb') as f:
                f.write(response)
            updateExtraData(last_modified, time)
        return response, last_modified

    def getFeed(self, url=EXTRA):
        """
        url から Feed を取得し、dict形式で結果を保持する
        """
        last_modified = getExtraLastModified()
        if last_modified == "na":
            req_header = {}
        else:
            req_header = { 'If-Modified-Since': last_modified }
        print(f"request_header:{req_header}")
        
        time = datetime.datetime.now()
        http_response = self.http_session.get(url,headers = req_header,timeout=10)
        if "Last-Modified" in http_response.headers:
            print(f"Last-Modified: {http_response.headers['Last-Modified']}")
        if "Cache-Control" in http_response.headers:
            print(f"Cache-Control: {http_response.headers['Cache-Control']}")
        print(http_response.status_code)
        if http_response.status_code == 304: # Not Modified
            print("extra.xml:304")
            response, lm = self.readExtraFile()
            if lm == "file": # 304を受け取ったときにレスポンスで返されたLast-Modifiedを使用
                if "Last-Modified" in http_response.headers:
                    last_modified = http_response.headers['Last-Modified']
                else:
                    last_modified = "na"
            else:
                last_modified = lm
        else: # レスポンスにextra.xmlが含まれるはず
            print(f"extra.xml:{http_response.status_code}")
            response = http_response.content
            if "Last-Modified" in http_response.headers:
                last_modified = http_response.headers['Last-Modified']
            else:
                last_modified = "na"
            with open(JMAFeed.FILENAME, mode='wb') as f:
                f.write(response)
            updateExtraData(last_modified, time)

        self.dict = xmltodict.parse( response )

    def analyzeVPWW54ListbyLMO(self, obs):
        """
        地方気象台 obs が発表した気象特別警報・警報・注意報（VPWW54形式：気象警報・注意報（Ｈ２７））のリストを取得する
        """
        vpww54list = []
        for entry in self.dict['feed']['entry']:
            if entry['title'] == JMAFeed.VPWW54_TITLE and entry['author']['name'] == obs:
                warning = JMAFeedEntryData(
                    title = entry['title'],
                    id = entry['id'],
                    updated = datetime.datetime.strptime(entry['updated'][:-1]+'+0000','%Y-%m-%dT%H:%M:%S%z').astimezone(timezone('Asia/Tokyo')),
                    author_name=entry['author']['name'],
                    content = entry['content']['#text']
                )
                if len(vpww54list) == 0:
                    vpww54list.append(warning)
                else:
                    # 日付の新しいものから古いものへ順に並べて、wpww54listに保存する
                    found = False
                    for idx, item in enumerate(vpww54list):
                        if warning.updated > item.updated:
                            vpww54list.insert( idx, warning)
                            found = True
                            break
                        else:
                            continue
                    if not found:
                        vpww54list.append(warning)
        self.VPWW54list = vpww54list
        return vpww54list
    
    def getLatestVPWW54EntryByLMO(self, obs):
        self.LMO = obs
        if self.dict is None:
            self.getFeed()
        self.analyzeVPWW54ListbyLMO(obs)
        if len(self.VPWW54list) > 0:
            return self.VPWW54list[0]
        else:
            return None

class JMAFeedEntryData:
    """
    JMAFeedクラスのanalyzeVPWW54ListbyLMO(obs)メソッドが生成する気象情報リストに保管されるEntryデータのクラス
    """

    def __init__(self, title, id, updated, author_name, content):
        self.title = title
        self.id = id
        self.updated = updated
        self.author_name = author_name
        self.content = content

    def __str__(self):
        return f'title:{self.title}, id:{self.id}, updated:{self.updated}, LMO:{self.author_name}, msg:{self.content}'

class VPWW54XMLData:
    """
    VPWW54形式のXMLデータのクラス
    """
    
    def __init__(self, url, obs, feedobj):
        self.url = url
        self.filename = url.split('/')[-1]
        self.warnings = []
        self.dict = {}
        self.lmo = obs
        self.feedobj = feedobj

    def getData(self):
        """
        VPWW54形式のxmlファイルがダウンロード済みであればファイルから、そうでなければURLから取得する
        """
        # 当該xmlファイルが存在するか？
        filepath = os.path.join( DATADIR, self.filename)
        if (os.path.isfile(filepath)):
            print(f"xmlfile read:{self.filename}")
            response = self.readXMLfile(filepath)
        else:
            response = self.feedobj.http_session.get(self.url,timeout=10).content
            print(f"xmlfile download 1:{self.filename}")
            addVPWW54xml(self.lmo, self.filename)
            with open(filepath, mode='wb') as f:
                    f.write(response)

        self.dict = xmltodict.parse( response )

    def readXMLfile(self, xmlfile):
        """
        xmlfile で指定したXMLファイルを読み取り、文字列として返す
        xmlfile が存在しない場合は、""空文字列を返す
        """
        response = ""
        if (os.path.isfile(xmlfile)):
            with open(xmlfile, mode="r", encoding='utf-8') as f:
                response = f.read()
        return response

    def analyzeAll(self, warning_type='気象警報・注意報（市町村等）' ):
        """
        取得したxmlデータを解析し、警報・注意報に関する情報を得る
        """
        # Controlタグ情報の取得
        self.control = VPWW54Control(
            title = self.dict['Report']['Control']['Title'],
            datetime = datetime.datetime.strptime(self.dict['Report']['Control']['DateTime'][:-1]+'+0000','%Y-%m-%dT%H:%M:%S%z').astimezone(timezone('Asia/Tokyo')),
            status = self.dict['Report']['Control']['Status'],
            publishing_office = self.dict['Report']['Control']['PublishingOffice']
        )
        # Headタグ情報の取得
        self.head = VPWW54Head(
            title = self.dict['Report']['Head']['Title'],
            report_datetime = datetime.datetime.strptime(self.dict['Report']['Head']['ReportDateTime'].replace('+09:00','+0900'),'%Y-%m-%dT%H:%M:%S%z'),
            info_type = self.dict['Report']['Head']['InfoType'],
            info_kind = self.dict['Report']['Head']['InfoKind'],
        )
        # Body>Warningタグ情報の取得
        for warning in self.dict['Report']['Body']['Warning']:
            if warning['@type'] == warning_type:
                for item in warning['Item']:
                    # Area>NameタグとChangeStatusタグの取得
                    if 'ChangeStatus' in item:
                        #print(f"item : changestatus")
                        city_warnings = VPWW54BodyWarningTypeCity(
                            area_name=item['Area']['Name'],
                            change_status = item['ChangeStatus']
                        )
                    else:
                        #print(f"item : non changestatus")
                        city_warnings = VPWW54BodyWarningTypeCity(
                            area_name=item['Area']['Name'],
                            change_status = None
                        )
                    # Kindタグ情報の取得
                    #print(f"!!!type") #:{item['Kind']}")
                    if isinstance((item['Kind']),dict):
                        #print(f"## item dict")
                        if 'Name' in item['Kind']:
                            #print(f"{item['Kind']['Name']} : {item['Kind']['Status']}")
                            city_warnings.addKind(
                                kind_name = item['Kind']['Name'],
                                status = item['Kind']['Status']
                            )
                        else:
                            #print(f"### None") #: {item['Kind']['Status']}")
                            city_warnings.addKind(
                                kind_name = None,
                                status = item['Kind']['Status']
                            )
                    elif type(item['Kind']) is list:
                        #print(f"#### item list") #:{item['Kind']}")
                        for kind in item['Kind']:
                            city_warnings.addKind(
                                kind_name = kind['Name'],
                                status = kind['Status']
                            )
                    # 解析結果をwarnings属性へ追加
                    if city_warnings is not None:
                        #print(f"append:{city_warnings}")
                        self.warnings.append( city_warnings )

    def getCityWarnings( self, city ):
        """
        VPWW54形式xmlデータを取得し、指定されたcityの警報・注意報を取り出す
        """
        if len(self.warnings) == 0:
            self.getData()
            self.analyzeAll()
            #print("analyzeAll:::")
        for warning in self.warnings:
            if warning.areaName == city:
                #print(f"{warning}")
                return warning, self.control, self.head
                

class VPWW54Control:
    """
    VPWW54形式xmlデータのControlタグに含まれるデータのクラス
    """

    def __init__(self, title, datetime, status, publishing_office):
        self.title = title
        self.datetime = datetime
        self.status = status
        self.publishedBy = publishing_office

    def __str__(self):
        return f'Control, title:{self.title}, datetime:{self.datetime}, status:{self.status}, publishedBy:{self.publishedBy}'

class VPWW54Head:
    """
    VPWW54形式xmlデータのHeadタグに含まれるデータのクラス
    """
    def __init__(self, title, report_datetime, info_type, info_kind):
        self.title = title
        self.reportDateTime = report_datetime
        self.infoType = info_type
        self.infoKind = info_kind

    def __str__(self):
        return f'Head, title:{self.title}, reportDateTime:{self.reportDateTime}, infoType:{self.infoType}, infoKind:{self.infoKind}'

class VPWW54BodyWarningTypeCity:
    """
    VPWW54形式xmlデータのBodyタグに含まれる市町村の警報・注意報データのクラス
    """

    warningType = '気象警報・注意報（市町村等）'

    def __init__(self, area_name, change_status):
        self.areaName = area_name
        self.changeStatus = change_status
        self.kind = []

    def __str__(self):
        ans = f'Warning, type:{self.warningType}, city:{self.areaName}, changeStatus:{self.changeStatus}'
        for item in self.kind:
            ans = ans + f", Item, kindName:{item['kindName']}, status:{item['status']}"
        return ans

    def addKind( self, kind_name, status):
        self.kind.append( {'kindName': kind_name, 'status': status})

def isExtraWithin10Minutes():
    """
    extra.xmlを10分以内に取得済みか判定する
    """
    try:
        extra = session.query(Extra).first()
    except Exception as err:
        if (not os.path.isfile(JMAFeed.FILENAME)):
            print("Error: db file not found. Please run `python models.py`")
        print(f"{err}")
        sys.exit()

    if extra is None:
        print("no extra : without 9 minutes")
        return False
    else:
        if datetime.datetime.now()- extra.downloaded_at < datetime.timedelta(minutes = 9):
            print("within 9 minutes")
            return True
        else:
            print("without 9 minutes")
            return False

def getExtraLastModified():
    """
    前回取得したextra.xmlのLast-Modified値をDBから取得する
    Last-Modifiedが設定されていないかった場合は、"na"を返す
    通常は"Sat, 24 Aug 2024 07:27:23 GMT"のようにdatetimeを返す

    """
    try:
        extra = session.query(Extra).first()
    except Exception as err:
        if (not os.path.isfile(JMAFeed.FILENAME)):
            print("Error: db file not found. Please run `python models.py`")
        print(f"{err}")
        sys.exit()

    if extra is None:
        print("no extra data")
        return "na"
    else:
        return extra.last_modified

def updateExtraData( last_modified, time ):
    """
    extra.xmlのダウンロード時間をtimeに更新する
    """
    print(f"extra_table update:{last_modified},{time}")
    extra = session.query(Extra).first()
    if extra is None:
        new_extra = Extra(last_modified=last_modified,downloaded_at=time)
        session.add( new_extra )
        session.commit()
    else:
        extra.last_modified = last_modified
        extra.downloaded_at = time
        session.commit()
    session.close()
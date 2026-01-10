from dotenv import load_dotenv
from email.mime.text import MIMEText
from JMAWeb import JMAWebURLs

import datetime
import os
import smtplib

class Gmail:
    def __init__(self, gmail_from, gmail_app_pass, gmail_to, gmail_bcc):
        self.gmail_from = gmail_from
        self.gmail_app_pass = gmail_app_pass
        self.gmail_to = gmail_to
        self.gmail_bcc = gmail_bcc

    def __create_message(self, obs, city, warning, status, dt):
        dts = dt.strftime("%Y/%m/%d %H:%M:%S")
        body = f"LWO:{obs}\nDATE:{dts}\nCITY:{city}\nWARN:{warning}\nSTAT:{status}\n"
        #if status in ['発表']:
        #    body += f" {city} に {warning} が {status} されました。\n"
        #else:
        #    body += f" {city} に {warning} の {status} が発表されました。\n"
        #body += f" 気象庁｜{JMAWebURLs.getLink(city)[0]}の警報・注意報は\n {JMAWebURLs.getLink(city)[1]}\n で確認できます。"
        body += f"LINK:気象庁｜{JMAWebURLs.getLink(city)[0]}の警報・注意報\nURL:{JMAWebURLs.getLink(city)[1]}\nEND"

        msg=MIMEText(body)
        msg["Subject"]=f"{city}:{warning}:{status}"
        msg["From"]=self.gmail_from
        msg["To"]=self.gmail_to
        msg["Bcc"]=self.gmail_bcc
        self.message = msg

    def send_message(self, obs, city, warning, status, dt, debug=False):
        self.__create_message(obs, city, warning, status, dt)
        try:
            smtp=smtplib.SMTP("smtp.gmail.com",587)
            smtp.set_debuglevel(debug)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(self.gmail_from, self.gmail_app_pass)
            smtp.send_message(self.message)
            smtp.close()
        except Exception as ex:
            print(f"send Error:{ex}")


if __name__=="__main__":
    load_dotenv()
    GMAIL_APP_PASS = os.getenv('GMAIL_APP_PASS')
    GMAIL_FROM = os.getenv('GMAIL_FROM')
    EMAIL_TO = os.getenv('EMAIL_TO')
    EMAIL_BCC = os.getenv('EMAIL_BCC')

    city = "テスト市"
    warning = "テスト大雨注意報"
    status = "発表"

    pub_dt = datetime.datetime.now() 
    mygmail = Gmail(GMAIL_FROM, GMAIL_APP_PASS, EMAIL_TO , EMAIL_BCC)
    mygmail.send_message('テスト気象台', city, warning, status, datetime.datetime.now(), debug=True)

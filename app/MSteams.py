from pymsteams import connectorcard
from JMAWeb import JMAWebURLs
import os
import datetime
from dotenv import load_dotenv

class MSTeams:
    def __init__(self, webhook_url, mention_uid, mention_display_name):
        self.teams = connectorcard(webhook_url)
        self.mention_uid = mention_uid
        self.mention_display_name = mention_display_name

    def __create_mention_payload(self, obs, city, warning, status, dt):
        dts = dt.strftime("%Y/%m/%d %H:%M:%S")
        mention_entity = {
            "type": "mention",
            "text": f"<at>{self.mention_display_name}</at>",
            "mentioned": {
                "id": self.mention_uid,
                "name": self.mention_display_name
            }
        }
        adaptive_card_content = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.0",
            "type": "AdaptiveCard",
            "body": [
                {"type": "TextBlock", "text": f"{city}", "size": "large", "weight": "bolder"},
                {"type": "TextBlock", "text": f"{warning} : {status}", "size": "large", "weight": "bolder", "spacing": "none"},
                {"type": "TextBlock", "text": f"{obs} {dts} 発表", "spacing": "none"},
                {"type": "TextBlock", "text": f"{mention_entity['text']}"}
            ],
            "actions": [
                { "type": "Action.OpenUrl", "title": f"気象庁｜{JMAWebURLs.getLink(city)[0]}の警報・注意報を開く", "url": f"{JMAWebURLs.getLink(city)[1]}", "role": "button"}
            ],
            "msteams": {"entities": [mention_entity]}
        }
        self.teams.payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": adaptive_card_content
            }]
        }

    def send_message(self, obs, city, warning, status, dt):
        self.__create_mention_payload(obs, city, warning, status, dt)
        try:
            self.teams.send()
        except Exception as ex:
            print(f"send Error:{ex}")

if __name__=="__main__":
    # 動作確認用
    load_dotenv()
    WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK')
    MENTION_USERID = os.getenv('MENTION_USERID')
    MENTION_USERNAME = os.getenv('MENTION_USERNAME')
    myteams = MSTeams(WEBHOOK_URL, MENTION_USERID, MENTION_USERNAME)
    myteams.send_message('テスト気象台', 'テスト市', "テスト注意報", "テスト発表", datetime.datetime.now())
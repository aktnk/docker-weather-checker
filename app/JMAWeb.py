
class JMAWebURLs:

    link = [
        { "city": "裾野市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=2222000" },
        { "city": "御殿場市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=2221500" },
        { "city": "三島市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=2220600"},
        { "city": "熱海市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=2220500"},
        { "city": "都城市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=4520200"},
        { "city": "つがる市", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja&area_type=class20s&area_code=0220900"},
    ]
    default = { "city": "全国", "url": "https://www.jma.go.jp/bosai/warning/#lang=ja"}

    @classmethod
    def getLink(cls, city):
        for item in cls.link:
            if item["city"] == city:
                return (item["city"], item["url"])
        return cls.getDefaultLink()
    
    @classmethod
    def getDefaultLink(cls):
        return (cls.default["city"], cls.default["url"])

if __name__=="__main__":
    ans = JMAWebURLs.getLink("裾野市")
    print(f"{ans[0]} - {ans[1]}")
    ans = JMAWebURLs.getLink("東京都")
    print(f"{ans[0]} - {ans[1]}")
    

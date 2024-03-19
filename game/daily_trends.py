import random
from functools import cache

from rss_parser import RSSParser
import requests
import re

SUPPORTED_GEO = ["PL", "US"]


@cache
class DailyTrends:
    def __init__(self):
        self.data = {}
        for geo in SUPPORTED_GEO:
            rss_url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
            rss = RSSParser.parse(requests.get(rss_url).text)
            data = []
            for item in rss.channel.items:
                data += re.findall(r"\w{2,}", item.title.content)
            self.data[geo] = data

    def get_words(self, geo, k):
        if geo in SUPPORTED_GEO:
            return random.sample(self.data[geo], k=k)

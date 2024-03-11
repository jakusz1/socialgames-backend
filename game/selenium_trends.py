import json
import logging
import os
import time
from functools import cache

from selenium import webdriver
import chromedriver_binary
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
import re


CHROME_USER_DATA = "C:\\Users\\jakus\\AppData\\Local\\Google\\Chrome\\User Data"
DOWNLOAD_XPATH = "//trends-widget[@widget-name='TIMESERIES']//button[contains(@class, 'export')][1]"
TIMEOUT = 10


def _get_file_path():
    with open(CHROME_USER_DATA + "\\Default\\Preferences") as f:
        return f"{json.load(f)['download']['default_directory']}\\multiTimeline.csv"


def _fix_non_int(string, default_val=0):
    try:
        return int(string)
    except ValueError:
        return default_val


@cache
class SeleniumTrends:
    def __init__(self):
        self._logger = logging.getLogger('selenium_trends')
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={CHROME_USER_DATA}")
        self._driver = webdriver.Chrome(options=options)
        self._file_path = _get_file_path()

    def __del__(self):
        self._driver.quit()

    def get_data(self, prompts, geo):
        data = pd.DataFrame()
        try:
            os.remove(self._file_path)
        except FileNotFoundError:
            pass
        self._driver.get(f"https://trends.google.com/trends/explore?geo={geo}&q={','.join(prompts)}")
        try:
            WebDriverWait(self._driver, TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, DOWNLOAD_XPATH))).click()
            attempt = 0
            while not os.path.exists(self._file_path):
                time.sleep(1)
                attempt += 1
                if attempt >= TIMEOUT:
                    raise Exception("Download wasn't finished in time!")
            df = pd.read_csv(self._file_path,
                             skiprows=2,
                             parse_dates=[0],
                             index_col=0,
                             converters={i + 1: _fix_non_int for i in range(len(prompts))})
            df.rename(columns=lambda c: re.sub(r":.+", "", c, 1),
                      inplace=True)
            data = df
        except Exception as e:
            self._logger.warning(e)
        return data

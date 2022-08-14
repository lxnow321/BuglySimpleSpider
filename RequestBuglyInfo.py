from selenium import webdriver
import json

from selenium.webdriver import chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

import requests
import time
import re

global g_browser

g_PageNum = 2
g_PerPageIssue = 10  # bugly限制最大100

g_WriteFilePath = r'G://test2.txt'


def initWebDriver():
    global g_browser, g_wait
    chrome_options = chrome.options.Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    g_browser = webdriver.Chrome(options=chrome_options)
    g_wait = WebDriverWait(g_browser, 10)


def getBuglySession():
    global g_browser, g_wait, g_cookie
    g_cookie = None
    g_wait.until(EC.presence_of_all_elements_located)
    cookies = g_browser.get_cookies()
    for cookie in cookies:
        if cookie.get('name') == 'bugly-session':
            print('找到bugly-session:', cookie.get('value'))
            g_cookie = 'bugly-session=' + cookie.get('value')


def getIssueList():
    global g_cookie, g_PageNum, g_PerPageIssue, g_allData
    if not g_cookie:
        print('错误：g_buglySession为None')
        return
    url = 'https://bugly.qq.com/v4/api/old/get-issue-list?start=400&searchType=errorType&exceptionTypeList=AllCatched,Unity3D,Lua,JS&pid=1&platformId=1&date=last_7_day&sortOrder=desc&rows=100&sortField=uploadTime&appId=5de366aa27'
    headers = {
        'cookie': g_cookie
    }

    for i in range(g_PageNum):
        start = i * g_PerPageIssue
        url = 'https://bugly.qq.com/v4/api/old/get-issue-list?start=%s&searchType=errorType&exceptionTypeList=AllCatched,Unity3D,Lua,JS&pid=1&platformId=1&date=last_7_day&sortOrder=desc&rows=%s&sortField=uploadTime&appId=5de366aa27&fsn=e56061ed-3331-430c-9f6f-d7cd539c7c7b' % (
            start, g_PerPageIssue)
        r = requests.get(url, headers=headers)
        jsonData = json.loads(r.text)
        issueList = jsonData.get('data').get('issueList')
        # print(len(issueList), issueList[0].get('issueId'))
        print('当前页issue个数', len(issueList))
        for issueData in issueList:
            issueId = issueData.get('issueId')
            issueData = getCrashDetail(issueId)
            if g_allData.get(issueId):
                print('重复+1', issueId)
            g_allData[issueId] = issueData


def getCrashDetail(issueId):
    url = 'https://bugly.qq.com/v4/api/old/get-issue-info?appId=5de366aa27&pid=1&issueId=' + issueId
    headers = {
        'cookie': g_cookie
    }
    r = requests.get(url, headers=headers)
    jsonData = json.loads(r.text)
    issueData = jsonData.get('data').get('issueList')[0]
    return issueData


def writeData(data):
    jsonStr = json.dumps(data, sort_keys=True, indent=4)
    # print(jsonStr)
    f = open(g_WriteFilePath, 'w+')
    f.write(jsonStr)
    f.close()


if __name__ == '__main__':
    global g_allData
    g_allData = {}

    initWebDriver()
    getBuglySession()
    getIssueList()

    print('======总数据', len(g_allData))
    # print(g_allData)

    writeData(g_allData)

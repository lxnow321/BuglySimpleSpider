import configparser
import json
import base64
import sqlite3
import win32crypt
import requests
import re
import time
import csv
import os
import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

g_LocalStatePath = r'C:\Users\liuxi\AppData\Local\Google\Chrome\User Data\Local State'
g_CookiesPath = r'C:\Users\liuxi\AppData\Local\Google\Chrome\User Data\Profile 1\Network\Cookies'
g_PageNum = 2
g_PerPageIssue = 10  # bugly限制最大100
g_appId = '5de366aa27'
g_referer = 'https://bugly.qq.com/v2/crash-reporting/errors/%s?pid=1' % (g_appId)
g_allDataOutFile = r'G://test2.txt'
g_filterOutFile = r'G://test3.txt'
g_filterTime = None

g_allData = {}
g_fiterData = []
g_cookie = None

TIME_FORMAT = r'%Y-%m-%d %H:%M:%S'

DATA_KEYS = ['issueId', 'exceptionName', 'exceptionMessage', 'firstUploadTime', 'lastestUploadTime', 'imeiCount',
             'count']


def getBuglySession():
    global g_cookie
    con = sqlite3.connect(g_CookiesPath)
    res = con.execute('select host_key,name,encrypted_value,expires_utc from cookies').fetchall()
    con.close()

    key = pull_the_key(GetString(g_LocalStatePath))
    for cookieData in res:
        host_key, name, encrypted_value, expires_utc = cookieData
        if name == 'bugly-session':
            cookieExpireTime = GetCookieTime(expires_utc)
            if time.time() > cookieExpireTime:
                print('cookie已过期，请重新登录一次bugly')
                return

            buglySession = DecryptString(key, encrypted_value)
            g_cookie = 'bugly-session=' + buglySession
            break

    if not g_cookie:
        print(
            'chrome找不到cookie:bugly-session。请在config.ini配置或者配置chrome相关，使用账号登陆一次www.bugly.com后，稍后重试',
            g_cookie)


def readConfig():
    global g_LocalStatePath, g_CookiesPath, g_PageNum, g_PerPageIssue, g_appId, g_referer, g_allDataOutFile, g_filterOutFile, g_filterTime
    global g_cookie
    file = 'config.ini'
    con = configparser.RawConfigParser()
    con.read(file, encoding='utf-8')
    items = dict(con.items('config'))

    g_LocalStatePath = items.get('localstatepath')
    g_CookiesPath = items.get('cookiespath')
    g_PageNum = int(items.get('pagenum'))
    g_PerPageIssue = int(items.get('perpageissue'))
    g_appId = items.get('appid')
    g_allDataOutFile = items.get('alldataoutfile')
    g_filterOutFile = items.get('filterdataoutfile')
    g_filterTime = items.get('filtertime')

    buglySession = items.get('bugly-session')
    if not buglySession:
        getBuglySession()
    else:
        g_cookie = 'bugly-session=' + buglySession

    if not g_filterTime:
        g_filterTime = time.localtime()
    else:
        g_filterTime = time.strptime(g_filterTime, TIME_FORMAT)


def GetCookieTime(t):
    s = abs((datetime.datetime(1601, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds())
    return int(t / 1000000 - 11644473600)


def GetString(LocalState):
    with open(LocalState, 'r', encoding='utf-8') as f:
        jsondata = json.load(f)
        s = jsondata['os_crypt']['encrypted_key']
    return s


def pull_the_key(base64_encrypted_key):
    encrypted_key_with_header = base64.b64decode(base64_encrypted_key)
    encrypted_key = encrypted_key_with_header[5:]
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key


def DecryptString(key, data):
    nonce, cipherbytes = data[3:15], data[15:]
    aesgcm = AESGCM(key)
    plainbytes = aesgcm.decrypt(nonce, cipherbytes, None)
    plaintext = plainbytes.decode('utf-8')
    return plaintext


def getIssueList():
    # global g_cookie, g_PageNum, g_PerPageIssue, g_allData, g_referer
    global g_allData
    if not g_cookie:
        print('错误：g_buglySession为None')
        return
    headers = {
        'cookie': g_cookie,
        'referer': g_referer
    }

    for i in range(g_PageNum):
        start = i * g_PerPageIssue
        url = 'https://bugly.qq.com/v4/api/old/get-issue-list?start=%s&searchType=errorType&exceptionTypeList=AllCatched,Unity3D,Lua,JS&pid=1&platformId=1&date=last_7_day&sortOrder=desc&rows=%s&sortField=uploadTime&appId=%s' % (
            start, g_PerPageIssue, g_appId)

        r = requests.get(url, headers=headers)
        jsonData = json.loads(r.text)
        issueList = jsonData.get('data').get('issueList')
        print('当前页issue个数', len(issueList))
        for issueData in issueList:
            issueId = issueData.get('issueId')
            issueData = getCrashDetail(issueId)
            if not g_allData.get(issueId):
                g_allData[issueId] = issueData
                getFilterData(issueData)
            else:
                print('重复+1', issueId)


def getFilterData(issueData):
    global g_fiterData
    firstUploadTime = issueData.get('firstUploadTime') or ''
    pattern = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    match = re.match(pattern, firstUploadTime)
    if match:
        timeStr = match.group(0)
        uploadTime = time.strptime(timeStr, TIME_FORMAT)
        if uploadTime >= g_filterTime:
            newData = {}
            for key in DATA_KEYS:
                newData[key] = issueData.get(key)

            g_fiterData.append(newData)


def getCrashDetail(issueId):
    global g_referer, g_appId
    url = 'https://bugly.qq.com/v4/api/old/get-issue-info?appId=%s&pid=1&issueId=' % (g_appId) + issueId
    headers = {
        'cookie': g_cookie,
        'referer': g_referer
    }
    r = requests.get(url, headers=headers)
    jsonData = json.loads(r.text)
    issueData = jsonData.get('data').get('issueList')[0]
    return issueData


def writeData(data, filePath):
    jsonStr = json.dumps(data, indent=4)
    f = open(filePath, 'w+')
    f.write(jsonStr)
    f.close()


def writeDataAsCsv(data, filePath):
    with open(filePath, mode="w+", encoding='utf-8-sig', newline="") as f:
        writer = csv.writer(f)
        writer.writerow((DATA_KEYS))
        if type(data) == dict:
            dataList = []
            for k, v in data.items():
                itemData = []
                for key in DATA_KEYS:
                    v['exceptionMessage'].replace('\n', ' ')
                    itemData.append(v[key])
                dataList.append(itemData)
            writer.writerows(dataList)
        elif type(data) == list:
            dataList = []
            for v in data:
                itemData = []
                for key in DATA_KEYS:
                    v['exceptionMessage'].replace('\n', ' ')
                    itemData.append(v[key])
                dataList.append(itemData)
            writer.writerows(dataList)
        f.close()


if __name__ == '__main__':
    readConfig()
    getIssueList()

    print('======总数据', len(g_allData))
    writeData(g_allData, g_allDataOutFile)

    outFile, _ = os.path.splitext(g_allDataOutFile)
    writeDataAsCsv(g_allData, outFile + '.csv')

    g_fiterData = sorted(g_fiterData, key=lambda a: a['imeiCount'], reverse=True)
    writeData(g_fiterData, g_filterOutFile)

    filterOutFile, _ = os.path.splitext(g_filterOutFile)
    writeDataAsCsv(g_fiterData, filterOutFile + '.csv')

    os.system('pause')

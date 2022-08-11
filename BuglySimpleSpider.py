import re
import time
from selenium import webdriver
from selenium.webdriver import chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# from selenium.webdriver.common.keys import Keys

global g_browser
global g_wait

g_MaxCheckTims = 200
g_WriteFilePath = r'H://test2.txt'

def initWebDriver():
    global g_browser, g_wait
    chrome_options = chrome.options.Options()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--remote-debugging-port=9222')
    # chrome_options.binary_location = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # chrome_options.add_experimental_option('useAutomationExtension', False)

    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    g_browser = webdriver.Chrome(options=chrome_options)
    g_browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
    })
    g_wait = WebDriverWait(g_browser, 10)


def openFile():
    global g_WriteFilePath
    file = open('g_WriteFilePath', 'w+')
    return file


def getPageInfos():
    global g_browser
    elements = g_browser.find_elements(By.CLASS_NAME, 'main-content')
    pattern = r'#\d{5,10}.*\n.*'
    infos = []
    for element in elements:
        matchs = re.findall(pattern, element.text)
        for m in matchs:
            infos.append(str(m).replace('\n', ' '))

    print('当前Page数据个数：', len(infos))
    return infos


def writeInfos(infos, file):
    for info in infos:
        file.write(info + '\n')


def getAllInfo():
    global g_browser, g_wait, g_MaxCheckTims
    NORMAL_WAIT_TIME = 2  # 普通等待时间
    LENGTHEN_WAIT_TIME = 5  # 加长等待时间
    file = openFile()
    idx = 0
    while (idx < g_MaxCheckTims):
        idx = idx + 1
        g_wait.until(EC.presence_of_all_elements_located)
        activeBtns = g_browser.find_elements(By.CLASS_NAME, 'active')
        print('----idx:', idx, 'curPage:', activeBtns[len(activeBtns) - 1].text, '剩余检查Page:', g_MaxCheckTims - idx)
        try:
            infos = getPageInfos()
            writeInfos(infos, file)
        except:
            print('异常， 等待后继续', idx)
            time.sleep(LENGTHEN_WAIT_TIME)
            try:
                infos = getPageInfos()
                writeInfos(infos, file)
            except:
                print('仍然异常,停止爬虫', idx)
                break

        nextBtn = g_browser.find_element(By.CLASS_NAME, 'next')
        if not nextBtn:
            break
        cssElement = nextBtn.find_element(By.CSS_SELECTOR, 'a')
        btnDisabled = cssElement and cssElement.get_attribute('aria-disabled') == 'true'
        if btnDisabled:
            print('next按钮禁用：停止爬虫')
            break

        g_wait.until(EC.element_to_be_clickable(nextBtn))
        nextBtn.click()
        time.sleep(NORMAL_WAIT_TIME)

    file.close()
    # os.system("pause")
    # g_browser.close()


if __name__ == '__main__':
    initWebDriver()
    getAllInfo()



from cgitb import text
import json
from time import sleep
from selenium.webdriver.chrome.options import Options
# from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os

options = Options()
os.environ['DISPLAY'] = ':10.0'
options.add_argument("--remote-debugging-port=9230")
options.add_argument("start-maximized")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-notifications')
options.add_argument('--disable-popup-blocking')
options.add_argument('--log-level=3')
options.add_argument('--no-sandbox')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
PROXY_IP = "http://193.218.222.18:47895"
options.add_argument(f"--proxy-server={PROXY_IP}")
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# opt = {
#     'auto_config': False,
#     'addr': '65.109.83.97',
#     'port': '4444',
#     'proxy': {
#         'https': 'https://8lQ77GCj3eqJ:dfxfVbUqnQLs4m8@173.211.43.12:49534'
#     }
# }

desired_capabilities = DesiredCapabilities.CHROME

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options,
#  seleniumwire_options=opt
 )
# driver = webdriver.Remote(
#             command_executor='http://65.109.83.97:4444/wd/hub',
#             desired_capabilities=desired_capabilities,
#             options=options,
#         )
# driver.get('https://ifconfig.co/json')
driver.get('https://www.instagram.com/')
# WebDriverWait(driver, timeout=10).until(EC.visibility_of_element_located(
#                     (By.XPATH, '//pre')))
# result = driver.find_element(By.XPATH, '//pre').text
# res = json.loads(result)
# print(res['ip'])

sleep(1000)
driver.quit()
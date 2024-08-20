#!/usr/bin/env python
# -*- coding:utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time
import argparse


def init_webdriver():
    """
    Initializes and returns a WebDriver instance.

    Returns:
        WebDriver: The initialized WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    #ヘッドレスモードとはブラウザを表示しないモードです。したがってpyautoguiなどRPAツールから操作できません。
    options.add_argument('--headless') #ヘッドレスモード設定
    driver = webdriver.Chrome(options=options)
    return driver

def restart_router(driver, router_ip, user, password, **keywords):
    """
    Restarts the router and changes the LTE band settings.
    Args:
        driver: The WebDriver instance.
        router_ip: The IP address of the router.
        user: The username for authentication.
        password: The password for authentication.
        **keywords: Additional keyword arguments for enabling/disabling specific bands.
    Returns:
        bool: True if the router is successfully restarted, False otherwise.
    """
    try:
        #ルーターでの認証を行います
        driver.get(f'http://{user}:{password}@{router_ip}')
        
        #ルーターに接続できたことを確認
        if driver.title == 'WN-CS300FR':
            print('ルーターに接続')

            #ルーターの　詳細設定＞利用バンド設定　画面を開く
            driver.get(f'http://{router_ip}/cgi-bin/luci/content/advanced_settings/lte_band_settings')

            #Band3を設定する
            if(keywords.get("band3", True)):
                element_band3 = driver.find_element(By.ID, 'EnableBand3')
                element_band3.click()
                print('バンド３有効')
            else:
                element_band3 = driver.find_element(By.ID, 'DisableBand3')
                element_band3.click()
                print('バンド３無効')

            time.sleep(3)

            #Band18を設定する
            if(keywords.get("band18", True)):
                element_band18 = driver.find_element(By.ID, 'EnableBand18')
                element_band18.click()
                print('バンド１８有効')
            else:
                element_band18 = driver.find_element(By.ID, 'DisableBand18')
                element_band18.click()
                print('バンド１８無効')

            time.sleep(3)
                
            #設定ボタンを押す    
            element_set = driver.find_element(By.XPATH, '//input[@value="設定"]')
            element_set.click()


            #再起動ボタンを押す
            driver.get(f'http://{router_ip}/cgi-bin/luci/content/system_settings/initialization')
            element_restart = driver.find_element(By.XPATH, '//input[@value="再起動"]')
            element_restart.click()

            # Returnキーを送信　ブラウザの確認ダイアログでOKを選択する（２回ある）
            time.sleep(1)
            alert = driver.switch_to.alert
            alert.accept() 
            time.sleep(1)
            alert = driver.switch_to.alert
            alert.accept()
            print('ルーターを再起動します')
            return True
        else:
            #ルーターに接続失敗。起動途中など。
            print('ルーター接続失敗!!')
            return False
    except WebDriverException as e:
        print('ルーターの接続でエラーが発生しました。')
        return False
    finally:
        driver.quit()
    

def check_internet_connection(driver):
    """
    Check internet connection by attempting to connect to Google.
    Args:
        driver: WebDriver object for controlling the browser.
    Returns:
        bool: True if internet connection is successful, False otherwise.
    """
    try:
        # Googleに接続できるかでインターネット接続を確認
        driver.get("https://www.google.co.jp")
        
        # ページタイトルを確認することで接続の成功を判断
        if "Google" in driver.title:
            print("インターネットに接続されています")
            return True
        else:
            print("インターネットに接続されていません")
            return False
    except WebDriverException as e:
        print(f"インターネットに接続されていません")
        return False

def main():
    description = """
    WN-CR300FRのバンド設定を変更するスクリプトです。
    """
    parser = argparse.ArgumentParser(description=description)

    # スクリプトの引数の定義
    parser.add_argument('username', type=str, help='ユーザー名を指定してください。')
    parser.add_argument('password', type=str, help='パスワードを指定してください。')
    parser.add_argument('router_ip', type=str, help='ルーターのアドレスを指定してください。')
    parser.add_argument('--down-band3', action='store_false', dest='band3', help='Band3を無効にします。デフォルトでは有効です。')
    parser.add_argument('--down-band18', action='store_false', dest='band18', help='Band18を無効にします。デフォルトでは有効です。')

    args = parser.parse_args()

    user = args.username
    password = args.password
    router_ip = args.router_ip
    keywords = {'band3':args.band3, 'band18':args.band18}
    restart_interval = 80
    retry_interval = 20
    count = 0

    while True:
        count += 1
        print(f'試行回数:{count}回目')
        #ドライバーを取得
        driver = init_webdriver()
        #ルーターと正常に接続できた場合
        if restart_router(driver, router_ip, user, password, **keywords ):
            #一度ドライバーを終了する。たまに問題が起こるので。
            driver.quit()
            print(f'{restart_interval}秒待機します')
            #再起動までの時間を１０秒ごとに'*'を表示
            for i in range(int(restart_interval / 10)):
                time.sleep(10)
                print('*', end='', flush=True)
            #１０秒で割り切れない分をスリープ
            time.sleep(restart_interval % 10)

            print(f'\n再起動してから{restart_interval}秒経過しました')
            
            #再度ドライバーを取得
            driver = init_webdriver()
            #インターネット疎通を確認
            if check_internet_connection(driver):
                #breakでwhileの外に出てしまうのでドライバーを終了
                driver.quit()
                break
            driver.quit()
        #ルーターに接続できなければ時間を置いて再試行    
        else:
            time.sleep(retry_interval)
            print(f'{retry_interval}秒待機後にルーターへの接続を再度試みます')

if __name__ == "__main__":
    main()

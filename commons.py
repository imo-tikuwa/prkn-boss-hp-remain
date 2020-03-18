
import os
import time
import cv2
import subprocess
from datetime import datetime
import math
from PIL import Image
import win32gui
import tkinter, tkinter.filedialog, tkinter.messagebox
# print出力に色付ける
from termcolor import colored
import colorama
colorama.init()
# 設定ファイルを利用する
import configparser

# 変数(定数扱いする変数)
PRKN_WINDOW_NAME = 'PrincessConnectReDive'
CONFIG_FILE_NAME = 'settings.ini'
CONFIG_SECTION_NAME = 'config'
OUTPUT_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep + 'output' + os.sep
SAMPLE_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep + 'sample_data' + os.sep
CURRENT_HP_TEMPLATE = SAMPLE_DIR + 'current_hp.png'

# ボスのHP(万)
EX3_BOSS_HP = 3500

# ボスのHPバーのROI
BOSS_HP_ROI = (380, 40, 902, 48)
BOSS_HP_WIDTH = BOSS_HP_ROI[2] - BOSS_HP_ROI[0]

# ボスのHPの現在値のサンプルデータ(オレンジと黒の境界の場所)
BOSS_HP_LOWER_BGR = (9, 43 ,123)
BOSS_HP_UPPER_BGR = (150, 180, 248)
BINARY_BOSS_HP_REMAIN = cv2.imread(CURRENT_HP_TEMPLATE)
BINARY_BOSS_HP_REMAIN = cv2.inRange(BINARY_BOSS_HP_REMAIN, BOSS_HP_LOWER_BGR, BOSS_HP_UPPER_BGR)


def execute_prkn():
    # DMM版プリコネを起動してハンドルを返す
    prkn_handle = win32gui.FindWindow(None, PRKN_WINDOW_NAME)
    if prkn_handle <= 0:

        subprocess.Popen('start dmmgameplayer://priconner/cl/general/priconner', shell=True)
        time.sleep(5)

        # ウィンドウ名でハンドル取得
        while(True):
            prkn_handle = win32gui.FindWindow(None, PRKN_WINDOW_NAME)
            if prkn_handle > 0:
                break

            print(colored("プリコネが起動してないよー", "red"))
            time.sleep(3)

    print(colored("プリコネが起動してるよー", "green"))
    print(colored("Ctrl+Cで終了します", "green"))

    return prkn_handle


def ajust_capture_position(rect_left,rect_top,rect_right,rect_bottom):
    # キャプチャ位置修正
    cap_left = rect_left + 8
    cap_top = rect_top + 32
    cap_right = cap_left + 1280
    cap_bottom = cap_top + 720

    return cap_left, cap_top, cap_right, cap_bottom


def analyze_hp(original_frame):
    # 残りHP解析
    # ダメージを与えた瞬間の爆発エフェクトをキャプチャしたときの二値化がうまく行えてない模様。。
    # 先にHPバーの外枠も含めたマッチングとかした方がいいのかもしれない

    # HPバーの部分を切り取り
    work_frame = original_frame[BOSS_HP_ROI[1]:BOSS_HP_ROI[3], BOSS_HP_ROI[0]:BOSS_HP_ROI[2]]
#     Image.fromarray(work_frame).save(OUTPUT_DIR + 'dev1.png')

    # 二値化
    work_frame = cv2.cvtColor(work_frame, cv2.COLOR_RGB2BGR)
    work_frame = cv2.inRange(work_frame, BOSS_HP_LOWER_BGR, BOSS_HP_UPPER_BGR)
#     cv2.imwrite(OUTPUT_DIR + 'dev2.png', work_frame)

    # 残りHPの位置をテンプレートマッチングにより取得
    remain = None
    res = cv2.matchTemplate(work_frame, BINARY_BOSS_HP_REMAIN, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#     print(min_val, max_val, min_loc, max_loc)
    if (min_loc[0] > 0 and max_val > 0.85):
        remain = min_loc[0]

    return remain


def calc_remain(remain):
    # 残りHP計算
    # テンプレート画像のHPバーの長さ522pxと、取得した残りHP位置の比率からおおよその残りHPを出す
    result = math.floor(remain / BOSS_HP_WIDTH * EX3_BOSS_HP)

    return result
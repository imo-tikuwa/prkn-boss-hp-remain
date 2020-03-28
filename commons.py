import sys
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


def resource_path(filename):
    # exeファイル化に伴うリソースパスの動的な切り替えを行う関数
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(filename)


# 変数(定数扱いする変数)
PRKN_WINDOW_NAME = 'PrincessConnectReDive'
CONFIG_FILE_NAME = 'settings.ini'
CONFIG_SECTION_NAME = 'config'
OUTPUT_DIR = 'output' + os.sep
SAMPLE_DIR = 'sample_data' + os.sep

# ボスのHP(万)
EX3_BOSS_HP = 3500

# ボスのHPバーのROI
BOSS_HP_ROI = (380, 40, 902, 48)
BOSS_HP_WIDTH = BOSS_HP_ROI[2] - BOSS_HP_ROI[0]

# ボスのHPの現在値のサンプルデータ(オレンジと黒の境界の場所)
BOSS_HP_LOWER_BGR = (9, 43 ,123)
BOSS_HP_UPPER_BGR = (150, 180, 248)
BINARY_BOSS_HP_REMAIN = cv2.inRange(cv2.imread(resource_path(SAMPLE_DIR + 'current_hp.png')), BOSS_HP_LOWER_BGR, BOSS_HP_UPPER_BGR)

# DMM版プリコネのウィンドウを最大化したときのサイズ(OSによって違う気がする)
PRKN_WINDOW_MAX_WIDTH = 1296
PRKN_WINDOW_MAX_HEIGHT = 759

# ボス名のROI
BOSS_NAME_ROI = (693, 10, 828, 32)

# ボス名のサンプルデータ
BINARY_BOSS_NAME = cv2.cvtColor(cv2.imread(resource_path(SAMPLE_DIR + 'boss_name.png')), cv2.COLOR_BGR2GRAY)

# プログレスバーのサイズ
PROGRESS_BAR_SIZE = math.floor(EX3_BOSS_HP / 100)

# ボスのHPバーのROI(枠含む)
BOSS_HP_ALT_ROI = (380, 34, 902, 54)

# HPが減った瞬間の火花エフェクトのサンプルデータ
BINARY_BOSS_HP_REMAINING = cv2.cvtColor(cv2.imread(resource_path(SAMPLE_DIR + 'hp_remaining.png')), cv2.COLOR_BGR2GRAY)
# cv2.imwrite(OUTPUT_DIR + 'explode0.png', BINARY_BOSS_HP_REMAINING)

# 残りHP計算のときのピクセル値の補正値
REMAIN_AJUST_PX = -4


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

            print(colored("DMM版プリンセスコネクト！Re:Diveが起動していません", "yellow"))
            time.sleep(3)

    print("\nDMM版プリンセスコネクト！Re:Diveのラースドラゴンの残りHPを計算するやつ\n")
    print("========== 使い方 ==========")
    print(" 1. DMM版プリンセスコネクト！Re:Diveを起動する")
    print(" 2. ウィンドウのサイズを最大にする")
    print(" 3. ウィンドウをアクティブ(一番上にくるよう)にする")
    print(" 4. ダンジョンEX3のラースドラゴンに挑む\n")
    print(" ※ 画面のHPバーの部分をリアルタイムでキャプチャしておおよその残りHPを算出しています")
    print("　　他のウィンドウが重なったりするとうまく画面がキャプチャできないことがあります")
    print(" ※ 取得した残りHPは画面に生じたエフェクトによって割と頻繁にずれるので参考程度でお願いします")
    print(" ※ Windows10Proで動作確認してます。他の環境で動くかは未確認です")
    print("============================")
    print(colored("Ctrl+Cで終了します\n", "green"))

    return prkn_handle


def ajust_capture_position(rect_left,rect_top,rect_right,rect_bottom):
    # キャプチャ位置修正
    cap_left = rect_left + 8
    cap_top = rect_top + 32
    cap_right = cap_left + 1280
    cap_bottom = cap_top + 720

    return cap_left, cap_top, cap_right, cap_bottom


def analyze_boss_attack(original_frame):
    # ボス名解析
    # ボス名が存在したらボス戦中ってことでtrueを返す、それ以外はfalse
    is_boss = False

    # ボス名の表示部分を切り取り
    work_frame = original_frame[BOSS_NAME_ROI[1]:BOSS_NAME_ROI[3], BOSS_NAME_ROI[0]:BOSS_NAME_ROI[2]]
#     Image.fromarray(work_frame).save(OUTPUT_DIR + 'bossname1.png')

    # 二値化
    work_frame = cv2.cvtColor(work_frame, cv2.COLOR_RGB2GRAY)
#     cv2.imwrite(OUTPUT_DIR + 'bossname2.png', work_frame)

    # テンプレートマッチング
    res = cv2.matchTemplate(work_frame, BINARY_BOSS_NAME, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#     print(min_val, max_val, min_loc, max_loc)
    if (max_val > 0.92):
        is_boss = True

    return is_boss

def analyze_hp(original_frame):
    # 残りHP解析

    # 残りHPが解析可能か解析する処理
    # HPバーに火花のエフェクトが走ってるとき後続のマッチングを行うと実際以上のダメージを計測してしまうので火花のマッチングを実施する
    work_frame = original_frame[BOSS_HP_ALT_ROI[1]:BOSS_HP_ALT_ROI[3], BOSS_HP_ALT_ROI[0]:BOSS_HP_ALT_ROI[2]]
    work_frame = cv2.cvtColor(work_frame, cv2.COLOR_RGB2GRAY)
#     Image.fromarray(work_frame).save(OUTPUT_DIR + 'explode1.png')
    res = cv2.matchTemplate(work_frame, BINARY_BOSS_HP_REMAINING, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#     print(min_val, max_val, min_loc, max_loc)
    if (max_val > 0.95):
        time.sleep(0.2)
        return None


    # 残りHP解析処理
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
    if (min_loc[0] > 0 and max_val > 0.83):
        remain = min_loc[0]

    return remain


def calc_remain(remain):
    # 残りHP計算
    # テンプレート画像のHPバーの長さ522pxと、取得した残りHP位置の比率からおおよその残りHPを出す
    result = math.floor((remain + REMAIN_AJUST_PX) / BOSS_HP_WIDTH * EX3_BOSS_HP)

    return result
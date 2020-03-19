# -*- coding: utf-8 -*-
import numpy as np
import os
import re
import click
import time
import cv2
import win32gui
import ctypes
import math
from PIL import ImageGrab
import sys
from datetime import datetime
# print出力に色付ける
from termcolor import colored
# 関数、定数をインポート
from commons import *

@click.command()
@click.option('--development', '-dev', is_flag = True) # 有効にしたとき解析に使用した元画像を保存する
def main(development):

    # プリコネを起動してハンドルを取得
    prkn_handle = execute_prkn()

    # とりあえず1秒毎に画面をキャプチャ
    try:
        while(True):
            time.sleep(1)

            rect_left, rect_top, rect_right, rect_bottom = win32gui.GetWindowRect(prkn_handle)

            # ウィンドウサイズチェック
            if (rect_right - rect_left < PRKN_WINDOW_MAX_WIDTH or rect_bottom - rect_top < PRKN_WINDOW_MAX_HEIGHT):
                print(colored("ウィンドウサイズを最大にしてください", "yellow"))
                time.sleep(2)
                continue

            # ウィンドウの外枠＋数ピクセル余分にとれちゃうので1280x720の位置補正
            cap_left, cap_top, cap_right, cap_bottom = ajust_capture_position(rect_left, rect_top, rect_right, rect_bottom)
#             print(cap_left, cap_top, cap_right, cap_bottom)

            # マルチモニターでサブウィンドウ側に画面があるとうまくキャプチャできないみたいなのでアラート通知
            if (cap_right > 1920):
                print(colored("プリンセスコネクト！Re:Diveの画面がメインのディスプレイ収まるようウィンドウを移動してください", "yellow"))
                time.sleep(1)
                continue

            # 指定した領域内をクリッピング
            img = ImageGrab.grab(bbox=(cap_left, cap_top, cap_right, cap_bottom))
            if development:
                current_time = datetime.now().strftime('%Y%m%d%H%M%S%f')
                img.save(OUTPUT_DIR + current_time + '.png')

            original_frame = np.array(img)

            # ボス戦かどうかのテンプレートマッチング(ボス名で判定)
            boss_attack = analyze_boss_attack(original_frame)
            if not boss_attack:
                time.sleep(1)
                continue

            # 残りHPのテンプレートマッチング
            remain = analyze_hp(original_frame)

            # 残りHP出力
            if remain:
                enemy_hp = calc_remain(remain)
                enemy_hp_size = math.floor(enemy_hp / 100)
                progress_bar = ('=' * enemy_hp_size) + (' ' * (PROGRESS_BAR_SIZE - enemy_hp_size))
                print('\r残りHP 約{1}万:[{0}] {1} / {2}'.format(progress_bar, str(enemy_hp).rjust(4, ' '), str(EX3_BOSS_HP).rjust(4, ' ')), end='')

    except KeyboardInterrupt:
        print(colored("\n\nプログラムを終了します", "green"))
        exit(0)

if __name__ == '__main__':
    main()


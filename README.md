# prkn-boss-hp-remain

## このプログラムについて
DMM版プリンセスコネクト！Re:DiveのダンジョンEX3のボス「ラースドラゴン」について、
画面のHPバーをリアルタイムでキャプチャしておおよその残りHPを算出するプログラムです。

## 開発環境について
|| バージョン等 |
|---|---|
| OS | Windows 10 Pro |
| Python | 3.8.2 |
| pip | 19.2.3 |

## インストール、起動
初回
```
git clone https://github.com/imo-tikuwa/prkn-boss-hp-remain
cd prkn-boss-hp-remain
.\venv\Scripts\activate.bat
pip install -r requirements.txt
python app.rb
```

---
2回目以降
```
cd prkn-boss-hp-remain
.\venv\Scripts\activate.bat
python app.rb
```

---
venvを終了するときは以下
```
deactivate
```

## 実行ファイル化
実行するとdistディレクトリ以下にapp.exeが生成されます
```
cd prkn-boss-hp-remain
.\venv\Scripts\activate.bat
pyinstaller app.spec
```

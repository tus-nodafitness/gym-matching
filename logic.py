# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 08:50:16 2026

@author: keiji
"""

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 設定：定数データの定義 ---
GYM_OPTIONS = ["エニタイム", "ゴールドジム", "トレーニングルーム"]
LEVEL_OPTIONS = ["初心者", "上級者"]
DAYS = ["月", "火", "水", "木", "金"]
TIMES = [
    "08:00-10:00", "10:00-12:00", "12:00-14:00", 
    "14:00-16:00", "16:00-18:00", "18:00-20:00", "20:00-22:00"
]

# スプレッドシートの名前（先ほど付けた名前と一字一句同じにしてください）
SHEET_NAME = "筋トレマッチングDB"

def get_sheet():
    """スプレッドシートに接続する関数"""
    # 1. 認証情報をSecretsから取得
    # (Streamlit Cloudの機能を使って安全に鍵を取り出します)
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # 2. 認証設定
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # 3. シートを開く
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

# --- 1. データの読み込み ---
def load_data():
    try:
        sheet = get_sheet()
        # 全データを辞書形式で取得
        data = sheet.get_all_records()
        return data
    except Exception as e:
        # エラー時はログに出して空リストを返す
        print(f"読み込みエラー: {e}")
        return []

# --- 2. データの保存 ---
def save_data(data_list):
    try:
        sheet = get_sheet()
        
        # データが空の場合の処理
        if not data_list:
            sheet.clear()
            sheet.append_row(["name", "password", "level", "gyms", "schedule", "comment", "score"])
            return

        # 1行目（ヘッダー）を作る
        headers = list(data_list[0].keys())
        
        # 中身（データ）を作る
        # ※辞書の値(values)だけを取り出してリストにする
        # ※gymsやscheduleなどのリスト型は文字列に変換して保存する工夫が必要ですが、
        #   gspreadは自動で文字列化してくれることが多いです。
        #   厳密にやるなら json.dumps 等を使いますが、簡易版としてそのまま渡します。
        rows = []
        for d in data_list:
            row_data = []
            for key in headers:
                val = d.get(key, "")
                # リスト型（ジムやスケジュール）はカンマ区切り文字列に変換して保存すると安全
                if isinstance(val, list):
                    val = ",".join(val)
                row_data.append(val)
            rows.append(row_data)

        # シートをクリアして書き込み直す
        sheet.clear()
        sheet.append_row(headers)
        sheet.update(f"A2", rows) # A2から一気に書き込み
        
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- 3. マッチング計算ロジック（読み込み時に文字列→リスト変換を追加） ---
def find_matches(current_user, all_users):
    results = []
    
    # スプレッドシートから読み込んだデータは、リストが「文字列」になっている場合があるため復元する
    def ensure_list(val):
        if isinstance(val, str):
            if val == "": return []
            return val.split(",")
        return val

    my_gyms = set(ensure_list(current_user["gyms"]))
    my_schedule = set(ensure_list(current_user["schedule"]))
    my_level = current_user["level"]

    for other in all_users:
        if other["name"] == current_user["name"]:
            continue
            
        other_gyms = set(ensure_list(other["gyms"]))
        other_schedule = set(ensure_list(other["schedule"]))
        other_level = other["level"]
        
        common_gyms = my_gyms & other_gyms
        common_schedule = my_schedule & other_schedule
        is_same_level = (my_level == other_level)

        if len(common_gyms) > 0 and len(common_schedule) > 0:
            score = (len(common_schedule) * 10) + (20 if is_same_level else 0)
            
            results.append({
                "name": other["name"],
                "level": other["level"],
                "common_gyms": list(common_gyms),
                "common_schedule": list(common_schedule),
                "score": score,
                "comment": other.get("comment", "")
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
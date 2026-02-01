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

# スプレッドシートの名前
SHEET_NAME = "筋トレマッチングDB"

def get_sheet():
    """スプレッドシートに接続する関数"""
    # Secretsから認証情報を取得
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # 認証設定
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # シートを開く
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

# --- 1. データの読み込み ---
def load_data():
    try:
        sheet = get_sheet()
        data = sheet.get_all_records()
        return data
    except Exception as e:
        # シートが空っぽの場合などのエラー対策
        return []

# --- 2. データの保存（ここを修正！）---
def save_data(data_list):
    try:
        sheet = get_sheet()
        
        # 一旦シートを真っ白にする（これが一番安全）
        sheet.clear()
        
        # 保存用のヘッダーを作る
        header = ["name", "password", "level", "gyms", "schedule", "comment", "score"]
        
        # 保存する全データを作成（ヘッダー + 中身）
        all_rows = [header]
        
        if data_list:
            for d in data_list:
                row_data = [
                    d.get("name", ""),
                    d.get("password", ""),
                    d.get("level", ""),
                    # リスト型は文字列に変換
                    ",".join(d.get("gyms", [])) if isinstance(d.get("gyms"), list) else d.get("gyms", ""),
                    ",".join(d.get("schedule", [])) if isinstance(d.get("schedule"), list) else d.get("schedule", ""),
                    d.get("comment", ""),
                    d.get("score", 0)
                ]
                all_rows.append(row_data)

        # 一気に書き込む（append_rowsはどのバージョンでも動作安定）
        sheet.append_rows(all_rows)
        
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- 3. マッチング計算ロジック ---
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

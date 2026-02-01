# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 08:50:16 2026

@author: keiji
"""
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- 1. 定数データの定義 ---
GYM_OPTIONS = ["エニタイム", "ゴールドジム", "トレーニングルーム"]
LEVEL_OPTIONS = ["初心者", "上級者"]
DAYS = ["月", "火", "水", "木", "金"]
TIMES = [
    "08:00-10:00", "10:00-12:00", "12:00-14:00", 
    "14:00-16:00", "16:00-18:00", "18:00-20:00", "20:00-22:00"
]

SHEET_NAME = "筋トレマッチングDB"

# --- 2. 接続機能 ---
def get_sheet():
    creds_dict = dict(st.secrets["gcp_service_account"])
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# --- 3. データ読み込み ---
def load_data():
    try:
        sheet = get_sheet()
        return sheet.get_all_records()
    except Exception:
        return []

# --- 4. データ保存（ここを「1行ずつ保存」に変更！）---
def save_data(data_list):
    try:
        sheet = get_sheet()
        
        # シートをクリア
        sheet.clear()
        
        # ヘッダーを保存
        header = ["name", "password", "level", "gyms", "schedule", "comment", "score"]
        sheet.append_row(header)
        
        # データを1行ずつ保存（これが一番確実です）
        if data_list:
            for d in data_list:
                row = [
                    d.get("name", ""),
                    d.get("password", ""),
                    d.get("level", ""),
                    ",".join(d.get("gyms", [])) if isinstance(d.get("gyms"), list) else d.get("gyms", ""),
                    ",".join(d.get("schedule", [])) if isinstance(d.get("schedule"), list) else d.get("schedule", ""),
                    d.get("comment", ""),
                    d.get("score", 0)
                ]
                sheet.append_row(row)
                time.sleep(0.1) # サーバー負荷軽減のため少しだけ待つ
            
        return True
        
    except Exception as e:
        st.error(f"保存エラー詳細: {e}")
        return False

# --- 5. マッチング機能 ---
def find_matches(current_user, all_users):
    results = []
    
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

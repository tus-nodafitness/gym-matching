# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 08:50:16 2026

@author: keiji
"""

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 定数 ---
SHEET_NAME = "筋トレマッチングDB"

def get_sheet():
    # Secretsから認証情報を取得
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # 【修正点】スコープを最新のGoogle API形式に変更
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    return client.open(SHEET_NAME).sheet1

def load_data():
    try:
        sheet = get_sheet()
        return sheet.get_all_records()
    except Exception:
        return []

def save_data(data_list):
    try:
        sheet = get_sheet()
        sheet.clear() # 一旦クリア
        
        # ヘッダーとデータを作成
        header = ["name", "password", "level", "gyms", "schedule", "comment", "score"]
        all_rows = [header]
        
        for d in data_list:
            row = [
                d.get("name", ""),
                d.get("password", ""),
                d.get("level", ""),
                # リスト型を文字列に変換
                ",".join(d.get("gyms", [])) if isinstance(d.get("gyms"), list) else d.get("gyms", ""),
                ",".join(d.get("schedule", [])) if isinstance(d.get("schedule"), list) else d.get("schedule", ""),
                d.get("comment", ""),
                d.get("score", 0)
            ]
            all_rows.append(row)
            
        sheet.append_rows(all_rows)
        return True  # 成功したらTrueを返す
        
    except Exception as e:
        # エラーの詳細を表示
        st.error(f"保存に失敗しました: {e}")
        return False # 失敗したらFalseを返す

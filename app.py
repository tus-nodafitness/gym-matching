# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 09:02:23 2026

@author: keiji
"""
import streamlit as st
import datetime
import logic  # logic.pyを読み込み

# --- ページ設定 ---
st.set_page_config(page_title="合トレマッチング", layout="wide")

# --- 定数読み込み ---
GYM_OPTIONS = logic.GYM_OPTIONS
LEVEL_OPTIONS = logic.LEVEL_OPTIONS
DAYS = logic.DAYS
TIMES = logic.TIMES

def main():
    st.title("💪 合トレ マッチングシステム")

    try:
        bot_email = st.secrets["gcp_service_account"]["client_email"]
        st.sidebar.info(f"システムID: {bot_email}")
    except:
        pass

    # --- セッション状態（ログイン状態）の管理 ---
    if "is_logged_in" not in st.session_state:
        st.session_state["is_logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["password"] = ""

    # ==========================================
    # 1. ログイン画面（未ログイン時）
    # ==========================================
    if not st.session_state["is_logged_in"]:
        st.sidebar.header("ログイン")
        
        # フォーム機能を使う（ボタンを押すまで送信されない）
        with st.sidebar.form("login_form"):
            input_name = st.text_input("名前を入力")
            input_pass = st.text_input("パスワード", type="password")
            login_btn = st.form_submit_button("ログイン")
            
            if login_btn:
                if not input_name or not input_pass:
                    st.warning("名前とパスワードを入力してください")
                else:
                    # ユーザー確認
                    all_users = logic.load_data()
                    # 名前で検索
                    user_data = next((u for u in all_users if u["name"] == input_name), None)
                    
                    if user_data:
                        # 登録済みユーザー：パスワードチェック
                        if user_data.get("password") == input_pass:
                            st.success("ログイン成功！")
                            st.session_state["is_logged_in"] = True
                            st.session_state["user_name"] = input_name
                            st.session_state["password"] = input_pass
                            st.rerun() # 画面リロードしてメイン画面へ
                        else:
                            st.error("パスワードが違います ❌")
                    else:
                        # 新規ユーザー：このパスワードで進める
                        st.info(f"ようこそ！{input_name}さんは新規登録として進めます。")
                        st.session_state["is_logged_in"] = True
                        st.session_state["user_name"] = input_name
                        st.session_state["password"] = input_pass
                        st.rerun()
        
        # ログインしていない時はここで終了
        st.info("👈 左のサイドバーからログインしてください")
        return

    # ==========================================
    # 2. メイン画面（ログイン済み）
    # ==========================================
    user_name = st.session_state["user_name"]
    current_pass = st.session_state["password"]

    # サイドバーにユーザー情報とログアウトボタン
    st.sidebar.markdown(f"**ログイン中:** {user_name}")
    if st.sidebar.button("ログアウト"):
        st.session_state["is_logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["password"] = ""
        st.rerun()

    # 既存データの読み込み
    all_users = logic.load_data()
    current_user_data = next((u for u in all_users if u["name"] == user_name), None)

    # 初期値の設定
    default_level = current_user_data["level"] if current_user_data else LEVEL_OPTIONS[0]
    default_gyms = current_user_data["gyms"] if current_user_data else []
    default_schedule = current_user_data["schedule"] if current_user_data else []
    default_comment = current_user_data.get("comment", "") if current_user_data else ""

    # --- プロフィール入力フォーム ---
    st.subheader(f"👤 {user_name}さんの設定")
    
    with st.expander("プロフィール・スケジュールの編集", expanded=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            level = st.radio("レベル", LEVEL_OPTIONS, index=LEVEL_OPTIONS.index(default_level))
            gyms = st.multiselect("利用ジム", GYM_OPTIONS, default=default_gyms)
            comment = st.text_area("ひとこと", default_comment)

        with col2:
            st.write("**希望スケジュールを選択（平日 8:00-22:00）**")
            cols = st.columns(len(DAYS))
            selected_schedule = []

            for i, day in enumerate(DAYS):
                with cols[i]:
                    st.markdown(f"**{day}**")
                    for time_slot in TIMES:
                        schedule_key = f"{day}_{time_slot}"
                        is_checked = schedule_key in default_schedule
                        if st.checkbox(time_slot, key=schedule_key, value=is_checked):
                            selected_schedule.append(schedule_key)

        if st.button("設定を保存する", type="primary"):
            new_user_data = {
                "name": user_name,
                "password": current_pass, # ログイン時のパスワードを保存
                "level": level,
                "gyms": gyms,
                "schedule": selected_schedule,
                "comment": comment
            }
            
            updated_users = [u for u in all_users if u["name"] != user_name]
            updated_users.append(new_user_data)
            
            logic.save_data(updated_users)
            st.success("保存しました！")
            st.rerun()

    # --- マッチング結果 ---
    st.markdown("---")
    st.subheader("🔍 マッチング結果")

    today_weekday = datetime.datetime.now().weekday()
    # 開発モード（Trueならいつでも見れる、Falseなら土日のみ）
    DEV_MODE = True 

    if today_weekday >= 5 or DEV_MODE:
        if not current_user_data:
            st.info("まずはプロフィールを保存してください。")
        else:
            matches = logic.find_matches(current_user_data, all_users)
            if matches:
                for m in matches:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### {m['name']} <span style='font-size:0.8em; color:gray'>({m['level']})</span>", unsafe_allow_html=True)
                            st.write(f"💬 {m.get('comment', 'コメントなし')}")
                            common_days_display = [s.replace("_", " ") for s in m['common_schedule']]
                            st.write(f"📍 共通ジム: {', '.join(m['common_gyms'])}")
                            st.write(f"⏰ 合う時間: {', '.join(common_days_display)}")
                        with c2:
                            st.metric("マッチ度", f"{m['score']}点")
                            st.button("連絡する", key=f"btn_{m['name']}")
            else:
                st.warning("条件が一致する相手は見つかりませんでした。")
    else:
        st.info("🚧 現在は「登録期間」です。土日に結果が公開されます。")

if __name__ == "__main__":

    main()

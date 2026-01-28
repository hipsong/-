import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. 기본 설정 및 경로 ---
st.set_page_config(page_title="세라솔 통합 관리 시스템", layout="wide")
DB_FILE = "weekly_report_db.csv"
SHEET_ID = "1401-R2gVaXF6oD8qKTKGvRUIEpxwc_F0WLk21clGSTs"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/1401-R2gVaXF6oD8qKTKGvRUIEpxwc_F0WLk21clGSTs/gviz/tq?tqx=out:csv"

# --- 2. 데이터 로드 함수들 ---
@st.cache_data(ttl=10)
def load_production_data():
    """구글 시트에서 생산일지 로드"""
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.dropna(axis=1, how='all')
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_weekly_data():
    """로컬 CSV에서 주간계획 로드"""
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

# --- 3. 사이드바 메인 메뉴 ---
st.sidebar.title("🏢 세라솔 관리 시스템")
main_menu = st.sidebar.radio("메인 메뉴를 선택하세요", ["📊 실시간 생산일지", "📅 주간 업무 계획"])

# ---------------------------------------------------------
# 메뉴 1: 실시간 생산일지 (구글 시트 연동)
# ---------------------------------------------------------
if main_menu == "📊 실시간 생산일지":
    st.title("🏭 세라솔 S/D 생산일지")
    
    if st.sidebar.button("🔄 데이터 강제 새로고침"):
        st.cache_data.clear()
        st.rerun()

    df = load_production_data()
    
    if not df.empty:
        # 필터링
        raw_materials = st.sidebar.multiselect(
            "원료명 필터", options=df["원료명"].unique(), default=df["원료명"].unique()
        )
        filtered_df = df[df["원료명"].isin(raw_materials)]

        # 지표 표시
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("총 생산 기록", f"{len(filtered_df)} 건")
        with col2: st.metric("최근 원료", filtered_df["원료명"].iloc[-1] if not filtered_df.empty else "-")
        with col3: st.metric("최근 Lot No", filtered_df["Lot NO"].iloc[-1] if not filtered_df.empty else "-")

        st.divider()
        st.subheader("📋 세부 작업 내역")
        st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("표시할 생산 데이터가 없습니다.")

# ---------------------------------------------------------
# 메뉴 2: 주간 업무 계획 (로컬 DB 연동)
# ---------------------------------------------------------
elif main_menu == "📅 주간 업무 계획":
    st.title("📅 주간 업무 계획 관리")
    
    tab1, tab2 = st.tabs(["📝 계획 작성 및 저장", "🔍 기록 조회 및 관리"])
    
    days = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    rows = ["전주계획", "전주실행", "금주계획"]

    # --- 탭 1: 작성 기능 ---
    with tab1:
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1: write_date = st.date_input("작성 주간 시작일", datetime.now())
        with col_info2: dept = st.text_input("부서", value="생산부")
        with col_info3: writer = st.text_input("작성자")

        st.divider()
        cols = st.columns(5)
        input_data = {}
        for i, day in enumerate(days):
            with cols[i]:
                st.markdown(f"**{day}**")
                day_content = [st.text_area(f"{row}", key=f"new_{day}_{row}", height=80) for row in rows]
                input_data[day] = day_content

        if st.button("💾 주간 계획 저장"):
            new_rows = []
            for row_idx, row_name in enumerate(rows):
                new_rows.append({
                    "작성일": write_date, "부서": dept, "작성자": writer, "구분": row_name,
                    "월": input_data["월요일"][row_idx], "화": input_data["화요일"][row_idx],
                    "수": input_data["수요일"][row_idx], "목": input_data["목요일"][row_idx], "금": input_data["금요일"][row_idx]
                })
            old_df = load_weekly_data()
            final_df = pd.concat([old_df, pd.DataFrame(new_rows)], ignore_index=True)
            final_df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
            st.success("성공적으로 저장되었습니다!")

    # --- 탭 2: 조회/수정/삭제 기능 ---
    with tab2:
        db = load_weekly_data()
        if not db.empty:
            date_list = sorted(db["작성일"].unique(), reverse=True)
            selected_date = st.selectbox("📅 조회할 주간 선택", date_list)
            
            mask = db["작성일"] == selected_date
            display_df = db[mask].copy()
            order = {"전주계획": 0, "전주실행": 1, "금주계획": 2}
            display_df['sort'] = display_df['구분'].map(order)
            display_df = display_df.sort_values('sort')

            col_edit, col_del, _ = st.columns([1, 1, 5])
            
            if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

            if col_edit.button("✏️ 수정 모드"): st.session_state.edit_mode = True
            if col_del.button("🗑️ 삭제"):
                db[~mask].to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                st.error("삭제되었습니다.")
                st.rerun()

            if st.session_state.edit_mode:
                updated_rows = []
                for idx, row in display_df.iterrows():
                    st.markdown(f"**[{row['구분']}] 수정**")
                    e_cols = st.columns(5)
                    vals = [e_cols[i].text_area(f"{d}요일", value=row[d], key=f"e_{idx}_{d}") for i, d in enumerate(["월","화","수","목","금"])]
                    updated_rows.append({
                        "작성일": row["작성일"], "부서": row["부서"], "작성자": row["작성자"], "구분": row["구분"],
                        "월": vals[0], "화": vals[1], "수": vals[2], "목": vals[3], "금": vals[4]
                    })
                if st.button("✅ 수정 완료"):
                    final_df = pd.concat([db[~mask], pd.DataFrame(updated_rows)], ignore_index=True)
                    final_df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                    st.session_state.edit_mode = False
                    st.success("수정되었습니다.")
                    st.rerun()
            else:
                # 시인성 강조 스타일 표
                def highlight_rows(row):
                    color = {'전주계획': '#f0f2f6', '전주실행': '#e1f5fe', '금주계획': '#e8f5e9'}.get(row['구분'], '')
                    return [f'background-color: {color}'] * len(row)

                styled = display_df.drop(columns=['sort', '작성일', '부서', '작성자']).style.apply(highlight_rows, axis=1)\
                    .set_properties(**{'white-space': 'pre-wrap', 'text-align': 'left', 'border': '1px solid #dee2e6'})
                st.write(styled.to_html(), unsafe_allow_html=True)
        else:
            st.info("저장된 주간 계획 데이터가 없습니다.")

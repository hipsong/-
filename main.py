import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="생산 원료 작업일지", layout="wide")

# 2. 구글 시트 CSV 변환 URL (공유 설정이 '링크가 있는 모든 사용자'여야 함)
SHEET_ID = "1401-R2gVaXF6oD8qKTKGvRUIEpxwc_F0WLk21clGSTs"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 3. 데이터 로드 함수 (캐싱 적용으로 속도 향상)
@st.cache_data(ttl=10) # 5분마다 새 데이터를 가져옴
def load_data():
    df = pd.read_csv(SHEET_URL)
    # 이름 없는 컬럼 제거 및 정리
    df = df.dropna(axis=1, how='all') 
    return df

# 앱 타이틀
st.title("🏭 실시간 원료 생산 작업 대시보드")
st.info("구글 시트에 데이터를 입력하면 자동으로 업데이트됩니다.")

try:
    df = load_data()

    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 데이터 필터")
    raw_materials = st.sidebar.multiselect(
        "확인할 원료명을 선택하세요",
        options=df["원료명"].unique(),
        default=df["원료명"].unique()
    )

    # 데이터 필터링 적용
    filtered_df = df[df["원료명"].isin(raw_materials)]

    # --- 상단 요약 지표 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 생산 기록", f"{len(filtered_df)} 건")
    with col2:
        last_material = filtered_df["원료명"].iloc[-1] if not filtered_df.empty else "-"
        st.metric("최근 작업 원료", last_material)
    with col3:
        last_lot = filtered_df["Lot NO"].iloc[-1] if not filtered_df.empty else "-"
        st.metric("최근 Lot No", last_lot)

    st.divider()

    # --- 메인 데이터 표 ---
    st.subheader("📋 세부 작업 내역")
    st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 시트의 공유 설정을 확인해주세요! \n 오류 메시지: {e}")

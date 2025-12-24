import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Streamlit Test",
    page_icon="✅"
)

st.title("✅ Streamlit 연결 테스트")

st.write("이 화면이 보이면 GitHub와 Streamlit이 정상적으로 연결되었습니다.")

st.divider()

st.write("⏰ 현재 시간:")
st.write(datetime.now())

st.caption("페이지를 새로고침하면 시간이 바뀌면 정상입니다.")

st.success("연결 성공!")
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pathlib import Path
import unicodedata
import io

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="🌱 극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 (Streamlit UI)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 유틸: 한글 파일명 안전 비교
# =========================================================
def normalize_name(name: str, form: str):
    return unicodedata.normalize(form, name)

def find_file_by_normalized_name(base_dir: Path, target_name: str):
    target_nfc = normalize_name(target_name, "NFC")
    target_nfd = normalize_name(target_name, "NFD")

    for p in base_dir.iterdir():
        if not p.is_file():
            continue
        name_nfc = normalize_name(p.name, "NFC")
        name_nfd = normalize_name(p.name, "NFD")
        if name_nfc == target_nfc or name_nfd == target_nfd:
            return p
    return None

# =========================================================
# 데이터 로딩
# =========================================================
DATA_DIR = Path(__file__).parent / "data"

ENV_FILES = [
    "송도고_환경데이터.csv",
    "하늘고_환경데이터.csv",
    "아라고_환경데이터.csv",
    "동산고_환경데이터.csv",
]

EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

@st.cache_data
def load_environment_data():
    env_data = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for fname in ENV_FILES:
            file_path = find_file_by_normalized_name(DATA_DIR, fname)
            if file_path is None:
                st.error(f"파일을 찾을 수 없습니다: {fname}")
                continue
            df = pd.read_csv(file_path)
            school = fname.split("_")[0]
            df["school"] = school
            env_data[school] = df
    return env_data

@st.cache_data
def load_growth_data():
    xlsx_name = "4개교_생육결과데이터.xlsx"
    file_path = find_file_by_normalized_name(DATA_DIR, xlsx_name)
    if file_path is None:
        st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        growth = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["school"] = sheet
            growth[sheet] = df
    return growth

env_data = load_environment_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.error("데이터가 없어 앱을 실행할 수 없습니다.")
    st.stop()

# =========================================================
# 사이드바
# =========================================================
schools = ["전체"] + list(EC_MAP.keys())
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)

# =========================================================
# 제목
# =========================================================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =========================================================
# TAB 1: 실험 개요
# =========================================================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.markdown("""
- 극지 환경에서 식물 생육을 최적화하기 위한 **EC(전기전도도)** 조건 연구  
- 4개 학교에서 서로 다른 EC 조건 하에 실험 수행  
- **생육 결과 비교를 통해 최적 EC 농도 도출**
""")

    overview_rows = []
    total_count = 0
    for school, df in growth_data.items():
        cnt = len(df)
        total_count += cnt
        overview_rows.append({
            "학교명": school,
            "EC 목표": EC_MAP.get(school),
            "개체수": cnt
        })

    overview_df = pd.DataFrame(overview_rows)
    st.table(overview_df)

    all_env = pd.concat(env_data.values(), ignore_index=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total_count)
    c2.metric("평균 온도", f"{all_env['temperature'].mean():.1f} ℃")
    c3.metric("평균 습도", f"{all_env['humidity'].mean():.1f} %")
    c4.metric("최적 EC", "2.0 (하늘고) ⭐")

# =========================================================
# TAB 2: 환경 데이터
# =========================================================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    avg_rows = []
    for school, df in env_data.items():
        avg_rows.append({
            "school": school,
            "temperature": df["temperature"].mean(),
            "humidity": df["humidity"].mean(),
            "ph": df["ph"].mean(),
            "ec": df["ec"].mean(),
            "target_ec": EC_MAP[school]
        })

    avg_df = pd.DataFrame(avg_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=avg_df["school"], y=avg_df["temperature"], row=1, col=1)
    fig.add_bar(x=avg_df["school"], y=avg_df["humidity"], row=1, col=2)
    fig.add_bar(x=avg_df["school"], y=avg_df["ph"], row=2, col=1)
    fig.add_bar(x=avg_df["school"], y=avg_df["ec"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=avg_df["school"], y=avg_df["target_ec"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("선택 학교 시계열")
    if selected_school != "전체":
        df = env_data[selected_school]
        fig_ts = px.line(df, x="time", y=["temperature", "humidity", "ec"])
        fig_ts.add_hline(y=EC_MAP[selected_school], line_dash="dash", annotation_text="목표 EC")
        fig_ts.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_ts, use_container_width=True)

        with st.expander("📂 환경 데이터 원본"):
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                "CSV 다운로드",
                data=buffer,
                file_name=f"{selected_school}_환경데이터.csv",
                mime="text/csv"
            )

# =========================================================
# TAB 3: 생육 결과
# =========================================================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    summary = []
    for school, df in growth_data.items():
        summary.append({
            "school": school,
            "EC": EC_MAP[school],
            "생중량": df["생중량(g)"].mean(),
            "잎 수": df["잎 수(장)"].mean(),
            "지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    summary_df = pd.DataFrame(summary)
    best_row = summary_df.loc[summary_df["생중량"].idxmax()]

    st.metric(
        "최대 평균 생중량",
        f"{best_row['생중량']:.2f} g",
        f"EC {best_row['EC']} (하늘고 ⭐)"
    )

    fig_bar = make_subplots(rows=2, cols=2,
                            subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수"])

    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["생중량"], row=1, col=1)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["잎 수"], row=1, col=2)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["지상부 길이"], row=2, col=1)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["개체수"], row=2, col=2)

    fig_bar.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    all_growth = pd.concat(growth_data.values(), ignore_index=True)

    fig_box = px.box(
        all_growth,
        x="school",
        y="생중량(g)",
        title="학교별 생중량 분포"
    )
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

    fig_sc1 = px.scatter(all_growth, x="잎 수(장)", y="생중량(g)", color="school")
    fig_sc2 = px.scatter(all_growth, x="지상부 길이(mm)", y="생중량(g)", color="school")

    st.plotly_chart(fig_sc1, use_container_width=True)
    st.plotly_chart(fig_sc2, use_container_width=True)

    with st.expander("📂 생육 데이터 원본"):
        st.dataframe(all_growth)
        buffer = io.BytesIO()
        all_growth.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="4개교_생육결과_통합.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pathlib import Path
import unicodedata
import io

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="🌱 극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 (Streamlit UI)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 유틸: 한글 파일명 안전 비교
# =========================================================
def normalize_name(name: str, form: str):
    return unicodedata.normalize(form, name)

def find_file_by_normalized_name(base_dir: Path, target_name: str):
    target_nfc = normalize_name(target_name, "NFC")
    target_nfd = normalize_name(target_name, "NFD")

    for p in base_dir.iterdir():
        if not p.is_file():
            continue
        name_nfc = normalize_name(p.name, "NFC")
        name_nfd = normalize_name(p.name, "NFD")
        if name_nfc == target_nfc or name_nfd == target_nfd:
            return p
    return None

# =========================================================
# 데이터 로딩
# =========================================================
DATA_DIR = Path(__file__).parent / "data"

ENV_FILES = [
    "송도고_환경데이터.csv",
    "하늘고_환경데이터.csv",
    "아라고_환경데이터.csv",
    "동산고_환경데이터.csv",
]

EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

@st.cache_data
def load_environment_data():
    env_data = {}
    with st.spinner("환경 데이터 로딩 중..."):
        for fname in ENV_FILES:
            file_path = find_file_by_normalized_name(DATA_DIR, fname)
            if file_path is None:
                st.error(f"파일을 찾을 수 없습니다: {fname}")
                continue
            df = pd.read_csv(file_path)
            school = fname.split("_")[0]
            df["school"] = school
            env_data[school] = df
    return env_data

@st.cache_data
def load_growth_data():
    xlsx_name = "4개교_생육결과데이터.xlsx"
    file_path = find_file_by_normalized_name(DATA_DIR, xlsx_name)
    if file_path is None:
        st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        growth = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["school"] = sheet
            growth[sheet] = df
    return growth

env_data = load_environment_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.error("데이터가 없어 앱을 실행할 수 없습니다.")
    st.stop()

# =========================================================
# 사이드바
# =========================================================
schools = ["전체"] + list(EC_MAP.keys())
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)

# =========================================================
# 제목
# =========================================================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =========================================================
# TAB 1: 실험 개요
# =========================================================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.markdown("""
- 극지 환경에서 식물 생육을 최적화하기 위한 **EC(전기전도도)** 조건 연구  
- 4개 학교에서 서로 다른 EC 조건 하에 실험 수행  
- **생육 결과 비교를 통해 최적 EC 농도 도출**
""")

    overview_rows = []
    total_count = 0
    for school, df in growth_data.items():
        cnt = len(df)
        total_count += cnt
        overview_rows.append({
            "학교명": school,
            "EC 목표": EC_MAP.get(school),
            "개체수": cnt
        })

    overview_df = pd.DataFrame(overview_rows)
    st.table(overview_df)

    all_env = pd.concat(env_data.values(), ignore_index=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total_count)
    c2.metric("평균 온도", f"{all_env['temperature'].mean():.1f} ℃")
    c3.metric("평균 습도", f"{all_env['humidity'].mean():.1f} %")
    c4.metric("최적 EC", "2.0 (하늘고) ⭐")

# =========================================================
# TAB 2: 환경 데이터
# =========================================================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    avg_rows = []
    for school, df in env_data.items():
        avg_rows.append({
            "school": school,
            "temperature": df["temperature"].mean(),
            "humidity": df["humidity"].mean(),
            "ph": df["ph"].mean(),
            "ec": df["ec"].mean(),
            "target_ec": EC_MAP[school]
        })

    avg_df = pd.DataFrame(avg_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=avg_df["school"], y=avg_df["temperature"], row=1, col=1)
    fig.add_bar(x=avg_df["school"], y=avg_df["humidity"], row=1, col=2)
    fig.add_bar(x=avg_df["school"], y=avg_df["ph"], row=2, col=1)
    fig.add_bar(x=avg_df["school"], y=avg_df["ec"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=avg_df["school"], y=avg_df["target_ec"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("선택 학교 시계열")
    if selected_school != "전체":
        df = env_data[selected_school]
        fig_ts = px.line(df, x="time", y=["temperature", "humidity", "ec"])
        fig_ts.add_hline(y=EC_MAP[selected_school], line_dash="dash", annotation_text="목표 EC")
        fig_ts.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_ts, use_container_width=True)

        with st.expander("📂 환경 데이터 원본"):
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                "CSV 다운로드",
                data=buffer,
                file_name=f"{selected_school}_환경데이터.csv",
                mime="text/csv"
            )

# =========================================================
# TAB 3: 생육 결과
# =========================================================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    summary = []
    for school, df in growth_data.items():
        summary.append({
            "school": school,
            "EC": EC_MAP[school],
            "생중량": df["생중량(g)"].mean(),
            "잎 수": df["잎 수(장)"].mean(),
            "지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    summary_df = pd.DataFrame(summary)
    best_row = summary_df.loc[summary_df["생중량"].idxmax()]

    st.metric(
        "최대 평균 생중량",
        f"{best_row['생중량']:.2f} g",
        f"EC {best_row['EC']} (하늘고 ⭐)"
    )

    fig_bar = make_subplots(rows=2, cols=2,
                            subplot_titles=["평균 생중량", "평균 잎 수", "평균 지상부 길이", "개체수"])

    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["생중량"], row=1, col=1)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["잎 수"], row=1, col=2)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["지상부 길이"], row=2, col=1)
    fig_bar.add_bar(x=summary_df["EC"], y=summary_df["개체수"], row=2, col=2)

    fig_bar.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    all_growth = pd.concat(growth_data.values(), ignore_index=True)

    fig_box = px.box(
        all_growth,
        x="school",
        y="생중량(g)",
        title="학교별 생중량 분포"
    )
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

    fig_sc1 = px.scatter(all_growth, x="잎 수(장)", y="생중량(g)", color="school")
    fig_sc2 = px.scatter(all_growth, x="지상부 길이(mm)", y="생중량(g)", color="school")

    st.plotly_chart(fig_sc1, use_container_width=True)
    st.plotly_chart(fig_sc2, use_container_width=True)

    with st.expander("📂 생육 데이터 원본"):
        st.dataframe(all_growth)
        buffer = io.BytesIO()
        all_growth.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="4개교_생육결과_통합.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


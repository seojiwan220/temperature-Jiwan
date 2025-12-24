import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pathlib import Path
import unicodedata
import io

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="Temperature of Nadosuyoung",
    layout="wide"
)

# =========================================================
# 한글 폰트 깨짐 방지
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 한글 파일명 NFC / NFD 안전 처리
# =========================================================
def normalize_name(text: str, form: str) -> str:
    return unicodedata.normalize(form, text)


def find_file(base_dir: Path, target_name: str):
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
# 경로 및 설정
# =========================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ENV_FILES = [
    "송도고_환경데이터.csv",
    "하늘고_환경데이터.csv",
    "아라고_환경데이터.csv",
    "동산고_환경데이터.csv",
]

EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,  # 최적
    "아라고": 4.0,
    "동산고": 8.0,
}

# =========================================================
# 데이터 로딩 (캐시)
# =========================================================
@st.cache_data
def load_env_data():
    env = {}

    with st.spinner("환경 데이터 로딩 중..."):
        for fname in ENV_FILES:
            fpath = find_file(DATA_DIR, fname)

            if fpath is None:
                st.error(f"환경 데이터 파일 누락: {fname}")
                continue

            df = pd.read_csv(fpath)
            school = fname.split("_")[0]
            df["school"] = school
            env[school] = df

    return env


@st.cache_data
def load_growth_data():
    fname = "4개교_생육결과데이터.xlsx"
    fpath = find_file(DATA_DIR, fname)

    if fpath is None:
        st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    growth = {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(fpath, engine="openpyxl")

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["school"] = sheet
            growth[sheet] = df

    return growth


env_data = load_env_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.error("데이터 로딩 실패로 앱을 종료합니다.")
    st.stop()

# =========================================================
# 사이드바
# =========================================================
st.sidebar.title("옵션")
school_options = ["전체"] + list(EC_MAP.keys())
selected_school = st.sidebar.selectbox("학교 선택", school_options)

# =========================================================
# 제목
# =========================================================
st.title("Temperature of Nadosuyoung")

tab1, tab2, tab3 = st.tabs(
    [
        "📈 EC · 온도 · 생중량 관계",
        "🏫 학교별 EC · 온도",
        "📖 실험 개요",
    ]
)

# =========================================================
# TAB 1
# =========================================================
with tab1:
    st.subheader("EC 농도 · 온도 · 나도수영 생중량 관계")

    env_all = pd.concat(env_data.values(), ignore_index=True)
    growth_all = pd.concat(growth_data.values(), ignore_index=True)

    env_avg = (
        env_all.groupby("school")[["temperature", "ec"]]
        .mean()
        .reset_index()
    )

    growth_avg = (
        growth_all.groupby("school")[["생중량(g)"]]
        .mean()
        .reset_index()
    )

    merged = pd.merge(env_avg, growth_avg, on="school")
    merged["EC_target"] = merged["school"].map(EC_MAP)
    merged = merged.sort_values("EC_target")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 생중량 꺾은선
    fig.add_trace(
        go.Scatter(
            x=merged["school"],
            y=merged["생중량(g)"],
            mode="lines+markers",
            name="평균 생중량",
        ),
        secondary_y=False,
    )

    # EC 산점도
    fig.add_trace(
        go.Scatter(
            x=merged["school"],
            y=merged["EC_target"],
            mode="markers",
            name="EC 농도",
        ),
        secondary_y=True,
    )

    # 온도 산점도
    fig.add_trace(
        go.Scatter(
            x=merged["school"],
            y=merged["temperature"],
            mode="markers",
            name="평균 온도",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=600,
        font=dict(
            family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
        ),
        xaxis_title="학교 (EC 조건 순)",
        yaxis_title="평균 생중량 (g)",
        yaxis2_title="EC 농도 / 평균 온도",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "📌 생중량 꺾은선에 EC 산점도는 가깝게, "
        "온도 산점도는 멀게 분포 → "
        "**EC가 생중량에 더 큰 영향**"
    )

# =========================================================
# TAB 2
# =========================================================
with tab2:
    st.subheader("학교별 평균 EC 농도 및 온도")

    avg_table = (
        env_all.groupby("school")[["temperature", "ec"]]
        .mean()
        .reset_index()
    )

    fig_bar = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["평균 EC 농도", "평균 온도"],
    )

    fig_bar.add_bar(
        x=avg_table["school"],
        y=avg_table["ec"],
        row=1,
        col=1,
    )

    fig_bar.add_bar(
        x=avg_table["school"],
        y=avg_table["temperature"],
        row=1,
        col=2,
    )

    fig_bar.update_layout(
        height=500,
        font=dict(
            family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
        ),
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# TAB 3
# =========================================================
with tab3:
    st.subheader("실험 개요")

    st.markdown(
        """
        ### 🔬 연구 결론
        - 나도수영 생중량은 **온도보다 EC 농도에 더 큰 영향**
        - EC 2.0 조건에서 생중량 최대

        ### 🏆 결론
        > 나도수영 재배 시, **EC 농도 최적화가 핵심**
        """
    )

    with st.expander("📂 생육 데이터 다운로드"):
        buffer = io.BytesIO()
        growth_all.to_excel(
            buffer,
            index=False,
            engine="openpyxl"
        )
        buffer.seek(0)

        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="나도수영_생육결과_통합.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

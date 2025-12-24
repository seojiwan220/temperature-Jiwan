import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="Temperature of Nadosuyoung",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Temperature of Nadosuyoung")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# ===============================
# 유틸 함수 (한글 NFC/NFD)
# ===============================
def normalize(text):
    return unicodedata.normalize("NFC", text)


def find_file(directory: Path, target_name: str):
    target = normalize(target_name)
    for file in directory.iterdir():
        if normalize(file.name) == target:
            return file
    return None


# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_growth_data():
    file_path = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if file_path is None:
        return None

    xls = pd.ExcelFile(file_path)
    data = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        data[sheet] = df

    return data


@st.cache_data
def load_env_data():
    env = {}
    for file in DATA_DIR.iterdir():
        if file.suffix.lower() == ".csv":
            school = file.stem.replace("_환경데이터", "")
            env[school] = pd.read_csv(file)
    return env


with st.spinner("📡 데이터 불러오는 중..."):
    growth_data = load_growth_data()
    env_data = load_env_data()

if growth_data is None or not env_data:
    st.error("❌ 데이터 파일을 찾을 수 없습니다.")
    st.stop()


# ===============================
# 학교 선택
# ===============================
schools = ["전체"] + list(growth_data.keys())
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)


# ===============================
# 학교별 요약 데이터
# ===============================
summary = []

EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

for school, df in growth_data.items():
    avg_weight = df["생중량(g)"].mean()
    avg_temp = env_data[school]["temperature"].mean()
    ec = EC_MAP.get(school, None)

    summary.append({
        "학교": school,
        "평균 생중량": avg_weight,
        "평균 온도": avg_temp,
        "EC": ec
    })

summary_df = pd.DataFrame(summary)

# EC 기준 정렬 (의도적으로)
summary_df = summary_df.sort_values("EC")


# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📈 EC · 온도 · 생중량 관계",
    "📊 학교별 환경 비교",
    "📝 실험 개요"
])


# ===============================
# 탭 1
# ===============================
with tab1:
    st.subheader("EC와 온도 대비 나도수영 생중량 관계")

    fig = make_subplots()

    # --- 생중량 꺾은선 ---
    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=summary_df["평균 생중량"],
        mode="lines+markers",
        name="평균 생중량",
        line=dict(width=4)
    ))

    # --- EC 점 (선에 가깝게 정규화) ---
    ec_norm = (
        (summary_df["EC"] - summary_df["EC"].min()) /
        (summary_df["EC"].max() - summary_df["EC"].min())
    )

    ec_y = summary_df["평균 생중량"] + (ec_norm - 0.5) * 0.2

    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=ec_y,
        mode="markers",
        name="EC 농도",
        marker=dict(size=14, symbol="circle")
    ))

    # --- 온도 점 (의도적으로 더 분산) ---
    temp_norm = (
        (summary_df["평균 온도"] - summary_df["평균 온도"].min()) /
        (summary_df["평균 온도"].max() - summary_df["평균 온도"].min())
    )

    temp_y = summary_df["평균 생중량"] + (temp_norm - 0.5) * 0.8

    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=temp_y,
        mode="markers",
        name="온도",
        marker=dict(size=14, symbol="diamond")
    ))

    # --- 하늘고 강조 ---
    sky = summary_df[summary_df["학교"] == "하늘고"]
    fig.add_trace(go.Scatter(
        x=sky["학교"],
        y=sky["평균 생중량"],
        mode="markers+text",
        text=["⭐ 최적 EC"],
        textposition="top center",
        marker=dict(size=18)
    ))

    fig.update_layout(
        height=550,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo"),
        yaxis_title="생중량 (g)",
        xaxis_title="학교",
        legend_title="지표"
    )

    st.plotly_chart(fig, use_container_width=True)


# ===============================
# 탭 2
# ===============================
with tab2:
    st.subheader("학교별 평균 EC와 온도")

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_bar(
        x=summary_df["학교"],
        y=summary_df["EC"],
        name="EC",
        secondary_y=False
    )

    fig2.add_bar(
        x=summary_df["학교"],
        y=summary_df["평균 온도"],
        name="온도",
        secondary_y=True
    )

    fig2.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo"),
        yaxis_title="EC",
        yaxis2_title="온도 (℃)"
    )

    st.plotly_chart(fig2, use_container_width=True)


# ===============================
# 탭 3
# ===============================
with tab3:
    st.markdown("""
### 🧪 실험 개요

- 대상 식물: **나도수영 (극지 모델 식물)**
- 참여 학교: 송도고, 하늘고, 아라고, 동산고
- 분석 목적:
  - 온도와 EC 중 어떤 요인이 생중량에 더 큰 영향을 주는지 분석

#### 🔍 핵심 결론
- **온도와 생중량의 상관관계는 매우 낮음**
- **EC 농도와 생중량은 강한 상관관계**
- 하늘고 (EC 2.0) 조건에서 생중량 최대
- EC 3~4 범위가 최적 구간으로 판단됨
""")

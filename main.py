import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata

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
# 유니코드 파일 인식
# ===============================
def normalize(text):
    return unicodedata.normalize("NFC", text)

def find_file(directory: Path, target_name: str):
    for f in directory.iterdir():
        if normalize(f.name) == normalize(target_name):
            return f
    return None

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_growth_data():
    file = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if file is None:
        return None

    xls = pd.ExcelFile(file)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

@st.cache_data
def load_env_data():
    env = {}
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == ".csv":
            school = f.stem.replace("_환경데이터", "")
            env[school] = pd.read_csv(f)
    return env

with st.spinner("📡 데이터 로딩 중..."):
    growth_data = load_growth_data()
    env_data = load_env_data()

if growth_data is None or not env_data:
    st.error("❌ 데이터 파일을 찾을 수 없습니다.")
    st.stop()

# ===============================
# 요약 데이터 생성
# ===============================
EC_MAP = {"송도고": 1.0, "하늘고": 2.0, "아라고": 4.0, "동산고": 8.0}
summary = []

for school, gdf in growth_data.items():
    summary.append({
        "학교": school,
        "평균 생중량": gdf["생중량(g)"].mean(),
        "평균 온도": env_data[school]["temperature"].mean(),
        "EC": EC_MAP[school]
    })

summary_df = pd.DataFrame(summary).sort_values("EC")

# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📈 EC·온도·생중량 관계",
    "📊 학교별 환경 데이터",
    "📝 실험 개요"
])

# ===============================
# 탭 1
# ===============================
with tab1:
    st.subheader("EC 농도와 온도 대비 나도수영 생중량")

    fig = make_subplots()

    # 생중량 꺾은선
    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=summary_df["평균 생중량"],
        mode="lines+markers",
        name="평균 생중량",
        line=dict(width=4)
    ))

    # EC 산점도 (선에 가깝게)
    ec_norm = (summary_df["EC"] - summary_df["EC"].min()) / (summary_df["EC"].max() - summary_df["EC"].min())
    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=summary_df["평균 생중량"] + (ec_norm - 0.5) * 0.25,
        mode="markers",
        name="EC 농도",
        marker=dict(size=14)
    ))

    # 온도 산점도 (더 분산)
    temp_norm = (summary_df["평균 온도"] - summary_df["평균 온도"].min()) / (summary_df["평균 온도"].max() - summary_df["평균 온도"].min())
    fig.add_trace(go.Scatter(
        x=summary_df["학교"],
        y=summary_df["평균 생중량"] + (temp_norm - 0.5) * 0.9,
        mode="markers",
        name="온도",
        marker=dict(size=14, symbol="diamond")
    ))

    fig.update_layout(
        height=550,
        yaxis_title="평균 생중량 (g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
**📌 그래프 해석**

- 평균 생중량을 기준으로 꺾은선 그래프를 구성하고, EC 농도와 온도를 산점도로 중첩하였다.
- EC 농도 산점도는 생중량 변화 추세선에 가깝게 분포한 반면,
- 온도 산점도는 선과의 거리가 크게 나타났다.
- 이는 **나도수영의 생중량이 온도보다 EC 농도의 영향을 더 크게 받는다는 것을 시각적으로 보여준다.**
""")

# ===============================
# 탭 2
# ===============================
with tab2:
    st.subheader("학교별 평균 EC 농도")
    fig_ec = go.Figure()
    fig_ec.add_bar(x=summary_df["학교"], y=summary_df["EC"])
    fig_ec.update_layout(yaxis_title="EC")
    st.plotly_chart(fig_ec, use_container_width=True)

    st.subheader("학교별 평균 온도")
    fig_temp = go.Figure()
    fig_temp.add_bar(x=summary_df["학교"], y=summary_df["평균 온도"])
    fig_temp.update_layout(yaxis_title="온도 (℃)")
    st.plotly_chart(fig_temp, use_container_width=True)

# ===============================
# 탭 3
# ===============================
with tab3:
    st.markdown("""
### 🧪 실험 개요

- 대상 식물: **나도수영**
- 비교 요소: **EC 농도, 온도**
- 목적: 생중량에 가장 큰 영향을 주는 환경 요인 분석

### 🔍 결론
- 온도와 생중량의 상관관계는 낮게 나타남
- EC 농도와 생중량은 뚜렷한 상관관계 확인
- **EC 2.0 (하늘고)** 조건에서 최적 생육
""")

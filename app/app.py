import streamlit as st
import google.generativeai as genai
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from datetime import datetime, timedelta

# --- 配置页面 ---
st.set_page_config(page_title="NBA 红黑榜", page_icon="🏀", layout="wide")

# --- CSS 样式美化 (尽力模仿你的黑暗风格) ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #464b5c;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .red-list { border-top: 5px solid #ff4b4b; }
    .black-list { border-top: 5px solid #4b4b4b; }
    .gold-list { border-top: 5px solid #ffd700; }
    h1, h2, h3 { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. 配置 Gemini API ---
# 安全读取 Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ 请在 Streamlit Secrets 中配置 GOOGLE_API_KEY")

# --- 2. 获取 NBA 数据函数 ---
@st.cache_data(ttl=3600) # 缓存1小时，避免频繁请求
def get_nba_daily_stats():
    # 获取昨天的日期（美国时间）
    today = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
    
    try:
        # 从 NBA 官方 API 拉取数据
        logs = playergamelogs.PlayerGameLogs(
            date_from_nullable=today,
            date_to_nullable=today,
            season_nullable='2025-26' # 注意：如果新赛季开始需修改年份
        )
        df = logs.get_data_frames()[0]
        
        if df.empty:
            return None
            
        # 简单计算范特西分数 (NBA官方标准)
        # 1分=1, 篮板=1.2, 助攻=1.5, 抢断=3, 盖帽=3, 失误=-1
        df['FANTASY_PTS'] = (df['PTS'] + 
                             df['REB'] * 1.2 + 
                             df['AST'] * 1.5 + 
                             df['STL'] * 3 + 
                             df['BLK'] * 3 - 
                             df['TOV'])
        
        # 只需要关键列
        return df[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FANTASY_PTS', 'FG_PCT']]
    except Exception as e:
        st.error(f"无法连接 NBA 数据库: {e}")
        return None

# --- 3. Gemini 点评函数 ---
def get_gemini_comment(player_name, stats, list_type):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "AI 未连接"
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if list_type == "red":
        prompt = f"你是NBA范特西专家。球员 {player_name} 昨天表现超神：{stats}。请用一句极度夸张、崇拜的语气点评他（比如叫他亲爹、真神）。50字以内。"
    else:
        prompt = f"你是NBA毒舌评论员。球员 {player_name} 昨天表现灾难：{stats}。请用一句极度嘲讽、阴阳怪气的语气喷他（比如问他是不是在梦游）。50字以内。"
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "AI 暂时不想说话..."

# --- 主程序逻辑 ---
st.title("🏀 NBA 每日红黑榜 (Beta)")
st.caption(f"数据来源: NBA Official API | 更新时间: {datetime.now().strftime('%Y-%m-%d')}")

# 加载数据
with st.spinner('正在从 NBA 总部拉取数据...'):
    df = get_nba_daily_stats()

if df is not None and not df.empty:
    # 按范特西分数排序
    df_sorted = df.sort_values(by='FANTASY_PTS', ascending=False)
    
    # 提取红榜前3 和 黑榜倒数3
    top_players = df_sorted.head(3)
    bottom_players = df_sorted.tail(3)

    # === 红榜区域 ===
    st.header("🏆 今日红榜 (The Kings)")
    
    # 👑 榜首（大图展示）
    king = top_players.iloc[0]
    st.markdown(f"### 👑 今日真神：{king['PLAYER_NAME']}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # 模拟球员卡片数据
        st.markdown(f"""
        <div class='metric-card gold-list'>
            <h1>{int(king['PTS'])}</h1>
            <p>得分</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        stats_str = f"{king['PTS']}分 {king['REB']}板 {king['AST']}助"
        st.info(f"📊 数据：{stats_str} | 命中率: {king['FG_PCT']*100:.1f}%")
        # 只有榜首调用 AI 点评，节省额度
        if st.button("查看 AI 对真神的评价", key="ai_king"):
            comment = get_gemini_comment(king['PLAYER_NAME'], stats_str, "red")
            st.success(f"🤖 AI: {comment}")

    st.divider()

    # 其他红榜球员
    st.subheader("🔥 表现优异")
    r_cols = st.columns(2)
    for i in range(1, 3):
        p = top_players.iloc[i]
        with r_cols[i-1]:
            st.markdown(f"**#{i+1} {p['PLAYER_NAME']}** ({p['TEAM_ABBREVIATION']})")
            st.text(f"FPts: {p['FANTASY_PTS']:.1f} | {int(p['PTS'])}分/{int(p['REB'])}板/{int(p['AST'])}助")

    # === 黑榜区域 ===
    st.header("🗑️ 今日黑榜 (The Shame)")
    st.markdown("这里是今天表现最让人心碎（或甚至想骂人）的球员...")
    
    b_cols = st.columns(3)
    # 倒序展示倒数3名
    for i in range(3):
        p = bottom_players.iloc[2-i] # 倒数第一，倒数第二...
        with b_cols[i]:
            st.markdown(f"<div class='metric-card black-list'><h4>{p['PLAYER_NAME']}</h4></div>", unsafe_allow_html=True)
            st.caption(f"💩 只有 {int(p['PTS'])} 分")
            st.caption(f"失误: {int(p['TOV'])}")

else:
    st.info("😴 昨天好像没有比赛，或者数据还在路上（NBA API 有时会有延迟）。")
    st.write("如果是休赛期，这里就不会有数据哦。")

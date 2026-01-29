import streamlit as st
import google.generativeai as genai
import pandas as pd
from nba_api.stats.endpoints import playergamelogs
from datetime import datetime, timedelta

# --- 页面基础配置 ---
st.set_page_config(page_title="RED/BLACK LIST", page_icon="🏀", layout="wide")

# --- 核心样式 (模仿你的截图风格) ---
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background-color: #0b0e11;
        color: #e0e0e0;
    }
    
    /* 隐藏默认头部 */
    header {visibility: hidden;}
    
    /* 球员卡片样式 */
    .player-card {
        background: #1e2126;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        transition: transform 0.2s;
        border: 1px solid #333;
        margin-bottom: 15px;
        height: 100%;
    }
    .player-card:hover {
        transform: scale(1.02);
        border-color: #555;
    }
    
    /* 头像样式 */
    .player-img {
        width: 100%;
        height: auto;
        border-radius: 8px;
        margin-bottom: 8px;
        object-fit: cover;
        background: linear-gradient(to bottom, #2c3038, #1e2126);
    }
    
    /* 不同榜单的边框颜色 */
    .border-red { border-top: 4px solid #ff4b4b; box-shadow: 0 0 10px rgba(255, 75, 75, 0.1); }
    .border-gold { border-top: 4px solid #ffd700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.2); }
    .border-black { border-top: 4px solid #4a4a4a; opacity: 0.8; }
    
    /* 字体样式 */
    .stat-main { font-size: 1.2rem; font-weight: bold; color: #fff; margin: 0; }
    .stat-sub { font-size: 0.8rem; color: #888; margin: 0; }
    .rank-badge { 
        background-color: #333; color: #fff; padding: 2px 8px; 
        border-radius: 4px; font-size: 0.7rem; font-weight: bold;
        margin-bottom: 5px; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- 数据获取与处理 ---
@st.cache_data(ttl=3600)
def get_nba_data():
    # 获取数据 (为了演示稳定，这里先写死日期，你可以改成 datetime.now())
    # 真实使用时建议：yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
    target_date = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
    
    try:
        # 获取包含 PLAYER_ID 的数据
        logs = playergamelogs.PlayerGameLogs(
            date_from_nullable=target_date,
            date_to_nullable=target_date,
            season_nullable='2024-25'
        )
        df = logs.get_data_frames()[0]
        
        if df.empty:
            return None

        # --- 范特西积分算法 ---
        # 你的算法：得分(1) + 篮板(1.2) + 助攻(1.5) + 抢断(3) + 盖帽(3) - 失误(1)
        df['FPTS'] = (df['PTS'] + df['REB']*1.2 + df['AST']*1.5 + 
                      df['STL']*3 + df['BLK']*3 - df['TOV'])
        
        # 必须要有上场时间才算入红黑榜 (过滤掉垃圾时间上场1分钟的人)
        df['MIN_FLOAT'] = df['MIN'].astype(str).apply(lambda x: float(x.split(':')[0]) if ':' in x else 0)
        df = df[df['MIN_FLOAT'] > 10] # 至少打10分钟
        
        # 只需要展示用的列
        cols = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FPTS', 'MIN']
        return df[cols].sort_values(by='FPTS', ascending=False)
    except:
        return None

# --- UI 组件：HTML 球员卡 ---
def render_player_card(player, rank, card_type="red"):
    # NBA 官方头像 URL 规则
    headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player['PLAYER_ID']}.png"
    
    border_class = "border-red"
    if card_type == "gold": border_class = "border-gold"
    if card_type == "black": border_class = "border-black"
    
    card_html = f"""
    <div class="player-card {border_class}">
        <div class="rank-badge">#{rank} {player['TEAM_ABBREVIATION']}</div>
        <img src="{headshot_url}" class="player-img" onerror="this.src='https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png';">
        <div style="text-align: left; padding-left: 5px;">
            <div style="font-weight: bold; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {player['PLAYER_NAME']}
            </div>
            <div class="stat-main" style="color: {'#ffd700' if card_type=='gold' else '#fff'}">
                {int(player['FPTS'])} <span style="font-size:0.7rem; color:#666;">FPts</span>
            </div>
            <div class="stat-sub">
                {int(player['PTS'])}分 {int(player['REB'])}板 {int(player['AST'])}助
            </div>
            <div class="stat-sub" style="margin-top:2px; font-size: 0.7rem; color: #ff4b4b;">
                {'🔥 ' + str(int(player['STL']))+'断' if player['STL']>2 else ''} 
                {'🖐 ' + str(int(player['BLK']))+'帽' if player['BLK']>2 else ''}
            </div>
        </div>
    </div>
    """
    return card_html

# --- 主程序 ---
df = get_nba_data()

st.title("🏀 RED BLACK LIST")
st.caption(f"Fantasy Performance | {datetime.now().strftime('%Y-%m-%d')}")

if df is not None and not df.empty:
    
    # 1. 榜首 (The King)
    king = df.iloc[0]
    st.markdown("### 👑 今日真神 (The GOAT)")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(render_player_card(king, 1, "gold"), unsafe_allow_html=True)
    with col2:
        # 榜首的大字报
        st.markdown(f"## {king['PLAYER_NAME']}")
        st.metric("Fantasy Points", f"{king['FPTS']:.1f}", delta="全场最佳")
        st.write(f"📊 数据: {int(king['PTS'])}分 / {int(king['REB'])}篮板 / {int(king['AST'])}助攻 / {int(king['STL'])}抢断 / {int(king['BLK'])}盖帽")
        
        # AI 点评
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            if st.button("AI 点评真神"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"用极其崇拜、夸张的语气夸赞NBA球员{king['PLAYER_NAME']}今天的表现：{int(king['PTS'])}分,{king['FPTS']}范特西分。称呼他为'爹'或'神'。"
                res = model.generate_content(prompt)
                st.success(res.text)

    st.divider()

    # 2. 红榜 (Top 2-9)
    st.subheader("🔥 红榜精英 (Elite)")
    top_tier = df.iloc[1:9] # 取第2到第9名
    
    # 创建 4列 的网格
    cols = st.columns(4)
    for i, (index, row) in enumerate(top_tier.iterrows()):
        with cols[i % 4]: # 循环放入列中
            st.markdown(render_player_card(row, i+2, "red"), unsafe_allow_html=True)
            
    st.divider()

    # 3. 完整榜单 (折叠起来，避免太长，用表格展示)
    with st.expander("查看今日所有球员排名 (All Players)"):
        st.dataframe(
            df[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'FPTS', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 4. 黑榜 (倒数 8 名)
    st.subheader("🗑️ 今日黑榜 (The Shame)")
    st.caption("出场超过10分钟但打得最烂的球员")
    
    # 取倒数 8 名
    bottom_tier = df.tail(8).sort_values(by='FPTS', ascending=True) # 倒序排，最烂的在最前
    
    cols_black = st.columns(4)
    for i, (index, row) in enumerate(bottom_tier.iterrows()):
        with cols_black[i % 4]:
            st.markdown(render_player_card(row, len(df)-i, "black"), unsafe_allow_html=True)

else:
    st.info("🚧 正在等待比赛数据更新，或者昨天没有比赛。")

import streamlit as st
import google.generativeai as genai

# 1. 安全配置：从 Streamlit Secrets 读取 Key
# 这样即便代码公开，别人也看不到你的 Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Streamlit 控制台配置 API Key！")

st.title("🏀 NBA 范特西红黑榜")
st.subheader("由 Sands China 体育赛事部技术支持")

# 2. 获取用户输入
player_info = st.text_area("输入球员昨晚的数据或表现", placeholder="例如：库里 30分 8助攻 命中率 50%")

if st.button("生成红黑榜评价"):
    if player_info:
        try:
            # 3. 解决 NotFound 错误：使用最新的 1.5 系列模型
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 融入你的系统指令逻辑
            system_prompt = (
                "你是一个专业的 NBA 范特西专家。请根据以下球员表现，"
                "判断他应该进‘红榜’（超水平发挥）还是‘黑榜’（表现拉跨）。"
                "评价要专业且带一点毒舌或赞美。"
            )
            
            response = model.generate_content(f"{system_prompt}\n球员表现如下：{player_info}")
            
            st.write("---")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"运行出错啦：{e}")
    else:
        st.warning("请先输入球员信息。")

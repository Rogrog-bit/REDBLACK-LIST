import streamlit as st
import google.generativeai as genai

# 配置 Gemini API (Rog，这里先用你的 Key 测试，之后教你更安全的办法)
genai.configure(api_key="AIzaSyDKc-K9sOMihWzhAS_rvrhAAq7UpX_-zlk")

st.title("🏀 NBA 范特西红黑榜")
st.subheader("由 Gemini 提供支持的球员表现评定")

# 输入框
player_info = st.text_area("输入球员昨晚的数据或表现（例如：库里 30分 8助攻 命中率 50%）")

if st.button("生成红黑榜评价"):
    if player_info:
        model = genai.GenerativeModel('gemini-pro')
        # 这里就是你提到的系统设定逻辑
        prompt = f"你是一个专业的 NBA 范特西专家。请根据以下球员表现，判断他应该进‘红榜’还是‘黑榜’，并给出毒舌或赞美的理由：{player_info}"
        
        response = model.generate_content(prompt)
        st.write("---")
        st.markdown(response.text)
    else:
        st.warning("请先输入球员信息。")

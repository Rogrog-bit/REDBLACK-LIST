import streamlit as st
import google.generativeai as genai

# 安全地从 Streamlit Secrets 中读取 API Key
# 这样即使别人看到你的代码，也拿不到你的 Key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.title("🏀 NBA 范特西红黑榜")
st.subheader("由 Gemini 提供支持的球员表现评定")

# 输入框
player_info = st.text_area("输入球员昨晚的数据或表现（例如：库里 30分 8助攻 命中率 50%）")

if st.button("生成红黑榜评价"):
    if player_info:
        # 使用你想要的系统逻辑
        model = genai.GenerativeModel('gemini-pro')
        
        # 这里的 Prompt 可以根据你的 System Instruction 进一步细化
        prompt = f"你是一个专业的 NBA 范特西专家。请根据以下球员表现，判断他应该进‘红榜’还是‘黑榜’，并给出毒舌或赞美的理由：{player_info}"
        
        response = model.generate_content(prompt)
        st.write("---")
        st.markdown(response.text)
    else:
        st.warning("请先输入球员信息。")

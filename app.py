import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ================= 配置页面 =================
st.set_page_config(page_title="随便刷刷题", page_icon="🍀", layout="wide")

# ================= 0. 自定义样式 (CSS) =================
st.markdown("""
    <style>
    /* --- 全局主题色变量覆盖 (尝试覆盖 Streamlit 默认 Primary) --- */
    :root {
        --primary-color: #4CAF50;
    }

    /* --- 1. 题目文本样式 (蓝底黑字) --- */
    .question-text {
        font-size: 18px !important;
        line-height: 1.6 !important;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
        background-color: #e8f4f8; /* 淡蓝背景 */
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #2196F3; /* 深蓝装饰条 */
    }

    /* --- 2. 选项文本样式 --- */
    .stRadio label p, .stCheckbox label p {
        font-size: 17px !important;
        line-height: 1.5 !important;
    }

    /* --- 3. 强制绿色主题 (修复选中颜色还是红色的问题) --- */
    
    /* A. 复选框 (Checkbox) 选中态 */
    /* 针对较新版 Streamlit 的结构 */
    div[data-testid="stCheckbox"] label[data-checked="true"] div:first-child {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
    }
    /* 针对部分旧版或不同渲染结构，增加 aria-checked 支持 */
    div[data-testid="stCheckbox"] label[aria-checked="true"] div:first-child {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
    }
    
    /* B. 单选框 (Radio) 选中态 */
    div[role="radiogroup"] label[data-checked="true"] div:first-child {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
    }

    /* --- 4. 迷你按钮完美居中优化 (针对右侧快速跳转) --- */
    
    div[data-testid="stButton"] button {
        width: 100% !important;
        padding: 0px !important;        /* 去掉内边距，完全靠 Flex 居中 */
        font-size: 14px !important;     /* 字体大小 */
        height: 34px !important;        /* 固定高度 */
        min-height: 34px !important;
        
        /* 核心：Flexbox 强制居中 */
        display: flex !important;
        align-items: center !important;     /* 垂直居中 */
        justify-content: center !important; /* 水平居中 */
        
        line-height: 1 !important;
        white-space: nowrap !important;     /* 禁止换行 */
        border-radius: 4px !important;
    }
    
    /* 按钮内的文本元素也要强制居中 */
    div[data-testid="stButton"] button p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
    }

    /* 当前题号高亮 (Primary按钮) 改为绿色 */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
        color: white !important;
        font-weight: bold !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #45a049 !important;
        border-color: #45a049 !important;
    }

    /* 隐藏默认页眉页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ================= 1. 读取数据函数 =================
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_excel(file_path)
        df = df.fillna('')
        if '答案' in df.columns:
            df['答案'] = df['答案'].astype(str).str.strip().str.upper()
        if '类型' not in df.columns:
            df['类型'] = '单选'
        df['类型'] = df['类型'].apply(lambda x: '单选' if '单' in str(x) else ('多选' if '多' in str(x) else ('判断' if '判' in str(x) else str(x))))
        return df
    except Exception as e:
        st.error(f"读取 Excel 失败: {e}")
        return None

# ================= 2. 初始化状态 =================
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0  
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []    
if 'mode' not in st.session_state:
    st.session_state.mode = 'all'     
if 'answer_submitted' not in st.session_state:
    st.session_state.answer_submitted = False 

file_path = '题库.xlsx' 
df = load_data(file_path)

# ================= 3. 侧边栏：设置区 =================
with st.sidebar:
    st.header("🍀 设置")
    
    # 模式选择
    st.markdown("##### 模式")
    mode_label = st.radio("模式", ["顺序刷题", "只刷错题"], 
                          index=0 if st.session_state.mode == 'all' else 1, 
                          label_visibility="collapsed")
    new_mode = 'all' if mode_label == "顺序刷题" else 'mistake'
    
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.session_state.current_idx = 0
        st.session_state.answer_submitted = False
        st.rerun()

    st.divider()

    # 题型选择 (绿色勾选框)
    st.markdown("##### 题型筛选")
    c1, c2, c3 = st.columns(3)
    with c1: check_single = st.checkbox("单选", value=True)
    with c2: check_multi = st.checkbox("多选", value=True)
    with c3: check_judge = st.checkbox("判断", value=True)
    
    selected_types = []
    if check_single: selected_types.append("单选")
    if check_multi: selected_types.append("多选")
    if check_judge: selected_types.append("判断")
    
    st.divider()
    
    # 错题本
    st.markdown(f"##### 错题本 ({len(st.session_state.mistakes)})")
    with st.expander("👁️ 查看错题"):
        if not st.session_state.mistakes:
            st.caption("暂无错题")
        else:
            if df is not None:
                for idx, m_idx in enumerate(st.session_state.mistakes):
                    q_row = df.iloc[m_idx]
                    st.markdown(f"**{idx+1}. {q_row['题目'][:15]}...**")
                    st.markdown(f":green[{q_row['答案']}]")
                    st.markdown("---")
            
    if st.session_state.mistakes:
        if st.button("💾 导出错题"):
            mistake_df = df.iloc[st.session_state.mistakes]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            fname = f"错题_{timestamp}.xlsx"
            mistake_df.to_excel(fname, index=False)
            st.success(f"已导出: {fname}")
            
    st.divider()
    if st.button("🔄 重置"):
        st.session_state.current_idx = 0
        st.session_state.mistakes = []
        st.session_state.answer_submitted = False
        st.session_state.mode = 'all'
        st.rerun()

# ================= 4. 主界面逻辑 =================
if df is None:
    st.warning("请确保 '题库.xlsx' 文件存在。")
    st.stop()

# 筛选题目
if st.session_state.mode == 'all':
    base_indices = df.index.tolist()
else:
    base_indices = st.session_state.mistakes

type_filtered_indices = df[df['类型'].isin(selected_types)].index.tolist()
final_question_indices = [i for i in base_indices if i in type_filtered_indices]

if not final_question_indices:
    st.info("当前筛选条件下没有题目。")
    st.stop()

if st.session_state.current_idx >= len(final_question_indices):
    st.session_state.current_idx = 0

real_idx = final_question_indices[st.session_state.current_idx]
q_data = df.iloc[real_idx]
total_q = len(final_question_indices)

# ================= 5. 页面布局 =================

# 左7 右3 比例
main_col, nav_col = st.columns([7, 3])

# --- 右侧：快速跳转 (可折叠 + 5列布局 + 完美居中) ---
with nav_col:
    with st.expander("📍 快速跳转", expanded=True):
        with st.container(height=400):
            # 每行5个按钮，给数字留足空间
            cols_per_row = 5
            for i in range(0, total_q, cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < total_q:
                        q_num = i + j + 1
                        is_current = (i + j == st.session_state.current_idx)
                        btn_type = "primary" if is_current else "secondary"
                        
                        # 显示按钮
                        if cols[j].button(f"{q_num}", key=f"nav_{q_num}", type=btn_type, use_container_width=True):
                            st.session_state.current_idx = i + j
                            st.session_state.answer_submitted = False
                            st.rerun()

# --- 左侧：答题区 ---
with main_col:
    type_str = str(q_data['类型'])
    st.caption(f"进度: {st.session_state.current_idx + 1} / {total_q} | 题型: {type_str}")
    
    # 蓝色题干
    st.markdown(f'<div class="question-text">{q_data["题目"]}</div>', unsafe_allow_html=True)

    options = []
    option_labels = ['A', 'B', 'C', 'D', 'E']
    for col, label in zip(['选项A', '选项B', '选项C', '选项D', '选项E'], option_labels):
        val = str(q_data[col]).strip()
        if col in df.columns and val and val != 'nan':
            options.append(f"{label}. {val}")

    user_ans = None
    correct_ans = str(q_data['答案']).strip()
    input_disabled = st.session_state.answer_submitted
    is_multi = "多" in type_str

    if is_multi:
        st.write("请选择（多选）：")
        selected = []
        for opt in options:
            checked = st.checkbox(opt, key=f"multi_{real_idx}_{opt}", disabled=input_disabled)
            if checked:
                selected.append(opt[0])
        if selected:
            user_ans = "".join(sorted(selected))
        
        st.write("")
        if not st.session_state.answer_submitted:
            if st.button("提交答案", use_container_width=True):
                if user_ans:
                    st.session_state.answer_submitted = True
                    if user_ans != correct_ans:
                        if real_idx not in st.session_state.mistakes:
                            st.session_state.mistakes.append(real_idx)
                    st.rerun()
                else:
                    st.warning("请至少选一个！")
    else:
        def on_radio_change():
            st.session_state.answer_submitted = True

        choice = st.radio(
            "请选择：", 
            options, 
            index=None, 
            key=f"single_{real_idx}", 
            disabled=input_disabled,
            on_change=on_radio_change,
            label_visibility="collapsed"
        )
        if choice:
            user_ans = choice[0]
            if user_ans != correct_ans:
                 if real_idx not in st.session_state.mistakes:
                     st.session_state.mistakes.append(real_idx)

    # 结果显示
    if st.session_state.answer_submitted:
        st.divider()
        is_correct = (user_ans == correct_ans)
        if is_correct:
            st.success("✅ 回答正确")
        else:
            st.error(f"❌ 你的选择：{user_ans}")
            st.markdown(f"**正确答案：** :green[{correct_ans}]")

    st.write("")
    st.write("")

    # 底部导航
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        if st.session_state.current_idx > 0:
            if st.button("⬅️ 上一题", use_container_width=True):
                st.session_state.current_idx -= 1
                st.session_state.answer_submitted = False
                st.rerun()
    with b_col2:
        if st.session_state.current_idx < total_q - 1:
            if st.button("下一题 ➡️", use_container_width=True):
                st.session_state.current_idx += 1
                st.session_state.answer_submitted = False
                st.rerun()
        else:
            if st.button("🏁 重新开始", use_container_width=True):
                st.session_state.current_idx = 0
                st.session_state.answer_submitted = False
                st.balloons()
                st.rerun()
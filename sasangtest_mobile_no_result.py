# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==========================================
# [설정] 이메일 발송 정보 (보안 적용)
# ==========================================
try:
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    SENDER_PASSWORD = st.secrets["SENDER_PASSWORD"]
except:
    # 로컬 테스트용 더미 값 (실제 배포시 secrets 설정 필수)
    SENDER_EMAIL = "disc8275@gmail.com" 
    SENDER_PASSWORD = "axrd kith cizs svzg" 

RECEIVER_EMAIL = "ds1lih@naver.com" # 관리자 이메일

# ==========================================
# 1. 페이지 설정 및 스타일
# ==========================================
st.set_page_config(page_title="사상체질 문진표", layout="centered")

st.markdown("""
    <style>
    /* [화면 표시용 스타일] */
    h1 { 
        font-size: 1.5rem; 
        font-weight: 700;
    }
    h3 { 
        color: #16a085; 
        font-size: 1.2rem; 
    }
    .stButton button {
        height: 3rem;
        font-size: 1.2rem;
        border-radius: 10px;
    }
    div[data-testid="stRadio"] label {
        font-size: 1.1rem !important;
        padding: 10px 0;
        cursor: pointer;
        color: var(--text-color) !important; 
    }
    .question-text {
        font-size: 1.3rem;
        font-weight: bold;
        color: var(--text-color); 
        margin-bottom: 20px;
        line-height: 1.5;
    }
    
    /* [공통 테이블 스타일] */
    .guide-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 20px;
        font-size: 1rem;
    }
    .guide-table th {
        background-color: #f0f2f6;
        color: #333;
        padding: 12px;
        border: 1px solid #ddd;
        text-align: center;
        font-weight: bold;
    }
    .guide-table td {
        padding: 10px;
        border: 1px solid #ddd;
        vertical-align: top;
        color: var(--text-color);
    }
    
    @media (prefers-color-scheme: dark) {
        .guide-table th {
            background-color: #444;
            color: #fff;
            border-color: #666;
        }
        .guide-table td {
            border-color: #666;
        }
    }

    /* [인쇄 전용 스타일] */
    @media print {
        * { 
            color: black !important; 
            background-color: white !important;
            -webkit-print-color-adjust: exact !important; 
            print-color-adjust: exact !important; 
        }

        .guide-table th {
            background-color: #eee !important;
            color: black !important;
            border: 1px solid black !important;
        }
        .guide-table td {
            color: black !important;
            border: 1px solid black !important;
        }

        .page-break { 
            page-break-before: always !important; 
            display: block !important; 
            height: 1px; 
        }

        @page {
            margin: 0mm !important; 
            size: auto; 
        }

        html, body {
            margin: 0 !important; 
            padding: 0 !important; 
            height: auto !important; 
            min-height: 0 !important; 
            overflow: visible !important; 
        }
        
        .stApp {
            min-height: 0 !important; 
            height: auto !important; 
            overflow: visible !important; 
            background-color: white !important; 
        }

        .block-container {
            margin: 15mm 15mm 0 15mm !important; 
            padding-top: 0 !important; 
            padding-bottom: 0 !important; 
            width: auto !important; 
        }

        section[data-testid="stSidebar"], 
        header, 
        footer, 
        .stAppDeployButton, 
        button, 
        .stButton, 
        div[data-testid="stHorizontalBlock"], 
        .stProgress, 
        iframe,
        textarea, 
        .stTextArea {
            display: none !important; 
            height: 0 !important; 
            width: 0 !important; 
            margin: 0 !important; 
            padding: 0 !important; 
            opacity: 0 !important; 
            visibility: hidden !important; 
        }
        
        iframe[title="streamlit.components.v1.components.html"] {
            display: none !important; 
            height: 0 !important; 
        }
    }
    </style>
    """, unsafe_allow_html=True)

TYPE_MAP = {'TY': '태양인', 'SY': '소양인', 'TE': '태음인', 'SE': '소음인'}

# 질문 목록 정의
QUESTIONS = [
    {"q": "오래 서 있거나 걷는 게 유난히 힘들고 다리에 힘이 없나요?", "type": "TY"},
    {"q": "가슴이 넓고 딱 벌어졌지만, 엉덩이 쪽은 빈약한 편인가요?", "type": "SY"},
    {"q": "배와 허리 부위가 굵고, 전체적으로 뼈대가 굵고 살집이 있나요?", "type": "TE"},
    {"q": "전체적으로 체구가 작고 마른 편이며, 엉덩이가 발달했나요?", "type": "SE"},
    {"q": "눈매가 날카롭고 강렬해서, 남들이 쳐다보기 어려워하나요?", "type": "TY"},
    {"q": "눈매가 날렵하고 입술이 얇으며, 턱이 뾰족한 편인가요?", "type": "SY"},
    {"q": "이목구비가 큼직하고 입술이 두툼해서 점잖은 인상인가요?", "type": "TE"},
    {"q": "인상이 부드럽고 얌전하며 오밀조밀하게 생겼나요?", "type": "SE"},
    {"q": "추진력이 강하고 결단력이 있지만, 남의 말을 잘 안 듣나요?", "type": "TY"},
    {"q": "성격이 급하고 활발하며 솔직하지만, 싫증을 잘 내나요?", "type": "SY"},
    {"q": "느긋하고 변화를 싫어하며, 속마음을 잘 드러내지 않나요?", "type": "TE"},
    {"q": "꼼꼼하고 내성적이며, 작은 일에도 걱정이 많은 편인가요?", "type": "SE"},
    {"q": "화가 나면 확 폭발했다가도 금방 풀리는 편인가요?", "type": "SY"},
    {"q": "새로운 일을 벌이는 것을 좋아하고 사람 사귀는 걸 즐기나요?", "type": "TY"},
    {"q": "겁이 많고 가슴이 자주 두근거리나요?", "type": "TE"},
    {"q": "불안한 마음이 자주 들고 질투심이 좀 있는 편인가요?", "type": "SE"},
    {"q": "음식을 먹으면 자꾸 토하거나 체하는 증상이 심한가요?", "type": "TY"},
    {"q": "소화가 아주 잘 돼서 과식하는 편이고, 배고픔을 못 참나요?", "type": "SY"},
    {"q": "무엇이든 잘 먹고, 많이 먹어도 소화에 큰 문제가 없나요?", "type": "TE"},
    {"q": "입이 짧고 소화가 잘 안 되며, 조금만 많이 먹어도 불편한가요?", "type": "SE"},
    {"q": "찬물이나 아이스크림을 먹어도 배탈이 잘 안 나나요?", "type": "SY"},
    {"q": "찬 음식을 먹으면 바로 설사를 하거나 배가 아픈가요?", "type": "SE"},
    {"q": "평소 땀이 잘 안 나고, 땀을 흘리면 오히려 개운한가요?", "type": "TE"},
    {"q": "조금만 움직여도 땀이 나고, 땀 흘리면 기운이 쏙 빠지나요?", "type": "SE"},
    {"q": "머리나 얼굴, 가슴 쪽에만 유독 땀이 많이 나나요?", "type": "SY"},
    {"q": "운동으로 땀을 흠뻑 흘려야 몸이 가볍고 컨디션이 좋나요?", "type": "TE"},
    {"q": "소변을 시원하게 잘 보면 몸이 건강하다고 느끼나요?", "type": "TY"},
    {"q": "변비가 있어서 며칠 화장실을 못 가도 배가 안 아프나요?", "type": "TE"},
    {"q": "변비가 생기면 가슴이 답답하고 무척 괴롭나요?", "type": "SY"},
    {"q": "대변이 묽지 않고 모양 있게 잘 나오면 속이 편한가요?", "type": "SY"},
    {"q": "설사를 하면 기운이 쫙 빠지고 배가 아픈가요?", "type": "SE"},
    {"q": "추위를 아주 많이 타고 손발이 차며, 여름에도 이불을 덮나요?", "type": "SE"},
    {"q": "더위를 못 참아서 찬물을 벌컥벌컥 마시나요?", "type": "SY"},
    {"q": "이유 없이 다리에 힘이 풀려서 걷기 힘들 때가 있나요?", "type": "TY"},
    {"q": "피부나 코, 기관지가 건조하고 뻑뻑한 느낌이 드나요?", "type": "TE"},
    {"q": "오후나 밤이 되면 몸에 열이 확 오르는 느낌이 있나요?", "type": "SY"},
    {"q": "피곤하면 눈이 쉽게 충혈되고 건조해지나요?", "type": "TE"},
]

OPTIONS = ["전혀 아니다", "아니다", "보통이다", "그렇다", "매우 그렇다"]

# ==========================================
# 세션 상태 초기화
# ==========================================
if 'step' not in st.session_state:
    st.session_state['step'] = 0  
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}
if 'answers_score' not in st.session_state:
    st.session_state['answers_score'] = [2] * len(QUESTIONS) 
if 'answers_log' not in st.session_state:
    st.session_state['answers_log'] = [""] * len(QUESTIONS)
if 'symptom_answers' not in st.session_state:
    st.session_state['symptom_answers'] = {}
if 'final_result' not in st.session_state:
    st.session_state['final_result'] = None

# ==========================================
# 로직 함수 (이메일 및 추천)
# ==========================================
def send_email_logic(target_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Fail to {target_email}: {e}")
        return False

def get_recommendation(constitution, symptoms):
    pain = symptoms.get('pain')
    sweat = symptoms.get('sweat')
    stool = symptoms.get('stool')
    
    if constitution == 'SE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if sweat == "땀이 거의 나지 않는다":
                return {"condition": "소음인 울광체질 (내부 양기가 갇힌 상태)", "desc": "대변이 잘 나오지 않거나 몸에 열감이 느껴지며, 심할 경우 불안함이나 조급함이 나타날 수 있습니다.", "prescription": "천궁계지탕, 궁귀향소산, 향부자팔물탕 등"}
            else: 
                return {"condition": "소음인 망양체질 (양기가 허약해 땀으로 빠지는 상태)", "desc": "식은땀이 잘 나며 잘 지치고 피로를 자주 느낄 수 있습니다", "prescription": "황기계지탕, 보중익기탕, 승양익기탕 등"}
        else: 
            if stool == "설사를 하거나 묽다":
                return {"condition": "소음인 태음병 (속이 냉하고 배탈이 잦음)", "desc": "배가 차갑고 복통 또는 설사가 잘 나며, 소화 기능 약합니다.", "prescription": "백하오이중탕, 곽향정기산 등"}
            else:
                return {"condition": "소음인 태음병 (위장이 차갑고 막힘)", "desc": "명치 밑이 답답하고 소화가 안 됩니다.", "prescription": "곽향정기산, 향사양위탕 등"}

    elif constitution == 'SY':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if stool == "설사를 하거나 묽다":
                return {"condition": "소양인 망음병 (겉은 열, 속은 냉)", "desc": "위로는 열이나고 답답하지만, 아래는 차거나 설사가 나기 쉽고 몸이 피곤합니다.", "prescription": "형방지황탕, 저령차전자탕, 활석고삼탕 등"}
            else: 
                return {"condition": "소양인 소양상풍병 (열기가 갇힘)", "desc": "머리가 아프고 몸에 열이 나며, 가슴이 답답하고 아픈 증상으로 발전하기 쉽습니다.", "prescription": "형방패독산, 형방도적산, 형방사백산 등"}
        else: 
            if stool == "변비가 있거나 잘 안 나온다":
                return {"condition": "소양인 흉격열병 (가슴에 열이 꽉 참)", "desc": "변비가 심하고 얼굴이 붉어지며 갈증을 자주 느낍니다.", "prescription": "형방사백산, 지황백호탕, 양격산화탕 등"}
            else:
                return {"condition": "소양인 음허오열병 (신장 기운 약화)", "desc": "오후에 얼굴에 열이 오르거나 허리/다리가 약해진 느낌이에요.", "prescription": "독활지황탕, 숙지황고삼탕 등"}

    elif constitution == 'TE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            return {"condition": "태음인 위완한병 (폐/대장이 차가움)", "desc": "목이 건조하고 답답하며, 가슴이 두근거리거나, 땀은 나지 않으면서 몸이 무겁게 느껴집니다.", "prescription": "태음조위탕, 조위승청탕, 녹용대보탕 등"}
        else: 
            return {"condition": "태음인 간열병 (간에 열이 많음)", "desc": "얼굴이 붉고 눈이 아프거나, 갈증이 심하고 변비가 잘 생깁니다.", "prescription": "갈근해기탕, 열다한소탕, 청폐사간탕 등"}

    elif constitution == 'TY':
        return {"condition": "태양인 특이 병증", "desc": "다리에 힘이 빠지거나(해역), 음식을 먹고 토하는 증상(열격)을 주의해야 해요.", "prescription": "오가피장척탕, 미후등식장탕"}
    
    return {"condition": "정보 부족", "desc": "", "prescription": ""}

def go_shortcut(selected_type):
    # 단축 경로는 결과가 바로 보이므로, 이 기능은 '사용자 결과 숨김' 요청에 따라 
    # 관리자에게만 데이터를 보내고 사용자에겐 '완료' 메시지만 보여주는 식으로 변경하거나
    # 단순히 입력을 건너뛰고 바로 완료 화면으로 가게 처리합니다.
    if 'name' not in st.session_state['user_info']:
        st.session_state['user_info'] = {
            'name': '방문자', 'birth': '-', 
            'height': '-', 'weight': '-', 
            'meds': '-', 'history': '-', 'comment': '체질 바로보기 선택'
        }
    
    fake_scores = {'TY': 20, 'SY': 20, 'TE': 20, 'SE': 20}
    fake_scores[selected_type] = 100.0
    
    fake_symptoms = {}
    if selected_type == 'SE':
        fake_symptoms = {'pain': "몸살 기운 (으슬으슬 춥고 열이 남)", 'sweat': "땀이 거의 나지 않는다", 'stool': "설사를 하거나 묽다"}
    elif selected_type == 'SY':
        fake_symptoms = {'pain': "속 문제", 'stool': "변비가 있거나 잘 안 나온다", 'sweat': "보통"}
    elif selected_type == 'TE':
        fake_symptoms = {'pain': "몸살 기운 (으슬으슬 춥고 열이 남)", 'sweat': "보통", 'stool': "보통"}
    else: # TY
        fake_symptoms = {'pain': "보통", 'sweat': "보통", 'stool': "보통"}
        
    rec = get_recommendation(selected_type, fake_symptoms)
    
    st.session_state['final_result'] = {
        'code': selected_type,
        'scores': fake_scores,
        'rec': rec
    }
    st.session_state['step'] = 999
    st.rerun()

# ==========================================
# 화면 렌더링 함수
# ==========================================
def go_next():
    st.session_state['step'] += 1

def go_prev():
    if st.session_state['step'] > 0:
        st.session_state['step'] -= 1

def main():
    current_step = st.session_state['step']
    total_q = len(QUESTIONS)
    
    # ----------------------------------
    # STEP 0: 기본 정보 입력
    # ----------------------------------
    if current_step == 0:
        st.markdown("<h1 style='text-align: center;'>사상체질 자가진단</h1>", unsafe_allow_html=True)
        st.info("본 프로그램은 나에게 꼭 맞는 건강 관리의 시작을 위해 사상 체질을 진단하는 프로그램입니다. 객관성과 정확도를 높이기 위해 전국 한의대 교수진이 집필한 사상체질병증 한의표준임상진료지침을 준수하여 40개 문항으로 제작되었습니다. 정확한 사상 체질 진단을 위해 각 질문을 꼼꼼하게 읽고 작성해주십시오.")
        
        with st.form("info_form"):
            name = st.text_input("이름 (필수)", placeholder="홍길동")
            birth = st.text_input("생년월일 (필수)", placeholder="예: 1980.01.01")
            
            # 이메일 입력란 삭제됨
            
            col1, col2 = st.columns(2)
            with col1: height = st.text_input("키 (cm)", placeholder="175")
            with col2: weight = st.text_input("몸무게 (kg)", placeholder="70")
            
            meds = st.text_input("복용 중인 약 (선택)")
            history = st.text_input("과거 병력 (선택)")
            comment = st.text_area("증상 및 기타 (선택)", height=80)
            
            if st.form_submit_button("진단 시작하기", use_container_width=True):
                if not name or not birth:
                    st.error("이름과 생년월일은 필수입니다.")
                else:
                    st.session_state['user_info'] = {
                        'name': name, 'birth': birth, 'height': height,
                        'weight': weight, 'meds': meds, 'history': history, 'comment': comment
                    }
                    go_next()
                    st.rerun()

        st.write("")
        st.markdown("---")
        st.subheader("⚡ 체질별 결과 바로보기 (설문 건너뛰기)")
        st.caption("아래 버튼을 누르면 설문 없이 즉시 제출 완료 처리하고, 해당 체질 데이터를 관리자에게 전송합니다.")
        
        if name:
             st.session_state['user_info']['name'] = name
             st.session_state['user_info']['birth'] = birth

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("☀️ 태양인", use_container_width=True):
                go_shortcut('TY')
        with c2:
            if st.button("🔥 소양인", use_container_width=True):
                go_shortcut('SY')
        with c3:
            if st.button("🌲 태음인", use_container_width=True):
                go_shortcut('TE')
        with c4:
            if st.button("💧 소음인", use_container_width=True):
                go_shortcut('SE')


    # ----------------------------------
    # STEP 1 ~ N: 개별 질문
    # ----------------------------------
    elif 1 <= current_step <= total_q:
        q_idx = current_step - 1
        q_data = QUESTIONS[q_idx]
        
        progress = q_idx / total_q
        st.progress(progress)
        st.caption(f"질문 {current_step} / {total_q}")
        
        st.markdown(f"<div class='question-text'>Q{current_step}.<br>{q_data['q']}</div>", unsafe_allow_html=True)
        
        default_idx = st.session_state['answers_score'][q_idx]
        
        choice = st.radio(
            "답변을 선택하세요",
            OPTIONS,
            index=default_idx,
            key=f"q_{q_idx}",
            horizontal=False,
            label_visibility="collapsed"
        )
        
        st.write("")
        st.write("")
        
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
                
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                score_val = OPTIONS.index(choice)
                st.session_state['answers_score'][q_idx] = score_val
                st.session_state['answers_log'][q_idx] = f"Q{current_step}. {q_data['q']} : {choice}"
                go_next()
                st.rerun()

    # ----------------------------------
    # STEP N+1 ~ N+3: 증상 질문
    # ----------------------------------
    elif current_step == total_q + 1:
        st.progress(1.0)
        st.markdown("<div class='question-text'>거의 다 왔습니다!<br>Q. 아플 때 주로 어떤 느낌인가요?</div>", unsafe_allow_html=True)
        ans = st.radio("통증 유형", ["몸살 기운 (으슬으슬 춥고 열이 남)", "속 문제 (소화가 안 되고, 가슴이 답답하거나 배가 아픔)"], key="sym_pain", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state['symptom_answers']['pain'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 2:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 아플 때 땀은 어떻게 나나요?</div>", unsafe_allow_html=True)
        ans = st.radio("땀 유형", ["땀이 거의 나지 않는다", "식은땀이 나거나 땀이 축축하게 난다"], key="sym_sweat", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state['symptom_answers']['sweat'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 3:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 대변 상태는 어떤가요?</div>", unsafe_allow_html=True)
        ans = st.radio("대변 유형", ["변비가 있거나 잘 안 나온다", "설사를 하거나 묽다", "평소와 비슷하다(보통)"], key="sym_stool", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("제출 하기", use_container_width=True):
                st.session_state['symptom_answers']['stool'] = ans
                
                raw_scores = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
                type_counts = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
                
                for i, score in enumerate(st.session_state['answers_score']):
                    q_type = QUESTIONS[i]['type']
                    raw_scores[q_type] += score
                    type_counts[q_type] += 1
                
                avg_scores = {k: (v / type_counts[k] if type_counts[k] > 0 else 0) for k, v in raw_scores.items()}
                max_score = max(avg_scores.values())
                result_types = [k for k, v in avg_scores.items() if v == max_score]
                my_type_code = result_types[0] 
                
                recommendation = get_recommendation(my_type_code, st.session_state['symptom_answers'])
                
                with st.spinner("결과 분석 및 전송 중..."):
                    answers_summary = "\n".join(st.session_state['answers_log'])
                    answers_summary += f"\n[증상] Pain: {st.session_state['symptom_answers']['pain']}"
                    answers_summary += f"\n[증상] Sweat: {st.session_state['symptom_answers']['sweat']}"
                    answers_summary += f"\n[증상] Stool: {st.session_state['symptom_answers']['stool']}"
                    
                    scores_str = ", ".join([f"{TYPE_MAP[k]}: {v:.1f}점" for k, v in avg_scores.items()])
                    info = st.session_state['user_info']

                    # 1. 관리자에게 보내는 메일 (처방 포함 전체 내용 + 사용자 이메일 정보 포함)
                    admin_body = f"""
[관리자 알림] 사용자 진단 결과
이름: {info['name']} ({info['birth']})
이메일: {info.get('email', '미입력')}
키/몸무게: {info.get('height','')}cm / {info.get('weight','')}kg
체질: {TYPE_MAP.get(my_type_code)}
점수: {scores_str}

[건강 정보]
약: {info.get('meds','')}
병력: {info.get('history','')}
코멘트: {info.get('comment','')}

[추천처방]
병증: {recommendation['condition']}
처방: {recommendation['prescription']}
설명: {recommendation['desc']}

[설문응답 로그]
{answers_summary}
                    """
                    send_email_logic(RECEIVER_EMAIL, f"[관리자] {info['name']}님 결과", admin_body)

                    # 2. 사용자에게 보내는 메일 (제출 확인용, 결과 제외) -> 이메일 입력 삭제로 작동 안 함
                    user_email = info.get('email')
                    if user_email:
                        user_body = f"""
안녕하세요, {info['name']}님.

디스코 한의원 사상체질 문진표가 성공적으로 제출되었습니다.
작성해주신 내용을 바탕으로 진료실에서 원장님과 상담 후 정확한 진단 결과를 안내해 드리겠습니다.

[제출 일시] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

감사합니다.
                        """
                        send_email_logic(user_email, f"[{info['name']}님] 문진표 제출 완료 안내", user_body)
                
                st.session_state['final_result'] = {
                    'code': my_type_code,
                    'scores': avg_scores,
                    'rec': recommendation
                }
                st.session_state['step'] = 999
                st.rerun()

    # ----------------------------------
    # [STEP 999] 제출 완료 화면 (결과 숨김)
    # ----------------------------------
    elif current_step == 999:
        st.balloons()
        
        st.success("✅ 문진표 작성이 완료되었습니다!")
        
        st.markdown("""
        <div style="text-align: center; margin: 50px 0;">
            <h3>설문에 참여해 주셔서 감사합니다.</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
            작성하신 내용은 원장님께 안전하게 전달되었습니다.<br>
            잠시만 대기해 주시면, <b>진료실에서 상세한 상담 및 체질 진단</b>을 도와드리겠습니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # [안내 문구 추가]
        if st.session_state['user_info'].get('email'):
            st.info(f"📧 입력하신 이메일({st.session_state['user_info']['email']})로 제출 확인 메일을 보내드렸습니다.")

        st.markdown("---")

        # [추가 요청] 추가 문의 사항 입력 필드
        st.markdown("##### ❓ 궁금한 점이 있으신가요?")
        feedback = st.text_area("체질이나 증상에 대해 더 궁금한 점이 있다면 적어주세요. 진료 시 참고하겠습니다. (선택)", height=80, key="final_feedback")

        if st.button("📨 문의 내용 추가 전송"):
            if feedback:
                # 관리자에게 메일 발송
                f_subject = f"[추가문의] {st.session_state['user_info']['name']}님 ({st.session_state['user_info']['birth']})"
                f_body = f"""
                [추가 문의 사항]
                작성자: {st.session_state['user_info']['name']}
                연락처(이메일): {st.session_state['user_info'].get('email', '미입력')}

                문의 내용:
                {feedback}
                """
                send_email_logic(RECEIVER_EMAIL, f_subject, f_body)
                st.success("소중한 의견이 원장님께 전달되었습니다!")
            else:
                st.toast("내용을 입력해주세요.")

        st.write("") 
        
        if st.button("🔄 처음부터 다시하기", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()
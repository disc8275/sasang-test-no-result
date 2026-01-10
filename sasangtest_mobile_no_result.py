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
    SENDER_EMAIL = "test@example.com"
    SENDER_PASSWORD = "password"

RECEIVER_EMAIL = "ds1lih@naver.com" 

# ==========================================
# 1. 페이지 설정 및 스타일
# ==========================================
st.set_page_config(page_title="디스코한의원 문진표", layout="centered")

# CSS 스타일 수정: 다크모드/라이트모드 자동 호환
st.markdown("""
    <style>
    /* 배경색 강제 지정 제거 (다크모드 호환을 위해) */
    
    /* 제목 색상을 테마 기본 텍스트 색상으로 변경 */
    h1 { 
        color: var(--text-color); 
        font-size: 1.5rem; 
    }
    
    /* 부제목 색상을 테마 포인트 색상으로 변경 */
    h3 { 
        color: var(--primary-color); 
        font-size: 1.2rem; 
    }
    
    .stButton button {
        height: 3rem;
        font-size: 1.1rem;
        border-radius: 10px;
    }
    
    div[data-testid="stRadio"] label {
        font-size: 1.1rem !important;
        padding: 10px 0;
        cursor: pointer;
    }
    
    /* 질문 텍스트 스타일 수정 */
    .question-text {
        font-size: 1.3rem;
        font-weight: bold;
        /* 고정된 색상(#333)을 제거하고 Streamlit 테마 변수 사용 */
        color: var(--text-color); 
        margin-bottom: 20px;
        line-height: 1.5;
    }
    
    /* 인쇄 시 강제 페이지 넘김을 위한 클래스 */
    @media print {
        .page-break { 
            page-break-before: always !important; 
            display: block !important;
            height: 1px;
        }
    }
    
    /* 인쇄 최적화 스타일 (머리글/바닥글 제거 및 빈 페이지 방지) */
    @media print {
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
            /* 인쇄 시에는 글자를 무조건 검정으로 (종이 절약/가독성) */
            color: black !important; 
            background-color: white !important;
        }
        
        .stApp {
            min-height: 0 !important;
            height: auto !important;
            overflow: visible !important;
        }

        .block-container {
            margin: 15mm 15mm 0 15mm !important; 
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            width: auto !important;
        }

        /* 인쇄 시 모든 텍스트 강제 검정색 */
        h1, h3, .question-text, p, div {
            color: black !important;
            -webkit-text-fill-color: black !important;
        }

        section[data-testid="stSidebar"], 
        header, 
        footer, 
        .stAppDeployButton, 
        button, 
        .stButton, 
        div[data-testid="stHorizontalBlock"], 
        .stProgress,
        iframe {
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

        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
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
    st.session_state['step'] = 0  # 0: 정보입력, 1~N: 질문, N+1~: 증상, 999: 결과
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}
if 'answers_score' not in st.session_state:
    st.session_state['answers_score'] = [2] * len(QUESTIONS) # 기본값 보통(2)
if 'answers_log' not in st.session_state:
    st.session_state['answers_log'] = [""] * len(QUESTIONS)
if 'symptom_answers' not in st.session_state:
    st.session_state['symptom_answers'] = {}
if 'final_result' not in st.session_state:
    st.session_state['final_result'] = None

# ==========================================
# 로직 함수 (이메일 및 추천)
# ==========================================
def send_email_result(info, constitution, scores, recommendation, answers_summary):
    try:
        subject = f"[사상체질진단 결과] {info['name']}님 ({info['birth']})"
        scores_str = ", ".join([f"{TYPE_MAP[k]}: {v:.1f}점" for k, v in scores.items()])

        body = f"""
[사용자 기본 정보]
- 이름: {info['name']}
- 생년월일: {info['birth']}
- 키/몸무게: {info.get('height','')}cm / {info.get('weight','')}kg
- 진단 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[건강 상세 정보]
- 약: {info.get('meds','')}
- 병력: {info.get('history','')}
- 코멘트: {info.get('comment','')}

[진단 결과]
- 체질: {TYPE_MAP.get(constitution, '알수없음')}
- 점수: {scores_str}

[추천 처방]
- 병증: {recommendation['condition']}
- 처방: {recommendation['prescription']}

[설문 응답 상세]
{answers_summary}
        """
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Fail: {e}")
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
        st.title("🩺 디스코한의원 문진표")
        st.info("이 프로그램은 한의표준임상진료지침을 바탕으로 제작했습니다. 꼼꼼하게 읽고 작성해주십시오.")
        
        with st.form("info_form"):
            name = st.text_input("이름 (필수)", placeholder="홍길동")
            birth = st.text_input("생년월일 (필수)", placeholder="예: 1980.01.01")
            col1, col2 = st.columns(2)
            with col1: height = st.text_input("키 (cm)", placeholder="175")
            with col2: weight = st.text_input("몸무게 (kg)", placeholder="70")
            
            meds = st.text_input("복용 중인 약 (선택)")
            history = st.text_input("과거 병력 (선택)")
            comment = st.text_area("원장님께 하고 싶은 말씀 (선택)", height=80)
            
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

    # ----------------------------------
    # STEP 1 ~ N: 개별 질문
    # ----------------------------------
    elif 1 <= current_step <= total_q:
        q_idx = current_step - 1
        q_data = QUESTIONS[q_idx]
        
        # 진행률 표시
        progress = q_idx / total_q
        st.progress(progress)
        st.caption(f"질문 {current_step} / {total_q}")
        
        st.markdown(f"<div class='question-text'>Q{current_step}.<br>{q_data['q']}</div>", unsafe_allow_html=True)
        
        # 이전 선택값 불러오기 (없으면 '보통이다')
        default_idx = st.session_state['answers_score'][q_idx]
        
        # 수직 라디오 버튼 (horizontal=False)
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
        
        # 버튼을 2개 컬럼으로 나눔 (이전 / 다음)
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
    # STEP N+1 ~ N+3: 증상 질문 (처방용)
    # ----------------------------------
    elif current_step == total_q + 1:
        st.progress(1.0)
        st.markdown("<div class='question-text'>거의 다 왔습니다!<br>Q. 아플 때 주로 어떤 느낌인가요?</div>", unsafe_allow_html=True)
        ans = st.radio("통증 유형", ["몸살 기운 (으슬으슬 춥고 열이 남)", "속 문제 (소화가 안 되고, 가슴이 답답하거나 배가 아픔)"], key="sym_pain", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", key="prev_sym1", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", key="next_sym1", use_container_width=True):
                st.session_state['symptom_answers']['pain'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 2:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 아플 때 땀은 어떻게 나나요?</div>", unsafe_allow_html=True)
        ans = st.radio("땀 유형", ["땀이 거의 나지 않는다", "식은땀이 나거나 땀이 축축하게 난다"], key="sym_sweat", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", key="prev_sym2", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", key="next_sym2", use_container_width=True):
                st.session_state['symptom_answers']['sweat'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 3:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 대변 상태는 어떤가요?</div>", unsafe_allow_html=True)
        ans = st.radio("대변 유형", ["변비가 있거나 잘 안 나온다", "설사를 하거나 묽다", "평소와 비슷하다(보통)"], key="sym_stool", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", key="prev_sym3", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("설문 완료 (결과 전송)", key="finish", use_container_width=True):
                st.session_state['symptom_answers']['stool'] = ans
                
                # --- 계산 로직 수행 ---
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
                
                # 이메일 전송
                with st.spinner("결과 분석 및 전송 중..."):
                    answers_summary = "\n".join(st.session_state['answers_log'])
                    answers_summary += f"\n[증상] Pain: {st.session_state['symptom_answers']['pain']}"
                    answers_summary += f"\n[증상] Sweat: {st.session_state['symptom_answers']['sweat']}"
                    answers_summary += f"\n[증상] Stool: {st.session_state['symptom_answers']['stool']}"
                    
                    send_email_result(
                        st.session_state['user_info'], my_type_code, avg_scores, recommendation, answers_summary
                    )
                
                # 결과 저장
                st.session_state['final_result'] = {
                    'code': my_type_code,
                    'scores': avg_scores,
                    'rec': recommendation
                }
                st.session_state['step'] = 999
                st.rerun()

    # ----------------------------------
    # 결과 화면
    # ----------------------------------
    elif current_step == 999:
        res = st.session_state['final_result']
        my_code = res['code']
        rec = res['rec']
        scores = res['scores']

        st.balloons()
        
        # 동점자 처리 및 타이틀
        max_score = max(scores.values())
        tied_keys = [k for k, v in scores.items() if v == max_score]

        if len(tied_keys) > 1:
            tied_names = [TYPE_MAP[k] for k in tied_keys]
            title_text = " 또는 ".join(tied_names)
            st.title(f"🎉 당신은 [{title_text}]일 확률이 같습니다!")
            st.warning(f"📢 **알림:** 점수가 동일하여 **{title_text}** 모두 해당될 가능성이 있습니다.\n\n시스템은 그중 **[{TYPE_MAP[my_code]}]**을 기준으로 상세 결과와 처방을 보여드립니다.")
            my_name = TYPE_MAP[my_code]
        else:
            my_name = TYPE_MAP[my_code]
            st.title(f"🎉 당신은 [{my_name}] 입니다!")

        # 차트 표시
        st.write("체질별 점수")
        chart_df = pd.DataFrame({'체질': [TYPE_MAP[k] for k in scores], '점수': list(scores.values())})
        st.bar_chart(chart_df.set_index('체질'))
        
        # 처방 표시
        st.success(f"### 💊 추천 처방: {rec['prescription']}")
        st.info(f"**상태:** {rec['condition']}\n\n**설명:** {rec['desc']}")

        # ------------------------------------------
        # [중요] 인쇄 시 페이지 나누기 (Page Break)
        # ------------------------------------------
        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.header(f"📋 {my_name} 상세 건강 가이드")

        # =========================================================
        # 상세 건강 가이드 (이전 STEP 1000 내용 통합)
        # =========================================================
        if my_code == 'SE': # 소음인
            st.markdown("""
            **1. 소음인의 특징**
            * 몸이 찬 편입니다.
            * 전반적인 체력이 약한 편입니다.
            * 소화기의 기능이 약해지기 쉽습니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **전신:** 무리를 하지 않았는데도 피로감이 지속되고, 아침에 일어나기 힘듭니다.
            * **소화:** 식욕이 떨어지고 소화가 잘 안 되며, 배에 가스가 찹니다.
            * **배설:** 설사를 자주 하거나, 대변이 가늘면서 시원하지 않습니다.
            * **기타:** 손발과 배가 차고, 특별한 이유 없이 마음이 늘 불안합니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **보온:** 항상 몸을 따뜻하게 합니다.
            2. **휴식:** 과로를 피하고 적절한 휴식이 필요합니다.
            3. **식사:** 규칙적인 식사가 중요하며, 따뜻한 성질의 음식이나 약간의 자극성 있는 조미료가 좋습니다.
            """)
            
            st.subheader("🥗 소음인에게 이로운 음식")
            food_data = {
                "분류": ["곡류군", "저지방 어육류", "중지방 어육류", "고지방 어육류", "채소군", "지방군/우유/과일"],
                "권장 음식": [
                    "백미, 차조, 찹쌀, 감자, 옥수수 / (떡, 누룽지)",
                    "닭고기(껍질/기름 제거), 명태, 조기, 도미, 대구, 민어, 농어, 가자미, 멸치",
                    "삼치, 갈치, 장어, 민어, 도루묵",
                    "닭고기(껍질 포함), 개고기, 뱀장어",
                    "깻잎, 냉이, 시금치, 양배추, 브로콜리, 마늘, 파, 고추, 양파, 부추, 쑥",
                    "들깨, 참기름, 산양유 / 사과, 귤, 토마토, 복숭아, 대추, 유자"
                ]
            }
            st.table(pd.DataFrame(food_data).set_index("분류"))

        elif my_code == 'SY': # 소양인
            st.markdown("""
            **1. 소양인의 특징**
            * 몸에 열이 많습니다.
            * 신경이 예민하고, 피부, 장, 방광 등이 과민한 편입니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **수면/정서:** 잠들기 어렵고 자주 깨며, 마음이 조급하고 불안합니다.
            * **배설:** 소변을 자주 보거나 색이 진하며, 변비나 설사가 잦습니다.
            * **신체:** 얼굴이나 피부 트러블이 잦고, 입이 마르며 갈증이 납니다.
            * **소화:** 가슴이 답답하고 속이 쓰리거나 구역질을 합니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **수면/마음:** 충분한 수면을 취하고, 매사에 여유를 가지려 노력하세요.
            2. **식사:** 천천히 식사하며, 서늘한 성질의 음식/해물/채소가 좋습니다.
            3. **피할 것:** 맵고 짠 음식, 성질이 더운 음식을 피하세요.
            4. **운동:** 하체를 강화시켜 주는 운동(등산, 자전거 등)이 좋습니다.
            """)
            
            st.subheader("🥗 소양인에게 이로운 음식")
            food_data = {
                "분류": ["곡류군", "저지방 어육류", "중지방 어육류", "고지방 어육류", "채소군", "지방군/우유/과일"],
                "권장 음식": [
                    "보리, 팥, 녹두 / (메밀, 고구마, 토란)",
                    "돼지고기(살코기), 오리고기, 복어, 굴, 새우, 오징어, 낙지, 조개, 게, 해삼",
                    "돼지고기(안심), 계란 / (두부, 고등어, 꽁치)",
                    "삼겹살, 족발, 돼지갈비, 베이컨",
                    "오이, 가지, 배추, 상추, 우엉, 숙주나물, 죽순",
                    "참깨, 참기름, 우유 / 딸기, 수박, 바나나, 참외, 메론, 키위"
                ]
            }
            st.table(pd.DataFrame(food_data).set_index("분류"))

        elif my_code == 'TE': # 태음인
            st.markdown("""
            **1. 태음인의 특징**
            * 섭취한 에너지를 소모시키고 배설시키는 것이 취약합니다.
            * 체구가 큰 편이고, 식욕과 위장기능이 좋아 비만해지기 쉽습니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **체중/식욕:** 살이 찌고, 배가 부른데도 자꾸 먹게 됩니다.
            * **배설:** 대변이 굳거나 설사가 잦아지는 등 양상이 달라집니다.
            * **신체:** 땀이 잘 나지 않거나, 상체로만 진땀이 많이 납니다. 아침에 얼굴/손발이 붓습니다.
            * **피부:** 얼굴이 붉어지고 열감이 많으며, 피부 트러블이 잦습니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **관리:** 변비와 체중 증가를 항상 경계해야 합니다.
            2. **식사:** 과식/폭식/야식을 피하고, 천천히 먹습니다. 식후 바로 눕지 마세요.
            3. **운동:** 땀을 흘릴 정도의 유산소 운동(열량 소모 많은 운동)이 좋습니다.
            """)
            
            st.subheader("🥗 태음인에게 이로운 음식")
            food_data = {
                "분류": ["곡류군", "저지방 어육류", "중지방 어육류", "고지방 어육류", "채소군", "지방군/우유/과일"],
                "권장 음식": [
                    "현미, 율무, 콩, 고구마, 옥수수, 토란, 밤, 마, 잣, 호두, 땅콩",
                    "소고기(사태, 홍두깨), 대구, 조기, 명태, 민어, 오징어",
                    "소고기(등심, 안심), 고등어, 꽁치, 갈치, 두부, 콩비지",
                    "소갈비, 뱀장어, 유부, 치즈",
                    "무, 호박, 콩나물, 고사리, 버섯, 김, 미역, 다시마, 도라지, 연근, 당근",
                    "들기름, 올리브유, 우유, 두유 / 배, 매실, 자두, 살구"
                ]
            }
            st.table(pd.DataFrame(food_data).set_index("분류"))

        elif my_code == 'TY': # 태양인
            st.markdown("""
            **1. 태양인의 특징**
            * 에너지를 축적하는 기능은 약하고, 발산/소모시키는 기능은 강합니다.
            * 머리와 목덜미가 발달한 반면, 허리나 하체가 빈약한 편입니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **신체:** 쉽게 몸살이 나고, 하체가 쉽게 피로하여 오래 걷기 힘듭니다.
            * **배설:** 소변 양과 횟수가 줄거나, 대변이 염소똥처럼 굳어집니다.
            * **입/소화:** 입 안에 맑은 침이나 거품이 고이고, 구역질을 합니다.
            * **정서:** 매사에 조급해지고 화가 잘 납니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **식사:** 매운 자극성 음식, 고지방 음식을 피하고 담백한 음식/해물/채소가 좋습니다.
            2. **운동:** 과격한 운동은 피하고, 허리/하체 근력 강화 운동을 하세요.
            3. **마음:** 조급해하지 말고 여유를 가지며, 원만한 인간관계를 유지하세요.
            """)
            
            st.subheader("🥗 태양인에게 이로운 음식")
            food_data = {
                "분류": ["곡류군", "저지방 어육류", "중지방 어육류", "고지방 어육류", "채소군", "지방군/우유/과일"],
                "권장 음식": [
                    "메밀(국수, 묵, 밥) / (보리, 녹두, 팥)",
                    "굴, 새우, 게, 오징어, 문어, 전복, 조개, 해삼, 홍합 / (흰살생선)",
                    "(사용 가능) 고등어, 꽁치, 장어",
                    "(해당 없음 / 육류는 피하는 것이 좋음)",
                    "상추, 깻잎, 배추, 오이, 가지, 시금치, 우엉, 숙주나물, 죽순",
                    "참깨 / 포도, 머루, 다래, 감, 키위, 파인애플, 오렌지"
                ]
            }
            st.table(pd.DataFrame(food_data).set_index("분류"))

        st.markdown("---")
        
        # 인쇄 버튼 (인쇄 시에는 보이지 않음)
        print_btn_code = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width:100%; padding:10px; background:white; border:1px solid #ddd; border-radius:5px;">🖨️ 결과 저장/인쇄</button>
        """
        components.html(print_btn_code, height=50)
        
        if st.button("🔄 처음부터 다시하기", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()
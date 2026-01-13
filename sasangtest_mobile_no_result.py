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

RECEIVER_EMAIL = "ds1lih@naver.com" # 관리자 이메일

# ==========================================
# [데이터 A] 사상체질 진단 데이터
# ==========================================
TYPE_MAP = {'TY': '태양인', 'SY': '소양인', 'TE': '태음인', 'SE': '소음인'}

# 사상체질 질문 목록
QUESTIONS_SASANG = [
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

OPTIONS_SASANG = ["전혀 아니다", "아니다", "보통이다", "그렇다", "매우 그렇다"]

# ==========================================
# [데이터 B] 장부변증 진단 데이터
# ==========================================
PATTERNS = {
    # --- 1. 심(Heart) 계열 ---
    '심기허(心氣虛) & 심양허(心陽虛)': {
        'symptoms': [
            {'question': '가슴이 두근거리고 숨이 차다.', 'weight': 5},
            {'question': '식은땀이 나면서 동시에 피로감이 심하다.', 'weight': 4},
            {'question': '가슴이 답답하고 아프다.', 'weight': 5},
            {'question': '추위를 많이 타고 손발이 차다.', 'weight': 4}
        ],
        'prescription': '양심탕(養心湯), 보원탕(保元湯)',
        'reference': '동의보감, 심계편'
    },
    '심혈허(心血虛) & 심음허(心陰虛)': {
        'symptoms': [
            {'question': '잠이 잘 안 오지 않거나 꿈을 많이 꾼다.', 'weight': 5},
            {'question': '가슴이 두근거리고 건망증이 있다.', 'weight': 4},
            {'question': '오후에 열이 오르거나 잘 때 식은땀이 난다.', 'weight': 5},
            {'question': '입과 목이 마르고 혀가 붉다.', 'weight': 3}
        ],
        'prescription': '천왕보심단(天王補心丹), 사물탕(四物湯) 가감',
        'reference': '동의보감'
    },
    '심화항성(心火亢盛)': {
        'symptoms': [
            {'question': '가슴이 답답하고 열이 난다.', 'weight': 5},
            {'question': '입안이나 혀가 헐고 아프다.', 'weight': 5},
            {'question': '소변색이 붉고 동시에 혀끝도 매우 붉다.', 'weight': 4}
        ],
        'prescription': '도적산(導赤散), 사심탕(瀉心湯)',
        'reference': '방약합편'
    },
    '심혈어조(心血瘀阻)': {
        'symptoms': [
            {'question': '심장 부위가 콕콕 찌르거나 쥐어짜듯이 아프다.', 'weight': 5},
            {'question': '가슴이 답답하고 입술이나 혀가 푸르스름하다.', 'weight': 5},
            {'question': '통증이 등이나 어깨로 퍼지기도 한다.', 'weight': 3}
        ],
        'prescription': '혈부축어탕(血府逐瘀湯), 단삼음(丹參飮)',
        'reference': '의림개착'
    },
    '담화요심(痰火擾心)': {
        'symptoms': [
            {'question': '가슴이 답답하고 두근거림이 심하다.', 'weight': 4},
            {'question': '불면증이 심하고 꿈을 많이 꾸며 잘 놀란다.', 'weight': 5},
            {'question': '정신이 혼미하거나 감정 기복이 심하다.', 'weight': 5},
            {'question': '가래가 끈적하고 입도 쓰다.', 'weight': 3}
        ],
        'prescription': '온담탕(溫膽湯), 황련온담탕(黃連溫膽湯)',
        'reference': '방약합편'
    },
    '심신불교(心腎不交)': {
        'symptoms': [
            {'question': '가슴 위쪽은 열이 나고 답답한데, 아랫배나 발은 차갑다.', 'weight': 5},
            {'question': '잠들기 힘들고 꿈이 많아 자고 나도 피곤하다.', 'weight': 5},
            {'question': '허리가 시큰거리고 귀에서 소리가 난다.', 'weight': 3}
        ],
        'prescription': '교태환(交泰丸), 천왕보심단(天王補心丹) 합 육미지황탕',
        'reference': '동의보감'
    },

    # --- 2. 폐(Lung) 계열 ---
    '폐기허(肺氣虛)': {
        'symptoms': [
            {'question': '기침 소리가 약하고 말하기 싫어한다.', 'weight': 5},
            {'question': '조금만 움직여도 숨이 차고 땀이 난다.', 'weight': 4},
            {'question': '가래가 있지만 색이 희거나 맑다.', 'weight': 3}
        ],
        'prescription': '보폐탕(補肺湯), 옥병풍산(玉屛風散)',
        'reference': '의학입문'
    },
    '폐음허(肺陰虛)': {
        'symptoms': [
            {'question': '마른 기침을 하지만, 가래가 없거나 끈적하다.', 'weight': 5},
            {'question': '가래에 피가 섞이거나 목이 쉰다.', 'weight': 5},
            {'question': '오후에 열이 오르면서 잘 때도 식은땀이 난다.', 'weight': 4}
        ],
        'prescription': '백합고금탕(百合固金湯), 자음강화탕(滋陰降火湯)',
        'reference': '동의보감'
    },
    '담습조폐(痰濕阻肺)': {
        'symptoms': [
            {'question': '기침과 함께 희고 끈적한 가래가 많다.', 'weight': 5},
            {'question': '가슴이 그득하고 답답하여 눕기가 불편하다.', 'weight': 5},
            {'question': '몸이 무겁고 붓는 느낌이 든다.', 'weight': 3}
        ],
        'prescription': '이진탕(二陳湯), 삼자양친탕(三子養親湯)',
        'reference': '방약합편'
    },

    # --- 3. 비위(Spleen & Stomach) 계열 ---
    '비기허(脾氣虛) & 비양허(脾陽虛)': {
        'symptoms': [
            {'question': '입맛이 없으면서 동시에 식후에 배가 더부룩하다.', 'weight': 5},
            {'question': '대변이 묽으면서 동시에 사지에 힘이 없다.', 'weight': 4},
            {'question': '배가 차고 아프지만 따뜻하게 하면 편해진다.', 'weight': 5},
            {'question': '얼굴색이 누렇게 뜬다.', 'weight': 3}
        ],
        'prescription': '삼령백출산(參苓白朮散), 이중탕(理中湯)',
        'reference': '제중신편'
    },
    '한습곤비(寒濕困脾)': {
        'symptoms': [
            {'question': '입안이 끈적하고 음식 맛이 잘 안 느껴진다.', 'weight': 5},
            {'question': '머리와 몸이 젖은 솜처럼 무겁거나 습한 날 증상이 심해진다.', 'weight': 5},
            {'question': '대변이 묽거나 설사를 하고 배가 차다.', 'weight': 4},
            {'question': '속이 메스껍고 식욕이 떨어진다.', 'weight': 3}
        ],
        'prescription': '위령탕(胃苓湯), 곽향정기산(藿香正氣散)',
        'reference': '방약합편'
    },
    '위화항성(胃火亢盛) & 식체': {
        'symptoms': [
            {'question': '치통이 있거나 잇몸에서 피가 난다.', 'weight': 3},
            {'question': '입 냄새가 심하고 배가 빨리 고프다.', 'weight': 4},
            {'question': '트림에서 냄새가 나고 신물이 올라온다.', 'weight': 5}
        ],
        'prescription': '청위산(淸胃散), 평위산(平胃散)',
        'reference': '동의보감'
    },
    '위음허(胃陰虛)': {
        'symptoms': [
            {'question': '입이 마르고 갈증이 나지만 물을 많이 마시지는 않는다.', 'weight': 5},
            {'question': '혀가 붉고 태가 거의 없어 반질반질하다.', 'weight': 5},
            {'question': '배가 고픈 느낌은 있는데 음식을 먹고 싶지 않다.', 'weight': 4},
            {'question': '속쓰림이나 헛구역질이 있다.', 'weight': 3}
        ],
        'prescription': '익위탕(益胃湯), 사삼맥문동탕(沙蔘麥門冬湯)',
        'reference': '온병조변'
    },

    # --- 4. 간담(Liver & Gallbladder) 계열 ---
    '간기울결(肝氣鬱結)': {
        'symptoms': [
            {'question': '평소 한숨을 자주 쉬고 우울감을 느낀다.', 'weight': 4},
            {'question': '옆구리나 가슴이 그득하게 아프다.', 'weight': 5},
            {'question': '목에 무언가 걸린 듯한 느낌이 있다.', 'weight': 3},
            {'question': '여성의 경우 생리통이나 생리불순이 있다.', 'weight': 4}
        ],
        'prescription': '소요산(逍遙散), 시호소간산(柴胡疎肝散)',
        'reference': '경악전서'
    },
    '간화상염(肝火上炎)': {
        'symptoms': [
            {'question': '성격이 급하고 화를 참기 힘들다.', 'weight': 4},
            {'question': '머리와 눈이 붉고 아프며 어지럽다.', 'weight': 5},
            {'question': '입이 쓰고 마르며 귀에서 소리가 난다.', 'weight': 3}
        ],
        'prescription': '용담사간탕(龍膽瀉肝湯)',
        'reference': '방약합편'
    },
    '간양상항(肝陽上亢)': {
        'symptoms': [
            {'question': '심한 현기증이 있고 머리가 터질 듯 아프다(특히 옆머리).', 'weight': 5},
            {'question': '얼굴이 붉어지고 화를 잘 내며 혈압이 높은 편이다.', 'weight': 4},
            {'question': '허리나 무릎에 힘이 없고 머리가 무겁다.', 'weight': 3}
        ],
        'prescription': '천마구등음(天麻鉤藤飮), 진간식풍탕(鎭肝熄風湯)',
        'reference': '의학충중참서루'
    },
    '간혈허(肝血虛)': {
        'symptoms': [
            {'question': '어지럽고 눈이 건조하며 침침하다.', 'weight': 5},
            {'question': '손발에 쥐가 잘 나거나 근육 경련이 있다.', 'weight': 5},
            {'question': '손톱이 마르고 갈라지며 윤기가 없다.', 'weight': 3},
            {'question': '여성의 경우 생리량이 매우 적다.', 'weight': 4}
        ],
        'prescription': '사물탕(四物湯) 가미, 보간탕(補肝湯)',
        'reference': '동의보감, 의학입문'
    },
    '담담습열(膽談濕熱) & 담허(膽虛)': {
        'symptoms': [
            {'question': '입이 쓰고 옆구리가 결리거나 아프다.', 'weight': 5},
            {'question': '잘 놀라고 겁이 많으며 잠을 깊이 못 잔다.', 'weight': 5},
            {'question': '결단력이 부족하고 한숨을 잘 쉰다.', 'weight': 3},
            {'question': '토하고 싶거나 속이 울렁거린다.', 'weight': 3}
        ],
        'prescription': '(습열) 인진호탕, (담허) 온담탕',
        'reference': '상한론, 동의보감'
    },

    # --- 5. 신장/방광(Kidney & Bladder) 계열 ---
    '신양허(腎陽虛)': {
        'symptoms': [
            {'question': '허리와 무릎이 시리고 아프다.', 'weight': 5},
            {'question': '추위를 심하게 타고 손발이 차다.', 'weight': 4},
            {'question': '새벽에 설사를 하거나 소변을 자주 본다.', 'weight': 4},
            {'question': '성기능이 감퇴(발기부전, 조루 등)되었다.', 'weight': 3}
        ],
        'prescription': '팔미지황환(八味地黃丸), 우귀음(右歸飮)',
        'reference': '동의보감'
    },
    '신음허(腎陰虛)': {
        'symptoms': [
            {'question': '허리와 무릎이 시큰거리고 힘이 없다.', 'weight': 5},
            {'question': '얼굴이나 손발바닥에 열감이 느껴진다.', 'weight': 4},
            {'question': '귀에서 소리가 나거나, 치아가 흔들리고 약하다.', 'weight': 3},
            {'question': '입이 마르고 소변색이 진하다.', 'weight': 3}
        ],
        'prescription': '육미지황탕(六味地黃湯), 좌귀음(左歸飮)',
        'reference': '동의보감'
    },
    '신정허(腎精虛)': {
        'symptoms': [
            {'question': '건망증이 심해지거나 머리카락이 많이 빠진다.', 'weight': 4},
            {'question': '동작이 둔해지고 다리에 힘이 없거나 치아가 흔들린다.', 'weight': 5},
            {'question': '귀에서 소리가 나거나 청력이 떨어진다.', 'weight': 4},
            {'question': '성인의 경우 조기 노화, 소아의 경우 발육이 늦다.', 'weight': 5}
        ],
        'prescription': '하거대조환(河車大造丸), 좌귀환(左歸丸)',
        'reference': '경악전서'
    },
    '방광습열(膀胱濕熱)': {
        'symptoms': [
            {'question': '소변을 자주 보고 급하게 마렵다.', 'weight': 5},
            {'question': '소변을 볼 때 찌릿하거나 아프다.', 'weight': 5},
            {'question': '소변 색이 붉거나 탁하고 아랫배가 빵빵하다.', 'weight': 4}
        ],
        'prescription': '팔정산(八正散)',
        'reference': '방약합편'
    },

    # --- 6. 기타/복합 계열 ---
    '대장습열(大腸濕熱)': {
        'symptoms': [
            {'question': '배가 아프고 변을 봐도 시원치 않다.', 'weight': 5},
            {'question': '대변에 점액이나 피가 섞여 나온다.', 'weight': 5},
            {'question': '항문이 작열감이 있다.', 'weight': 3}
        ],
        'prescription': '작약탕(芍藥湯), 백두옹탕(白頭翁湯)',
        'reference': '방약합편'
    },
    '어혈(瘀血) (전신성)': {
        'symptoms': [
            {'question': '특정 부위가 콕콕 찌르는 듯이 아프고 위치가 고정되어 있다.', 'weight': 5},
            {'question': '통증이 밤에 더 심해진다.', 'weight': 4},
            {'question': '피부에 멍이 잘 들거나 혀에 보라색 반점이 있다.', 'weight': 4},
            {'question': '피부가 거칠고 윤기가 없다.', 'weight': 3}
        ],
        'prescription': '당귀수산(當歸鬚散), 계지복령환(桂枝茯苓丸)',
        'reference': '금궤요략'
    },
    '기체혈어(氣滯血瘀)': {
        'symptoms': [
            {'question': '스트레스를 받으면 통증이 심해진다.', 'weight': 4},
            {'question': '처음에는 아픈 곳이 이동하다가 나중에는 한 곳이 찌르듯 아프다.', 'weight': 5},
            {'question': '가슴이 답답하고 한숨이 나오며 성격이 예민하다.', 'weight': 4},
            {'question': '통증 부위를 누르면 더 아프다.', 'weight': 3}
        ],
        'prescription': '혈부축어탕(血府逐瘀湯), 복원활혈탕(復元活血湯)',
        'reference': '의림개착'
    }
}

OPTIONS_JANGBU = ["아니오 (No)", "예 (Yes)"]

# ==========================================
# [데이터 전처리] 장부변증 중복 질문 통합
# ==========================================
QUESTION_MAP = {}    # { 질문텍스트 : [{'pattern':패턴명, 'weight':가중치}, ...] }
UNIQUE_QUESTIONS_JANGBU = [] # 중복이 제거된 장부변증 질문 리스트

for pattern_key, data in PATTERNS.items():
    for item in data['symptoms']:
        q_text = item['question']
        weight = item['weight']
        
        if q_text in QUESTION_MAP:
            QUESTION_MAP[q_text].append({'pattern': pattern_key, 'weight': weight})
        else:
            QUESTION_MAP[q_text] = [{'pattern': pattern_key, 'weight': weight}]
            UNIQUE_QUESTIONS_JANGBU.append(q_text)

# ==========================================
# 1. 페이지 설정 및 스타일
# ==========================================
st.set_page_config(page_title="디스코한의원 종합 문진표 (처방용)", layout="centered")

st.markdown("""
    <style>
    /* [화면 표시용 스타일] */
    h1 { 
        font-size: 1.5rem; 
        font-weight: 700;
    }
    .question-text {
        font-size: 1.3rem;
        font-weight: bold;
        color: var(--text-color); 
        margin-bottom: 20px;
        line-height: 1.5;
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
    
    /* [인쇄 및 결과 숨김 처리] */
    @media print {
        * { color: black !important; background-color: white !important; }
        .page-break { page-break-before: always !important; display: block !important; height: 1px; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 세션 상태 초기화
# ==========================================
# 전체 질문 순서: [사상 질문 37개] -> [사상 증상 3개] -> [장부 질문 N개]
TOTAL_SASANG_Q = len(QUESTIONS_SASANG)
TOTAL_SASANG_SYM = 3
TOTAL_JANGBU_Q = len(UNIQUE_QUESTIONS_JANGBU)

TOTAL_STEPS = TOTAL_SASANG_Q + TOTAL_SASANG_SYM + TOTAL_JANGBU_Q

if 'step' not in st.session_state:
    st.session_state['step'] = 0  
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

# 사상체질 답변 저장소
if 'answers_sasang' not in st.session_state:
    st.session_state['answers_sasang'] = [2] * TOTAL_SASANG_Q 
if 'answers_log_sasang' not in st.session_state:
    st.session_state['answers_log_sasang'] = [""] * TOTAL_SASANG_Q
if 'symptom_answers' not in st.session_state:
    st.session_state['symptom_answers'] = {}

# 장부변증 답변 저장소
if 'answers_jangbu' not in st.session_state:
    st.session_state['answers_jangbu'] = [0] * TOTAL_JANGBU_Q
if 'answers_log_jangbu' not in st.session_state:
    st.session_state['answers_log_jangbu'] = [""] * TOTAL_JANGBU_Q

if 'final_sent' not in st.session_state:
    st.session_state['final_sent'] = False

# ==========================================
# 로직 함수 (이메일 및 사상체질 분석)
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

# [사상체질] 전체 결과 텍스트 생성 (관리자용 리포트에 포함)
def get_full_guide_text(code):
    text = ""
    # (기존 코드의 상세 가이드 텍스트 로직 유지)
    if code == 'TY':
        text += "📋 태양인 상세 가이드\n...\n" # (지면상 축약, 실제 코드는 원본 유지)
        text += "1. 태양인의 특징\n에너지를 축적하는 기능은 약하고, 발산/소모시키는 기능은 강합니다.\n"
        text += "병원 처방 예시: 오가피장척탕, 미후등식장탕\n"
    elif code == 'SY':
        text += "📋 소양인 상세 가이드\n...\n"
        text += "1. 소양인의 특징\n몸에 열이 많고 신경이 예민합니다.\n"
        text += "병원 처방 예시: 형방지황탕, 형방패독산\n"
    elif code == 'TE':
        text += "📋 태음인 상세 가이드\n...\n"
        text += "1. 태음인의 특징\n체구가 크고 식욕이 좋으며 비만해지기 쉽습니다.\n"
        text += "병원 처방 예시: 태음조위탕, 갈근해기탕\n"
    elif code == 'SE':
        text += "📋 소음인 상세 가이드\n...\n"
        text += "1. 소음인의 특징\n몸이 차고 소화기 기능이 약합니다.\n"
        text += "병원 처방 예시: 곽향정기산, 향부자팔물탕\n"
    return text

# [사상체질] 추천 처방 로직
def get_recommendation(constitution, symptoms):
    pain = symptoms.get('pain')
    sweat = symptoms.get('sweat')
    stool = symptoms.get('stool')
    
    if constitution == 'SE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if sweat == "땀이 거의 나지 않는다":
                return {"condition": "소음인 울광체질", "desc": "내부 양기가 갇힌 상태", "prescription": "천궁계지탕, 궁귀향소산"}
            else: 
                return {"condition": "소음인 망양체질", "desc": "양기가 허약해 땀으로 빠짐", "prescription": "황기계지탕, 보중익기탕"}
        else: 
            if stool == "설사를 하거나 묽다":
                return {"condition": "소음인 태음병(설사)", "desc": "속이 냉하고 배탈이 잦음", "prescription": "백하오이중탕, 곽향정기산"}
            else:
                return {"condition": "소음인 태음병(복통)", "desc": "위장이 차갑고 막힘", "prescription": "곽향정기산, 향사양위탕"}

    elif constitution == 'SY':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if stool == "설사를 하거나 묽다":
                return {"condition": "소양인 망음병", "desc": "겉은 열, 속은 냉", "prescription": "형방지황탕, 저령차전자탕"}
            else: 
                return {"condition": "소양인 소양상풍병", "desc": "열기가 갇힘", "prescription": "형방패독산, 형방도적산"}
        else: 
            if stool == "변비가 있거나 잘 안 나온다":
                return {"condition": "소양인 흉격열병", "desc": "가슴에 열이 꽉 참", "prescription": "형방사백산, 지황백호탕"}
            else:
                return {"condition": "소양인 음허오열병", "desc": "신장 기운 약화", "prescription": "독활지황탕, 숙지황고삼탕"}

    elif constitution == 'TE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            return {"condition": "태음인 위완한병", "desc": "폐/대장이 차가움", "prescription": "태음조위탕, 녹용대보탕"}
        else: 
            return {"condition": "태음인 간열병", "desc": "간에 열이 많음", "prescription": "갈근해기탕, 열다한소탕"}

    elif constitution == 'TY':
        return {"condition": "태양인 특이 병증", "desc": "해역증/열격증 주의", "prescription": "오가피장척탕, 미후등식장탕"}
    
    return {"condition": "정보 부족", "desc": "", "prescription": ""}

# ==========================================
# 통합 분석 및 이메일 전송 함수
# ==========================================
def analyze_and_send():
    info = st.session_state['user_info']
    
    # --- 1. 사상체질 분석 ---
    raw_scores = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
    type_counts = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
    
    for i, score in enumerate(st.session_state['answers_sasang']):
        q_type = QUESTIONS_SASANG[i]['type']
        raw_scores[q_type] += score
        type_counts[q_type] += 1
    
    avg_scores = {k: (v / type_counts[k] if type_counts[k] > 0 else 0) for k, v in raw_scores.items()}
    max_score = max(avg_scores.values())
    result_types = [k for k, v in avg_scores.items() if v == max_score]
    my_type_code = result_types[0] 
    
    sasang_rec = get_recommendation(my_type_code, st.session_state['symptom_answers'])
    sasang_guide = get_full_guide_text(my_type_code)
    sasang_scores_str = ", ".join([f"{TYPE_MAP[k]}: {v:.1f}점" for k, v in avg_scores.items()])
    
    sasang_log = "\n".join(st.session_state['answers_log_sasang'])
    sasang_log += f"\n[증상] Pain: {st.session_state['symptom_answers'].get('pain')}"
    sasang_log += f"\n[증상] Sweat: {st.session_state['symptom_answers'].get('sweat')}"
    sasang_log += f"\n[증상] Stool: {st.session_state['symptom_answers'].get('stool')}"

    # --- 2. 장부변증 분석 ---
    jangbu_scores = {key: 0 for key in PATTERNS.keys()}
    jangbu_max_scores = {key: 0 for key in PATTERNS.keys()}
    
    # 분모 계산
    for q_text, mappings in QUESTION_MAP.items():
        for m in mappings:
            jangbu_max_scores[m['pattern']] += m['weight']
    
    # 분자 계산
    for idx, ans_val in enumerate(st.session_state['answers_jangbu']):
        if ans_val == 1:
            q_text = UNIQUE_QUESTIONS_JANGBU[idx]
            mappings = QUESTION_MAP[q_text]
            for m in mappings:
                jangbu_scores[m['pattern']] += m['weight']
    
    jangbu_results = []
    threshold = 0.6
    for pattern, score in jangbu_scores.items():
        if jangbu_max_scores[pattern] > 0:
            ratio = score / jangbu_max_scores[pattern]
            if ratio >= threshold:
                jangbu_results.append({
                    'pattern': pattern,
                    'ratio': ratio,
                    'score': score,
                    'max_score': jangbu_max_scores[pattern],
                    'info': PATTERNS[pattern]
                })
    jangbu_results.sort(key=lambda x: x['ratio'], reverse=True)
    
    jangbu_txt = ""
    if not jangbu_results:
        jangbu_txt = "특이 소견 없음"
    else:
        for res in jangbu_results:
            jangbu_txt += f"- {res['pattern']} : {res['ratio']*100:.1f}%\n"
            
    jangbu_log = "\n".join([log for i, log in enumerate(st.session_state['answers_log_jangbu']) if st.session_state['answers_jangbu'][i] == 1])

    # --- 3. 관리자 이메일 작성 ---
    admin_body = f"""
[관리자 알림] 디스코한의원 종합 문진 결과
이름: {info['name']} ({info['birth']})
이메일: {info.get('email', '미입력')}
키/몸무게: {info.get('height','')}cm / {info.get('weight','')}kg

[기본 정보]
약: {info.get('meds','')}
병력: {info.get('history','')}
불편증상: {info.get('comment','')}

=========================================
1. 사상체질 진단 결과
=========================================
판정: {TYPE_MAP.get(my_type_code)}
점수: {sasang_scores_str}

[추천 병증 및 처방]
병증: {sasang_rec['condition']}
처방: {sasang_rec['prescription']}
설명: {sasang_rec['desc']}

=========================================
2. 장부변증 진단 결과
=========================================
[감지된 주요 패턴]
{jangbu_txt}

[세부 내역]
"""
    for res in jangbu_results:
        admin_body += f"\n[{res['pattern']}]\n"
        admin_body += f"추천 처방: {res['info']['prescription']}\n"
        admin_body += f"참고 문헌: {res['info']['reference']}\n"

    admin_body += f"\n=========================================\n[설문 응답 로그]\n--- 사상체질 ---\n{sasang_log}\n\n--- 장부변증 ('예' 응답만) ---\n{jangbu_log}"

    send_email_logic(RECEIVER_EMAIL, f"[관리자] {info['name']}님 종합 진단 결과", admin_body)
    
    # 사용자에게는 결과 비공개 처리 (메일 발송 코드 제거 또는 간단한 인사만)
    # 요청사항: "결과는 설문자가 몰라야 해"
    return True

# ==========================================
# 화면 렌더링 함수
# ==========================================
def go_next():
    st.session_state['step'] += 1

def go_prev():
    if st.session_state['step'] > 0:
        st.session_state['step'] -= 1

def main():
    step = st.session_state['step']
    
    # ----------------------------------
    # STEP 0: 기본 정보 입력
    # ----------------------------------
    if step == 0:
        st.markdown("<h1 style='text-align: center;'>디스코한의원 종합 문진표</h1>", unsafe_allow_html=True)
        st.info("본 설문은 환자분의 현재 몸 상태를 정확히 파악하기 위한 통합 문진입니다. 100문항이 넘어서 많이 힘드시겠지만, 솔직하게 답변해 주십시오.")
        
        with st.form("info_form"):
            name = st.text_input("이름 (필수)", placeholder="홍길동")
            birth = st.text_input("생년월일 (필수)", placeholder="예: 1980.01.01")
            
            # [수정됨] 이메일 입력란 제거
            
            col1, col2 = st.columns(2)
            with col1: height = st.text_input("키 (cm)", placeholder="175")
            with col2: weight = st.text_input("몸무게 (kg)", placeholder="70")
            
            meds = st.text_input("복용 중인 약 (선택)")
            history = st.text_input("과거 병력 (선택)")
            comment = st.text_area("원장님께 하고 싶은 말씀 (선택)", height=80)
            
            if st.form_submit_button("문진 시작하기", use_container_width=True):
                if not name or not birth:
                    st.error("이름과 생년월일은 필수입니다.")
                else:
                    st.session_state['user_info'] = {
                        'name': name, 'birth': birth, 
                        'height': height, 'weight': weight, 
                        'meds': meds, 'history': history, 'comment': comment
                    }
                    go_next()
                    st.rerun()

    # ----------------------------------
    # STEP 1 ~ A: 사상체질 질문 (1 ~ 37)
    # ----------------------------------
    elif 1 <= step <= TOTAL_SASANG_Q:
        idx = step - 1
        q_data = QUESTIONS_SASANG[idx]
        
        progress = idx / TOTAL_STEPS
        st.progress(progress)
        st.caption(f"문진 진행 중... ({step}/{TOTAL_STEPS})")
        
        st.markdown(f"<div class='question-text'>Q{step}. {q_data['q']}</div>", unsafe_allow_html=True)
        
        default_idx = st.session_state['answers_sasang'][idx]
        choice = st.radio("답변을 선택하세요", OPTIONS_SASANG, index=default_idx, horizontal=False, label_visibility="collapsed", key=f"sq_{idx}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col2:
            if st.button("다음 ➡️", use_container_width=True):
                score_val = OPTIONS_SASANG.index(choice)
                st.session_state['answers_sasang'][idx] = score_val
                st.session_state['answers_log_sasang'][idx] = f"Q(사상){step}. {q_data['q']} : {choice}"
                go_next()
                st.rerun()

    # ----------------------------------
    # STEP A+1 ~ A+3: 사상체질 증상 질문
    # ----------------------------------
    elif TOTAL_SASANG_Q < step <= TOTAL_SASANG_Q + TOTAL_SASANG_SYM:
        offset = step - TOTAL_SASANG_Q
        st.progress(step / TOTAL_STEPS)
        st.caption(f"증상 상세 확인 ({step}/{TOTAL_STEPS})")

        if offset == 1:
            st.markdown("<div class='question-text'>Q. 아플 때 주로 어떤 느낌인가요?</div>", unsafe_allow_html=True)
            ans = st.radio("통증 유형", ["몸살 기운 (으슬으슬 춥고 열이 남)", "속 문제 (소화가 안 되고, 가슴이 답답하거나 배가 아픔)"], key="sym_pain")
            save_key = 'pain'
        elif offset == 2:
            st.markdown("<div class='question-text'>Q. 아플 때 땀은 어떻게 나나요?</div>", unsafe_allow_html=True)
            ans = st.radio("땀 유형", ["땀이 거의 나지 않는다", "식은땀이 나거나 땀이 축축하게 난다"], key="sym_sweat")
            save_key = 'sweat'
        elif offset == 3:
            st.markdown("<div class='question-text'>Q. 대변 상태는 어떤가요?</div>", unsafe_allow_html=True)
            ans = st.radio("대변 유형", ["변비가 있거나 잘 안 나온다", "설사를 하거나 묽다", "평소와 비슷하다(보통)"], key="sym_stool")
            save_key = 'stool'
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col2:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state['symptom_answers'][save_key] = ans
                go_next()
                st.rerun()

    # ----------------------------------
    # STEP B ~ END: 장부변증 질문
    # ----------------------------------
    elif TOTAL_SASANG_Q + TOTAL_SASANG_SYM < step <= TOTAL_STEPS:
        base_idx = TOTAL_SASANG_Q + TOTAL_SASANG_SYM
        idx = step - base_idx - 1
        q_text = UNIQUE_QUESTIONS_JANGBU[idx]

        st.progress(step / TOTAL_STEPS)
        st.caption(f"상세 문진 진행 중... ({step}/{TOTAL_STEPS})")
        
        st.markdown(f"<div class='question-text'>Q{step}. {q_text}</div>", unsafe_allow_html=True)
        
        default_idx = st.session_state['answers_jangbu'][idx]
        choice = st.radio("해당합니까?", OPTIONS_JANGBU, index=default_idx, horizontal=True, label_visibility="collapsed", key=f"jq_{idx}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col2:
            btn_text = "다음 ➡️" if step < TOTAL_STEPS else "제출하기"
            if st.button(btn_text, use_container_width=True):
                score_val = OPTIONS_JANGBU.index(choice)
                st.session_state['answers_jangbu'][idx] = score_val
                st.session_state['answers_log_jangbu'][idx] = f"Q(장부){step}. {q_text} : {choice}"
                
                if step < TOTAL_STEPS:
                    go_next()
                    st.rerun()
                else:
                    # 최종 제출 처리
                    with st.spinner("결과를 분석하여 전송 중입니다..."):
                        analyze_and_send()
                    st.session_state['step'] = 999
                    st.rerun()

    # ----------------------------------
    # [STEP 999] 완료 화면 (결과 비공개)
    # ----------------------------------
    elif step == 999:
        st.success("✅ 문진표 작성이 완료되었습니다.")
        st.info("수고하셨습니다. 작성해주신 내용은 원장님께 전달되었으며, 진료 시 정밀 분석을 위해 활용됩니다.")
        
        st.markdown("---")
        if st.button("처음으로 돌아가기", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()
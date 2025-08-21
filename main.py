import streamlit as st 
import os
import google.generativeai as genai
from dotenv import load_dotenv
import html
import re
import subprocess
import platform
from pathlib import Path
from config import GOOGLE_API_KEY, AMAZON_Q_PATH, DIAGRAM_SETTINGS
# =========================================
# 1. 세션 상태 초기화
# =========================================
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True

# =========================================
# 2. 랜딩 화면
# =========================================
if st.session_state.show_landing:
    st.markdown("""
        <style>
        .landing-img {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            cursor: pointer;
            z-index: 9999;
        }
        </style>
        <a href="?start=1">
            <img src="https://i.postimg.cc/gcQ8jXNc/Group-Project-1.png" class="landing-img">
        </a>
    """, unsafe_allow_html=True)

    # 클릭 감지
    if st.query_params.get("start"):
        st.session_state.show_landing = False
        st.query_params = {}  # 클릭 후 URL 초기화
        st.rerun()  # Streamlit 최신 버전용

    st.stop()  # 랜딩 화면이면 여기서 종료

# =========================================
# 환경 변수 로드
# =========================================
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# =========================================
# 체크리스트 관리 함수
# =========================================
def get_checked_security_items():
    """체크리스트에서 체크된 보안 항목들을 수집합니다."""
    checked_items = []
    
    # 기본 보안 체크리스트
    basic_checklist = [
        "VPC 적용 여부",
        "퍼블릭,프라이빗 서브넷 분리", 
        "보안 그룹 설정",
        "IAM 권한 최소화",
        "데이터 암호화",
        "로드밸런서 설정",
        "WAF 설정",
        "CloudFront 설정",
        "CloudTrail 설정",
        "CloudWatch 설정",
        "CloudWatch 로그 설정",
    ]
    
    for item in basic_checklist:
        if st.session_state.get(f"basic_{item}", False):
            checked_items.append(item)
    

    
    return checked_items

def format_security_requirements(checked_items):
    """체크된 보안 항목들을 Amazon Q 프롬프트 형식으로 변환합니다."""
    if not checked_items:
        return ""
    
    security_text = "\n\n보안 요구사항:\n"
    security_text += "다음 보안 요소들을 반드시 다이어그램에 포함하고 '*'별표 라벨을 앞뒤로 하여여 명확하게 구분해주세요:\n"
    
    for i, item in enumerate(checked_items, 1):
        # 예시 부분 제거하고 핵심 내용만 추출
        clean_item = item.split(" (예:")[0] if " (예:" in item else item
        security_text += f"{i}. {clean_item}\n"
    
    
    return security_text

# =========================================
# Amazon Q CLI 클라이언트 클래스
# =========================================
class AmazonQClient:
    """Amazon Q CLI 클라이언트"""
    
    def __init__(self):
        self.platform = platform.system()
    
    def generate_diagram_prompt(self, tree_structure, security_requirements=""):
        """트리 구조와 보안 요구사항을 기반으로 다이어그램 생성 프롬프트 생성"""
        
        return f"""AWS 클라우드 아키텍처 다이어그램을 생성해주세요.

아키텍처 구조:
{tree_structure}{security_requirements}

요구사항:
1. AWS 서비스 아이콘을 사용하여 시각적 다이어그램 생성
2. 서비스 간 연결 관계를 명확히 표시
3. generated-diagrams 폴더에 PNG 파일로 저장


다이어그램을 생성하고 저장해주세요."""
    
    def execute_command(self, prompt):
        """플랫폼별 명령어 실행"""
        try:
            if self.platform == "Windows":
                return self._execute_windows(prompt)
            else:
                return self._execute_unix(prompt)
        except Exception as e:
            st.error(f"Amazon Q CLI 실행 오류: {str(e)}")
            return None
    
    def _execute_windows(self, prompt):
        """Windows에서 명령어 실행"""
        try:
            # WSL이 설치되어 있는지 확인
            wsl_check = subprocess.run(['wsl', '--version'], capture_output=True, text=True)
            if wsl_check.returncode == 0:
                # WSL 사용 - 상대 경로 사용
                home_dir = os.path.expanduser("~")
                local_bin = os.path.join(home_dir, ".local", "bin")
                # WSL에서 현재 디렉토리로 이동 후 명령 실행
                cmd = f'cd . && source ~/.bashrc && export PATH=$PATH:{local_bin} && printf "y\\ny\\ny\\n" | {AMAZON_Q_PATH} chat "{prompt}"'
                
                return subprocess.run([
                    'wsl', '-e', 'bash', '-c', cmd
                ], capture_output=True, text=True, timeout=DIAGRAM_SETTINGS['timeout'], encoding=DIAGRAM_SETTINGS['encoding'])
            else:
                # WSL이 없으면 직접 실행 시도
                cmd = f'{AMAZON_Q_PATH} chat "{prompt}"'
                return subprocess.run([
                    'cmd', '/c', cmd
                ], capture_output=True, text=True, timeout=DIAGRAM_SETTINGS['timeout'], encoding=DIAGRAM_SETTINGS['encoding'])
                
        except FileNotFoundError:
            # WSL 명령어를 찾을 수 없으면 직접 실행
            cmd = f'{AMAZON_Q_PATH} chat "{prompt}"'
            return subprocess.run([
                'cmd', '/c', cmd
            ], capture_output=True, text=True, timeout=DIAGRAM_SETTINGS['timeout'], encoding=DIAGRAM_SETTINGS['encoding'])
    
    def _execute_unix(self, prompt):
        """Linux/Mac에서 명령어 실행"""
        home_dir = os.path.expanduser("~")
        local_bin = os.path.join(home_dir, ".local", "bin")
        cmd = f'source ~/.bashrc && export PATH=$PATH:{local_bin} && printf "y\\ny\\ny\\n" | {AMAZON_Q_PATH} chat "{prompt}"'
        
        return subprocess.run([
            'bash', '-c', cmd
        ], capture_output=True, text=True, timeout=DIAGRAM_SETTINGS['timeout'], encoding=DIAGRAM_SETTINGS['encoding'])
    
    def generate_diagram(self, tree_structure):
        """Amazon Q CLI를 통해 다이어그램 생성 요청"""
        try:
            # Amazon Q CLI 경로 확인
            st.info(f"🔧 Amazon Q CLI 경로: {AMAZON_Q_PATH}")
            
            checked_items = get_checked_security_items()
            security_requirements_text = format_security_requirements(checked_items)
            
            # 보안 요구사항이 있을 때만 프롬프트에 추가
            if security_requirements_text:
                prompt = self.generate_diagram_prompt(tree_structure, security_requirements_text)
            else:
                prompt = self.generate_diagram_prompt(tree_structure, "")
            
            # 디버깅을 위해 프롬프트 출력
            st.info("🔍 생성된 프롬프트:")
            st.code(prompt, language="text")
                
            result = self.execute_command(prompt)
            
            if result and result.returncode == 0:
                st.success("✅ Amazon Q CLI 실행 성공")
                return result.stdout or ""
            else:
                if result:
                    st.error(f"❌ Amazon Q CLI 오류 (코드: {result.returncode})")
                    st.error(f"오류 메시지: {result.stderr}")
                    st.info(f"출력: {result.stdout}")
                else:
                    st.error("❌ Amazon Q CLI 실행 결과가 없습니다")
                return None
                
        except Exception as e:
            st.error(f"Amazon Q CLI 실행 오류: {str(e)}")
            return None

# =========================================
# 다이어그램 관리 클래스
# =========================================
class DiagramManager:
    """다이어그램 파일 관리"""
    
    def __init__(self):
        # generated-diagrams 폴더 사용
        self.diagram_folder = Path('generated-diagrams')
        self.diagram_folder.mkdir(parents=True, exist_ok=True)
    
    def find_latest_diagram(self):
        """최신 다이어그램 파일 찾기"""
        png_files = list(self.diagram_folder.glob('*.png'))
        if png_files:
            latest_file = max(png_files, key=lambda x: x.stat().st_mtime)
            return latest_file
        return None
    
    def get_folder_contents(self):
        """다이어그램 폴더 내용 반환"""
        if self.diagram_folder.exists():
            return [f.name for f in self.diagram_folder.glob('*')]
        return []

# =========================================
# Gemini API 초기화
# =========================================
def initialize_gemini():
    """Gemini API 초기화"""
    try:
        if not GOOGLE_API_KEY:
            return False, None
        
        # Gemini API 설정
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # 모델 초기화 (최신 모델명 사용)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        return True, model
        
    except Exception as e:
        st.error(f"Gemini API 초기화 실패: {str(e)}")
        return False, None

# API 초기화 실행
api_ready, model = initialize_gemini()

# Amazon Q 클라이언트 초기화
amazon_q_client = AmazonQClient()

# 다이어그램 매니저 초기화
diagram_manager = DiagramManager()

# =========================================
# 트리 구조 추출 함수
# =========================================
def extract_tree_structure(text):
    """텍스트에서 트리 구조를 추출합니다."""
    # 트리 구조 패턴들
    tree_patterns = [
        r'```tree\s*\n(.*?)\n```',  # ```tree ... ``` 형태
        r'```\s*\n(.*?)\n```',      # ``` ... ``` 형태
        r'^\s*[├└│─]+.*$',          # 트리 문자로 시작하는 줄들
        r'^\s*[┌└├│─]+.*$',          # 다른 트리 문자들
        r'^\s*[│├└─]+.*$',           # 기본 트리 문자들
    ]
    
    for pattern in tree_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # 트리 구조가 없으면 전체 텍스트 반환
    return text

# =========================================
# 챗봇 응답 생성 함수
# =========================================
def generate_chatbot_response(user_message):
    """사용자 메시지에 대한 챗봇 응답을 생성합니다."""
    if not api_ready or not model:
        return "❌ API가 준비되지 않았습니다. GEMINI_API_KEY를 확인해주세요."
    
    try:
        # 기존 트리 아키텍처 컨텍스트 가져오기
        existing_tree = ss.get("current_tree", "")
        context_info = ""
        
        if existing_tree:
            context_info = f"""

기존 아키텍처 구조 (참고용):
{existing_tree}

위 구조를 기반으로 사용자의 새로운 요청을 처리해주세요. 
기존 구조와 일관성을 유지하면서 요청사항을 반영하거나 확장하세요.
"""
        
        # 클라우드 아키텍처 설계를 위한 프롬프트
        enhanced_prompt = f"""
사용자 요청: {user_message}

AWS 클라우드 아키텍처 전문가로서 답변해주세요. {context_info}

요청사항:
1. 사용자의 요청에 맞는 클라우드 아키텍처를 설계해주세요
2. 반드시 트리 구조로 표현해주세요 (예: ├─, │, └─ 문자 사용)
3. 트리구조는 응답에 1회만 표시해주세요
4. 각 컴포넌트의 역할과 연결 관계를 명확히 표시해주세요
5. 필요시 사용자에게 다시 질문하여 명확하게 하세요
6. 사용자의 요청 이외의 구성요소는 트리에 표시하지 마세요

중요 규칙:
- 모든 AWS 서비스와 리소스는 반드시 공식 영어 명칭을 사용하세요
- 예: EC2, S3, RDS, VPC, IAM, CloudFront, Lambda, ECS, EKS 등
- 한국어 설명은 가능하지만, 서비스명은 영어로 표기하세요
- 트리 구조에서 각 노드는 AWS 공식 서비스명을 사용하세요
- 기존 아키텍처가 있다면 일관성을 유지하면서 요청사항을 반영하세요

"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text if response.text else "죄송합니다. 응답을 생성할 수 없습니다."
        
    except Exception as e:
        return f"❌ 오류가 발생했습니다: {str(e)}"

# =========================================
# 트리 구조 추출 및 저장 함수
# =========================================
def update_tree_structure(bot_response):
    """봇 응답에서 트리 구조를 추출하고 저장합니다."""
    tree_structure = extract_tree_structure(bot_response)
    if tree_structure:
        ss["current_tree"] = tree_structure
        return True
    return False

# =========================================
# 트리 구조 초기화 함수
# =========================================
def clear_tree_structure():
    """트리 구조를 초기화합니다."""
    ss["current_tree"] = ""
    st.success("트리 구조가 초기화되었습니다!")

# =========================================
# 보안 분석 함수
# =========================================
def analyze_security_architecture(tree_structure, checked_items):
    """현재 아키텍처의 보안 구성요소를 분석하고 추가 권장사항을 제공합니다."""
    if not api_ready or not model:
        return "❌ Gemini API가 준비되지 않았습니다."
    
    try:
        # 체크된 보안 항목들을 텍스트로 변환
        security_items_text = ""
        if checked_items:
            security_items_text = "\n\n현재 적용된 보안 요소들:\n"
            for i, item in enumerate(checked_items, 1):
                security_items_text += f"{i}. {item}\n"
        else:
            security_items_text = "\n\n현재 적용된 보안 요소: 없음"
        
        # Gemini에게 보안 분석 요청
        prompt = f"""
다음 AWS 클라우드 아키텍처의 보안 구성요소를 분석해주세요:

아키텍처 구조:
{tree_structure}{security_items_text}

분석 요청사항:
1. 현재 아키텍처에서 각 보안 구성요소가 어떤 역할을 하는지 설명
2. 현재 구성에서 보안 취약점이나 개선점이 있는지 분석
3. 추가로 구성하면 좋을 보안 요소들을 제안
4. 각 보안 요소의 중요도와 우선순위를 평가

응답 형식:
- 현재 보안 구성요소 분석
- 보안 취약점 및 개선점
- 추가 권장 보안 요소
- 보안 강화 우선순위

AWS 보안 모범사례를 기준으로 전문적이고 실용적인 조언을 제공해주세요.
"""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "보안 분석을 완료할 수 없습니다."
        
    except Exception as e:
        return f"❌ 보안 분석 중 오류가 발생했습니다: {str(e)}"

# =========================================
# 다이어그램 생성 함수
# =========================================
def create_diagram_from_tree():
    """현재 트리 구조를 기반으로 Amazon Q를 통해 다이어그램 생성"""
    current_tree = ss.get("current_tree", "")
    
    if not current_tree:
        st.warning("⚠️ 다이어그램을 생성할 트리 구조가 없습니다. 먼저 아키텍처를 설계해주세요.")
        return
    
    # 체크된 보안 항목들 수집
    checked_items = get_checked_security_items()
    
    # 체크된 보안 항목들 표시
    if checked_items:
        st.info("🔒 적용할 보안 요소들:")
        for i, item in enumerate(checked_items, 1):
            clean_item = item.split(" (예:")[0] if " (예:" in item else item
            st.write(f"{i}. {clean_item}")
    else:
        st.info("ℹ️ 체크된 보안 항목이 없습니다. 기본 보안 설정으로 다이어그램을 생성합니다.")
    
    try:
        # 1. Amazon Q를 통한 다이어그램 생성
        with st.spinner("🎨 Amazon Q를 통해 다이어그램을 생성하고 있습니다..."):
            result = amazon_q_client.generate_diagram(current_tree)
            
            if result:
                st.success("✅ 다이어그램 생성 요청이 완료되었습니다!")
                st.info("📝 Amazon Q 응답:")
                st.code(result, language="text")
                
                # 생성된 다이어그램 파일 확인
                latest_diagram = diagram_manager.find_latest_diagram()
                if latest_diagram:
                    st.success(f"🎉 다이어그램 파일이 생성되었습니다: {latest_diagram.name}")
                    # 다이어그램을 세션 상태에 저장
                    ss["current_diagram"] = str(latest_diagram)
                    # 다이어그램 생성 완료 플래그 설정
                    ss["diagram_created"] = True
                else:
                    st.info("📁 다이어그램 파일을 확인 중입니다...")
                    
            else:
                st.error("❌ 다이어그램 생성에 실패했습니다.")
        
        # 2. Gemini를 통한 보안 분석
        with st.spinner("🔍 보안 아키텍처를 분석하고 있습니다..."):
            security_analysis = analyze_security_architecture(current_tree, checked_items)
            # 보안 분석 결과를 세션 상태에 저장
            ss["security_analysis"] = security_analysis
            # 분석 완료 시간 저장
            from datetime import datetime
            ss["analysis_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ 보안 분석이 완료되었습니다!")
        
        # 페이지 새로고침하여 결과 표시
        st.rerun()
                
    except Exception as e:
        st.error(f"❌ 처리 중 오류가 발생했습니다: {str(e)}")

# =========================================
# 다이어그램 표시 함수
# =========================================
def display_diagram():
    """현재 다이어그램을 표시합니다."""
    
    def _encode_image_to_base64(image_path):
        """이미지를 base64로 인코딩합니다."""
        import base64
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except:
            return ""
    
    current_diagram = ss.get("current_diagram", "")
    
    if current_diagram and os.path.exists(current_diagram):
        try:
            # 다이어그램 이미지를 460px 높이의 카드로 감싸서 표시
            # 파일 경로를 상대 경로로 변환
            relative_path = os.path.relpath(current_diagram)
            st.markdown(
                f'''
                <div class="card" style="height:460px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                    <img src="data:image/png;base64,{_encode_image_to_base64(current_diagram)}" 
                         style="max-width: 100%; max-height: 100%; object-fit: contain;" 
                         alt="생성된 아키텍처 다이어그램">
                </div>
                ''',
                unsafe_allow_html=True
            )
                    
        except Exception as e:
            st.error(f"❌ 다이어그램 표시 중 오류가 발생했습니다: {str(e)}")
            # 오류 발생 시 다이어그램 정보 초기화
            ss["current_diagram"] = ""
    else:
        # 다이어그램이 없을 때 기본 메시지 표시
        st.markdown(
            '<div class="card" style="height:460px; display:flex; align-items:center; justify-content:center; color:#888;">'
            '여기에 다이어그램이 표시됩니다.'
            '</div>',
            unsafe_allow_html=True
        )

# =========================================
# 페이지 레이아웃
# =========================================
st.set_page_config(
    page_title="AWS Diagram Generator",
    page_icon="⚡",
    layout="wide"
)

# 메인 타이틀
col1, col2 = st.columns([0.9, 0.1])  # 왼쪽 90%, 오른쪽 10%

with col1:
    st.title("⚡AWS Diagram Generator")

with col2:
    st.image(
        "https://i.postimg.cc/KcBtH7PX/1755745208336.png", 
        width=180  # 기존 50에서 120으로 확대
    )

# =========================================
# CSS: 말풍선 + 카드 + 중간제목 스타일
# =========================================
st.markdown("""
<style>
/* ===============================
   Global Layout / Font
================================= */
body {
    background-color: #fafafa;
    color: #111;
    font-family: 'Segoe UI', Roboto, sans-serif;
    line-height: 1.5;
}

/* ===============================
   Animated Main Title
================================= */
@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

h1 {
    font-weight: 800 !important;
    border-left: 6px solid #f15a24;
    padding-left: 10px;
    margin-bottom: 20px;
    font-size: 48px !important;
    background: linear-gradient(270deg, #f15a24, #ffd700, #1e90ff, #32cd32);
    background-size: 800% 800%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientMove 6s ease infinite;
}

/* ===============================
   Card / Section Titles
================================= */
.card {
    border-radius: 14px;
    padding: 16px;
    background: #ffffff;
    border: 1px solid #f15a24;
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    margin-bottom: 18px;
}

.title {
    font-size: 18px;
    font-weight: 700;
    color: #f15a24;
    height: 36px;       /* 제목 영역 높이 */
    padding-top: 6px;   /* 글자를 아래로 살짝 내림 */
    margin-bottom: 4px; /* 카드와의 간격 */
}

.section-subtitle {
    font-size: 18px;
    font-weight: 600;
    margin: 16px 0 8px 0;
    color: #111;
}

/* ===============================
   Chat Bubble Styles
================================= */
.chat-card {
    border-radius: 15px;
    padding: 15px;
    background: #ffffff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.chat-title {
    font-size: 18px;
    font-weight: 700;
    color: #f15a24;
    border-left: 6px solid #f15a24;
    padding-left: 10px;
    margin-bottom: 16px;
}

.chat-container {
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    background-color: #fafafa;
}

.chat-bubble-wrapper {
    display: flex;
    margin: 8px;
}

.chat-bubble {
    max-width: 60%;
    padding: 10px 15px;
    border-radius: 15px;
    font-size: 15px;
    line-height: 1.4;
    word-wrap: break-word;
    white-space: pre-wrap;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.user-bubble-wrapper {
    justify-content: flex-end;
}

.user-bubble {
    background-color: #FFE0C1;
    color: #111;
    background-image: none;
}

.bot-bubble-wrapper {
    justify-content: flex-start;
}

.bot-bubble {
    background-color: #F1F0F0;
}

.chat-input-spacer {
    height: 20px;
    margin-bottom: 10px;
}

/* ===============================
   Buttons
================================= */
button[kind="secondary"], button[kind="primary"] {
    background-color: #f15a24 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
    transition: background-color 0.2s ease;
}
button[kind="secondary"]:hover, button[kind="primary"]:hover {
    background-color: #d94c1a !important;
}

/* ===============================
   Checkboxes
================================= */
.stCheckbox label {
    color: #111 !important;
    font-weight: 500 !important;
}
.stCheckbox input:checked + div {
    border-color: #f15a24 !important;
}

/* ===============================
   Expanders
================================= */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #111 !important;
}
.streamlit-expanderHeader:hover {
    color: #f15a24 !important;
}

/* ===============================
   Scrollbar Customization
================================= */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #f2f2f2;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb {
    background: #f15a24;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #d94c1a;
}

/* ===============================
   Cloud / Tag Titles
================================= */
.cloud-title {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #f15a24, #ffd700, #1e90ff, #32cd32);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
}
.cloud-title::after {
    content: '';
    flex-grow: 1;
    height: 2px;
    background-color: #f15a24;
    margin-left: 10px;
    border-radius: 2px;
}

/* ===============================
   Tree Display Styles
================================= */
.tree-display {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-x: auto;
}

.tree-controls {
    display: flex;
    gap: 10px;
    margin-top: 15px;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}
</style>
""", unsafe_allow_html=True)

# =========================================
# 세션 상태 초기화
# =========================================
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "안녕하세요! 클라우드 아키텍처 설계를 도와드릴 수 있어요. 예를 들어 '서울 리전에 EC2 두 대 설치' 같은 요청을 주시면, 아키텍처 구조를 트리 형태로 만들어드릴 수 있습니다. 무엇을 도와드릴까요? 😊"}
    ]

if "current_tree" not in st.session_state:
    st.session_state["current_tree"] = ""

if "current_diagram" not in st.session_state:
    st.session_state["current_diagram"] = ""

if "diagram_created" not in st.session_state:
    st.session_state["diagram_created"] = False

if "security_analysis" not in st.session_state:
    st.session_state["security_analysis"] = ""

if "board_suggestions" not in st.session_state:
    st.session_state["board_suggestions"] = ""

ss = st.session_state

# =========================================
# 클라우드 아키텍처 다이어그램
# =========================================
st.markdown('<div class="cloud-title">☁️ Cloud Architecture Diagrams</div>', unsafe_allow_html=True)

colA, colB = st.columns(2, gap="large")
with colA:
    # 제목(왼쪽) + 제작하기 버튼(오른쪽)을 한 줄에 배치
    _title_col, _btn_col = st.columns([0.8, 0.2])
    with _title_col:
        st.markdown('<div class="title">🌳 아키텍처 트리 구조</div>', unsafe_allow_html=True)
    with _btn_col:
        if st.button("제작하기", key="create_diagram_button", use_container_width=True):
            create_diagram_from_tree()
    
    # 트리 구조 표시 영역
    tree_placeholder = st.empty()
    with tree_placeholder.container():
        if ss.get("current_tree"):
            st.markdown(
                f'<div class="card" style="height:460px; overflow-y:auto; white-space:pre-wrap; color:#000; padding:15px; font-family: monospace; font-size:14px; line-height:1.6;">{ss["current_tree"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="card" style="height:460px; display:flex; align-items:center; justify-content:center; color:#888;">'
                '여기에 아키텍처 트리 구조가 표시됩니다.' 
                '</div>',
                unsafe_allow_html=True
            )

with colB:
    # 제목(왼쪽) + 다운로드 버튼(오른쪽)을 한 줄에 배치
    _title_col, _btn_col = st.columns([0.8, 0.2])
    with _title_col:
        st.markdown('<div class="title">🔐 보안 적용 다이어그램</div>', unsafe_allow_html=True)
    with _btn_col:
        if ss.get("current_diagram") and os.path.exists(ss.get("current_diagram", "")):
            # 다이어그램 파일이 있을 때만 다운로드 버튼 표시
            with open(ss["current_diagram"], "rb") as file:
                st.download_button(
                    label="다운로드",
                    data=file.read(),
                    file_name=os.path.basename(ss["current_diagram"]),
                    mime="image/png",
                    use_container_width=True
                )
        else:
            # 다이어그램이 없을 때는 비활성화된 버튼 표시
            st.button("다운로드", disabled=True, use_container_width=True)
    
    # 보안 적용 다이어그램 표시 영역
    secure_placeholder = st.empty()
    with secure_placeholder.container():
        display_diagram()

# 체크 리스트와 보안 요소 설명서를 한 줄에 배치
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.expander("✅ 체크리스트", expanded=False):
        # 기존 기본 체크리스트
        st.markdown("**🔒 기본 보안 체크리스트**")
        basic_checklist = [
            "VPC 적용 여부",
            "퍼블릭,프라이빗 서브넷 분리", 
            "보안 그룹 설정",
            "IAM 권한 최소화",
            "데이터 암호화",
            "로드밸런서 설정",
            "WAF 설정",
            "CloudFront 설정",
            "CloudTrail 설정",
            "CloudWatch 설정",
            "CloudWatch 로그 설정",
        ]
        for item in basic_checklist:
            st.checkbox(item, key=f"basic_{item}")
        


with col2:
    with st.expander("✨ 보안 요소 설명서", expanded=False):
        # 보안 분석 결과가 있으면 표시
        if ss.get("security_analysis"):
            st.markdown("**🔍 보안 아키텍처 분석 결과**")
            st.markdown(ss["security_analysis"])
            st.markdown("---")
            
            # 마크다운 다운로드 버튼
            markdown_content = f"""# AWS 보안 아키텍처 분석 보고서

## 현재 아키텍처 구조
```
{ss.get("current_tree", "아키텍처 구조가 없습니다.")}
```

## 보안 분석 결과
{ss["security_analysis"]}

## 생성일시
{st.session_state.get("analysis_timestamp", "알 수 없음")}
"""
            
            st.download_button(
                label="📄 마크다운 다운로드",
                data=markdown_content,
                file_name="aws_security_analysis.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        else:
            st.info("🔍 보안 분석 결과가 없습니다. '제작하기' 버튼을 클릭하여 분석을 시작하세요.")

# 챗봇 영역
st.markdown('<div class="chat-title">🧠 클라우드 설계 어시스턴트</div>', unsafe_allow_html=True)
with st.expander("아키텍처 자동 응답기", expanded=True):
    # 챗봇 상태 표시 (에러일 때만 표시)
    if not api_ready:
        st.error("❌ Gemini API가 준비되지 않았습니다.")
        st.info("📝 .env 파일에 GEMINI_API_KEY=your_api_key_here 를 추가하세요.")
    
    # 챗봇 내용 렌더링
    chat_html = '<div class="chat-container">'
    for chat in ss["messages"]:
        role = chat["role"]
        content = chat["content"]
        if role == "user":
            chat_html += f"<div class='chat-bubble-wrapper user-bubble-wrapper'><div class='chat-bubble user-bubble'>{html.escape(content)}</div></div>"
        else:
            chat_html += f"<div class='chat-bubble-wrapper bot-bubble-wrapper'><div class='chat-bubble bot-bubble'>{html.escape(content)}</div></div>"
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
    st.markdown('<div class="chat-input-spacer"></div>', unsafe_allow_html=True)

    # 입력창
    prompt = st.chat_input("자연어 입력")
    if prompt and api_ready:
        # 사용자 메시지 추가
        ss["messages"].append({"role": "user", "content": prompt})
        
        # 챗봇 응답 생성
        with st.spinner("🤔 아키텍처 설계 중..."):
            bot_response = generate_chatbot_response(prompt)
            ss["messages"].append({"role": "assistant", "content": bot_response})
            
            # 트리 구조 추출 및 저장
            update_tree_structure(bot_response)
        
        # 페이지 새로고침
        st.rerun()
    elif prompt and not api_ready:
        st.error("API가 준비되지 않았습니다. 환경변수를 확인해주세요.")


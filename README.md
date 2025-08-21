# GITHUB
https://github.com/yujun9021/AWS_Diagram_Generator

# AWS Diagram Generator

AWS 클라우드 아키텍처 다이어그램을 자동으로 생성하는 Streamlit 애플리케이션입니다.

## 🚀 설치 및 실행

### 1. 필수 요구사항

- Windows 10/11
- WSL (Windows Subsystem for Linux)
- Python 3.8 이상
- Git

### 2. Amazon Q CLI 설치 (WSL에서 실행)

**WSL 터미널을 열고 다음 명령어를 실행하세요:**

```bash
# 1. WSL 터미널 열기
# Windows 시작 메뉴에서 "Ubuntu" 검색 후 실행
# 또는 PowerShell에서 'wsl' 입력

# 2. 프로젝트 디렉토리로 이동
cd /mnt/c/"YOUR PROJECT DIRECTORY"

# 3. Amazon Q 설치 스크립트 실행
chmod +x install_amazon_q.sh
./install_amazon_q.sh
```

**설치 과정:**
1. Amazon Q CLI 다운로드 및 설치
2. uv (Python 패키지 관리자) 설치
3. graphviz 설치
4. Amazon Q 로그인 (브라우저에서 완료)
5. MCP 서버 설정 파일 생성

### 3. Python 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AMAZON_Q_PATH=q
```

### 5. 애플리케이션 실행

```bash
streamlit run main.py
```

## 📋 주요 기능

- **🤖 AI 아키텍처 설계**: 자연어로 AWS 아키텍처 설계
- **🎨 자동 다이어그램 생성**: Amazon Q를 통한 시각적 다이어그램 생성
- **🔒 보안 분석**: Gemini를 통한 보안 구성요소 분석
- **📄 보고서 생성**: 마크다운 형태의 보안 분석 보고서 다운로드

## 🛠️ 사용 방법

1. **아키텍처 설계**: 챗봇에 "서울 리전에 EC2 두 대 설치" 같은 요청 입력
2. **보안 요소 선택**: 체크리스트에서 필요한 보안 요소 선택
3. **다이어그램 생성**: "제작하기" 버튼 클릭
4. **결과 확인**: 생성된 다이어그램과 보안 분석 결과 확인
5. **보고서 다운로드**: 마크다운 형태로 분석 결과 다운로드

## 📁 프로젝트 구조

```
final/
├── main.py                 # 메인 애플리케이션
├── config.py              # 설정 파일
├── requirements.txt       # Python 의존성
├── install_amazon_q.sh    # Amazon Q 설치 스크립트
├── generated-diagrams/    # 생성된 다이어그램 저장 폴더
└── README.md             # 이 파일
```

## 🔧 문제 해결

### Amazon Q CLI 문제
- WSL에서 설치했는지 확인
- `q --version` 명령어로 설치 확인
- PATH에 `~/.local/bin`이 포함되어 있는지 확인

### Gemini API 문제
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인
- API 키가 유효한지 확인

### 다이어그램 생성 문제
- Amazon Q 로그인이 완료되었는지 확인
- MCP 설정 파일이 올바른 위치에 있는지 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

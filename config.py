"""
설정 및 환경변수 관리 모듈
"""
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 환경변수 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
AMAZON_Q_PATH = os.getenv('AMAZON_Q_PATH', 'q')  # Amazon Q CLI 경로

# Streamlit 페이지 설정
PAGE_CONFIG = {
    'page_title': "클라우드 아키텍처 다이어그램 생성기",
    'page_icon': "☁️",
    'layout': "wide"
}

# 다이어그램 생성 설정
DIAGRAM_SETTINGS = {
    'timeout': 120,
    'encoding': 'utf-8'
}

# 지원 플랫폼 정보
SUPPORTED_PLATFORMS = {
    'Windows': 'Windows (WSL 또는 네이티브)',
    'Linux': 'Linux',
    'Darwin': 'macOS'
}

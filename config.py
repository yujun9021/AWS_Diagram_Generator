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

# 다이어그램 생성 설정
DIAGRAM_SETTINGS = {
    'timeout': 120,
    'encoding': 'utf-8'
}

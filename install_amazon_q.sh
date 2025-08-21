#!/bin/bash

# Amazon Q 설치 및 설정 스크립트
echo "🚀 Amazon Q 설치 및 설정을 시작합니다..."

# 1. Amazon Q CLI 설치
echo "📦 Amazon Q CLI를 다운로드하고 설치합니다..."
curl --proto '=https' --tlsv1.2 -sSf "https://desktop-release.q.us-east-1.amazonaws.com/latest/q-x86_64-linux-musl.zip" -o "q.zip"
unzip q.zip
cd q
chmod +x install.sh
./install.sh

# 2. uv 설치
echo "📦 uv를 설치합니다..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. graphviz 설치
echo "📦 graphviz를 설치합니다..."
sudo apt install graphviz -y

# 4. Amazon Q 로그인
echo "🔐 Amazon Q 로그인을 시작합니다..."
echo "### 링크를 클릭하고 아마존에서 로그인을 완료해 주세요 ###"
q login

# 5. MCP 서버 설정 파일 생성
echo "⚙️ MCP 서버 설정 파일을 생성합니다..."
mkdir -p ~/.aws/amazonq

cat > ~/.aws/amazonq/mcp.json << 'EOF'
{
  "mcpServers": {
    "awslabs.aws-diagram-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-diagram-mcp-server"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "autoApprove": [],
      "disabled": false
    },
    "awslabs.aws-documentation-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "autoApprove": [],
      "disabled": false
    }
  }
}
EOF

echo "✅ Amazon Q 설치 및 설정이 완료되었습니다!"
echo ""
echo "📋 설치된 구성요소:"
echo "  - Amazon Q CLI"
echo "  - uv (Python 패키지 관리자)"
echo "  - graphviz (다이어그램 생성 도구)"
echo "  - MCP 서버 설정"
echo ""
echo "🔧 다음 단계:"
echo "  1. q 명령어로 Amazon Q CLI 테스트"
echo "  2. 애플리케이션에서 Amazon Q 기능 사용"
echo ""
echo "💡 문제가 발생하면 다음을 확인하세요:"
echo "  - PATH에 ~/.local/bin이 포함되어 있는지"
echo "  - Amazon Q 로그인이 완료되었는지"
echo "  - MCP 설정 파일이 올바른 위치에 있는지"

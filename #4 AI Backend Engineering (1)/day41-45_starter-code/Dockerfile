# 멀티 스테이지 빌드 1단계
FROM python:3.11-slim AS builder

# 컨테이너 내에서 작업 디렉토리 설정
WORKDIR /app

# uv를 공식 이미지에서 복사
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 현재 내 폴더에 있는 pyproject.tml, uv.lock*, README.md를 ./(컨테이너)로 복사
COPY pyproject.toml uv.lock* README.md ./

# uv sync
RUN uv sync --frozen --no-dev --no-cache

# 멀티 스테이지 빌드 2단계
FROM python:3.11-slim AS runtime

WORKDIR /app

# apt-get update : 패키지 목록 최신화
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY --from=builder /app/.venv /app/.venv

COPY app/ ./app/

# daily mission에서는 여기 삭제!
COPY data/ ./data/

COPY pyproject.toml README.md ./

# 파일, 폴더의 소유자를 변경
# chown -> 소유자가 아니면 파일을 읽거나 쓰기가 불가능. COPY 명령어로 복사한 것은 root 소유
# 유저를 만들어서, 그 유저에게 권한을 줘야 함
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# PYTHONBUFFERED=1 : 즉시 출력
# PYTHONDONTWRITEBYTECODE=1 : .pyc 파일 생성 X
# PATH : 가상 환경의 bin 디렉토리를 PATH에 추가해야 패키지 실행
ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fL http://localhost:8000/api/v1/health/ || exit 1

# 컨테이너가 사용할 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

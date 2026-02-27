"""
루미 세계관 문서를 벡터 DB에 적재하는 스크립트 (멱등성 보장)

이 스크립트는 다음 작업을 수행합니다:
1. 기존 documents 테이블 비우기 (truncate) → 멱등성 보장
2. Markdown 문서 로드 및 메타데이터 추출
3. 문서 청킹 (RecursiveCharacterTextSplitter)
4. Upstage Embedding으로 벡터화
5. Supabase pgvector에 저장

실행 방법:
    # 기본: v2.5 (active) + v1.0 (deprecated) 모두 적재
    uv run python scripts/ingest_rag.py

    # v2.5 (active)만 적재 (Distractor 제외)
    uv run python scripts/ingest_rag.py --active-only

멱등성:
    이 스크립트는 몇 번을 실행해도 동일한 결과를 보장합니다.
    실행 시 기존 데이터를 모두 삭제하고 새로 적재합니다.

Distractor란?
    RAG 시스템의 메타데이터 필터링을 테스트하기 위한 "방해 문서"입니다.
    - v2.5 (status="active"): 최신 정보 (정답)
    - v1.0 (status="deprecated"): 이전 정보 (Distractor)

    2강에서 필터링 유무에 따른 검색 결과 차이를 시연할 때 사용합니다.
    예: "루미가 좋아하는 음식?"
        - 필터링 없음 → v1.0 "딸기" (❌ 오래된 정보)
        - status="active" 필터링 → v2.5 "딸기 알러지" (✅ 최신 정보)

실행 전 필요사항:
    1. .env 파일에 UPSTAGE_API_KEY, SUPABASE_URL, SUPABASE_KEY 설정
    2. Supabase SQL Editor에서 data/schema.sql 실행
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def extract_metadata(content: str) -> dict:
    """
    문서 상단의 RAG_METADATA 블록에서 메타데이터를 추출합니다.

    문서 형식 예시:
        <!--
        RAG_METADATA:
        {
          "version": "2.5",
          "status": "active"
        }
        -->

    Args:
        content: 문서 내용

    Returns:
        dict: 추출된 메타데이터 (없으면 기본값)
    """
    pattern = r"RAG_METADATA:\s*(\{[\s\S]*?\})\s*-->"
    match = re.search(pattern, content)

    if match:
        try:
            metadata = json.loads(match.group(1))
            logger.info(f"메타데이터 추출 성공: {metadata.get('version', 'unknown')}")
            return metadata
        except json.JSONDecodeError as e:
            logger.warning(f"메타데이터 JSON 파싱 실패: {e}")

    # 기본 메타데이터
    return {
        "version": "unknown",
        "status": "active",
        "document_type": "character_profile",
    }


def chunk_document(
    content: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> list[str]:
    """
    문서를 청크 단위로 분할합니다.

    Markdown 문서의 경우 섹션 구분자를 기준으로 분할합니다.

    Args:
        content: 문서 내용
        chunk_size: 청크 최대 크기 (문자 수)
        chunk_overlap: 청크 간 중복 크기

    Returns:
        list[str]: 청크 목록
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # 마크다운 섹션 구분자 기준으로 분할
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n## ",  # H2 헤더
            "\n### ",  # H3 헤더
            "\n#### ",  # H4 헤더
            "\n\n",  # 빈 줄
            "\n",  # 줄바꿈
            " ",  # 공백
        ],
        length_function=len,
    )

    chunks = splitter.split_text(content)
    logger.info(f"문서를 {len(chunks)}개 청크로 분할")

    return chunks


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    청크들을 Upstage Embedding으로 벡터화합니다.

    Args:
        chunks: 청크 목록

    Returns:
        list[list[float]]: 임베딩 벡터 목록
    """
    from langchain_upstage import UpstageEmbeddings
    from app.core.config import settings

    if not settings.upstage_api_key:
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

    embeddings = UpstageEmbeddings(
        api_key=settings.upstage_api_key,
        model="solar-embedding-1-large-passage",  # 4096차원
    )

    logger.info(f"{len(chunks)}개 청크 임베딩 시작...")

    # 배치로 임베딩 (API 호출 최소화)
    vectors = await embeddings.aembed_documents(chunks)

    logger.info(f"임베딩 완료: {len(vectors)}개 벡터 (차원: {len(vectors[0])})")

    return vectors


async def truncate_documents() -> int:
    """
    documents 테이블의 모든 데이터를 삭제합니다. (멱등성 보장)

    Returns:
        int: 삭제된 레코드 수
    """
    from supabase import create_client
    from app.core.config import settings

    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase 설정이 완료되지 않았습니다.")

    client = create_client(settings.supabase_url, settings.supabase_key)

    # 기존 데이터 수 확인
    existing = client.table("documents").select("id", count="exact").execute()
    existing_count = existing.count or 0

    if existing_count > 0:
        # 모든 데이터 삭제 (UUID 타입이므로 content 필드로 비교)
        client.table("documents").delete().neq("content", "").execute()
        logger.info(f"🗑️ 기존 데이터 {existing_count}개 삭제 완료")
    else:
        logger.info("📭 기존 데이터 없음")

    return existing_count


async def save_to_supabase(
    chunks: list[str], vectors: list[list[float]], metadata: dict
) -> int:
    """
    청크와 벡터를 Supabase에 저장합니다.

    Args:
        chunks: 청크 목록
        vectors: 임베딩 벡터 목록
        metadata: 문서 메타데이터

    Returns:
        int: 저장된 레코드 수
    """
    from supabase import create_client
    from app.core.config import settings

    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase 설정이 완료되지 않았습니다.")

    client = create_client(settings.supabase_url, settings.supabase_key)

    logger.info("Supabase에 저장 시작...")

    saved_count = 0
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        try:
            # 각 청크별 메타데이터 (원본 + 청크 인덱스)
            chunk_metadata = {**metadata, "chunk_index": i, "chunk_total": len(chunks)}

            result = (
                client.table("documents")
                .insert(
                    {"content": chunk, "embedding": vector, "metadata": chunk_metadata}
                )
                .execute()
            )

            saved_count += 1

            if (i + 1) % 10 == 0:
                logger.info(f"진행 중: {i + 1}/{len(chunks)}")

        except Exception as e:
            logger.error(f"청크 {i} 저장 실패: {e}")

    logger.info(f"Supabase 저장 완료: {saved_count}개")

    return saved_count


async def ingest_document(file_path: str) -> dict:
    """
    단일 문서를 처리하여 벡터 DB에 저장합니다.

    Args:
        file_path: 문서 파일 경로

    Returns:
        dict: 처리 결과 (chunks, saved, metadata)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    logger.info(f"문서 로드: {path.name}")

    # 1. 문서 로드
    content = path.read_text(encoding="utf-8")

    # 2. 메타데이터 추출
    metadata = extract_metadata(content)

    # 3. 청킹
    chunks = chunk_document(content)

    # 4. 임베딩
    vectors = await embed_chunks(chunks)

    # 5. 저장
    saved_count = await save_to_supabase(chunks, vectors, metadata)

    return {
        "file": path.name,
        "chunks": len(chunks),
        "saved": saved_count,
        "metadata": metadata,
    }


def parse_args():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description="루미 세계관 문서를 벡터 DB에 적재합니다. (멱등성 보장)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본: v2.5 (active) + v1.0 (deprecated) 모두 적재
  uv run python data/scripts/ingest_rag.py

  # v2.5 (active)만 적재 (Distractor 제외)
  uv run python data/scripts/ingest_rag.py --active-only

멱등성:
  몇 번을 실행해도 동일한 결과를 보장합니다.
  실행 시 기존 데이터를 모두 삭제하고 새로 적재합니다.

Distractor 설명:
  v1.0 (deprecated)은 RAG 메타데이터 필터링 시연용 "방해 문서"입니다.
  2강에서 필터링 유무에 따른 검색 결과 차이를 시연할 때 사용합니다.
        """,
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="v2.5 (active) 문서만 적재 (Distractor 제외)",
    )
    return parser.parse_args()


async def main():
    """
    메인 실행 함수 (멱등성 보장)

    기본: v2.5 (active) + v1.0 (deprecated) 모두 적재
    --active-only: v2.5만 적재 (Distractor 제외)
    """
    args = parse_args()

    logger.info("=" * 60)
    logger.info("RAG 데이터 Ingestion (멱등성 보장)")
    logger.info("=" * 60)

    # 프로젝트 루트의 data 폴더 (현재 스크립트 위치: data/scripts/ingest_rag.py)
    # parent=scripts, parent.parent=data
    data_dir = Path(__file__).parent.parent

    # 적재할 파일 목록 (기본: 둘 다 적재)
    files_to_ingest = [
        ("lumi_worldview_v2.5.md", "active", "최신 정보 (정답)"),
    ]

    if not args.active_only:
        files_to_ingest.append(
            ("lumi_worldview_v1.0.md", "deprecated", "이전 정보 (Distractor)")
        )
    else:
        logger.info("📌 --active-only 모드: v2.5 (active)만 적재합니다.")
    logger.info("")

    # 파일 존재 확인
    for filename, _, _ in files_to_ingest:
        file_path = data_dir / filename
        if not file_path.exists():
            logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            logger.info(f"먼저 data/{filename} 파일을 생성하세요.")
            return

    try:
        # 1. 기존 데이터 삭제 (멱등성 보장)
        logger.info("🔄 Step 1: 기존 데이터 정리")
        await truncate_documents()

        # 2. 문서 적재
        logger.info("\n🔄 Step 2: 문서 적재")
        results = []
        total_chunks = 0
        total_saved = 0

        for filename, expected_status, description in files_to_ingest:
            file_path = data_dir / filename
            logger.info(f"\n📄 {filename} ({description})")
            logger.info("-" * 40)

            result = await ingest_document(str(file_path))
            results.append(result)
            total_chunks += result["chunks"]
            total_saved += result["saved"]

            # 메타데이터 검증
            actual_status = result["metadata"].get("status", "unknown")
            if actual_status != expected_status:
                logger.warning(
                    f"⚠️ 메타데이터 불일치: 예상={expected_status}, 실제={actual_status}"
                )

        # 최종 결과
        logger.info("\n" + "=" * 60)
        logger.info("Ingestion 결과 요약")
        logger.info("=" * 60)
        for result in results:
            status_emoji = (
                "✅" if result["metadata"].get("status") == "active" else "📦"
            )
            logger.info(
                f"{status_emoji} {result['file']}: {result['saved']}/{result['chunks']} 청크"
            )
        logger.info("-" * 40)
        logger.info(f"총 청크: {total_chunks}개, 저장: {total_saved}개")
        logger.info("=" * 60)

        logger.success("RAG Ingestion 완료!")

    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        logger.info("1. .env 파일에 UPSTAGE_API_KEY 설정")
        logger.info("2. .env 파일에 SUPABASE_URL, SUPABASE_KEY 설정")
        logger.info("3. Supabase SQL Editor에서 data/schema.sql 실행")

    except Exception as e:
        logger.error(f"Ingestion 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

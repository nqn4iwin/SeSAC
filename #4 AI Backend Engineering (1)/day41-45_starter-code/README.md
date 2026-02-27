# AI Backend Engineering(Service Deployment, LLMOps) Starter Code

## 환경 설정
```
uv sync
```

### Service Deployment 1강


### Service Deployment 2강
- LangGraph MVP 구현



### 프로젝트 구조
app/
├── core/
│   ├── config.py          ← 설정 관리 (pydantic-settings)
│   └── prompts.py         ← 프롬프트 분리
├── schemas/
│   └── chat.py            ← API 요청/응답 모델
├── graph/                  ← 노트북에서 만든 에이전트
│   ├── state.py           ← State 정의
│   ├── nodes.py           ← 노드 구현
│   ├── edges.py           ← 라우팅 로직
│   └── graph.py           ← 그래프 조립 + 싱글톤
├── repositories/           ← DB 접근 계층 (Mock → Real)
│   ├── rag.py             ← RAG 검색 (Supabase pgvector)
│   ├── schedule.py        ← 스케줄 조회
│   └── fan_letter.py      ← 팬레터 저장
├── tools/
│   └── executor.py        ← Tool 실행 (Repository 활용)
├── api/routes/
│   └── chat.py            ← REST API 엔드포인트
└── main.py                ← FastAPI 앱 (lifespan, CORS)

## 이슈
- from app.graph.state import LumiState : app.graph.state가 밑줄

# Service Deployment 3강
## 오늘 할 일
- 2강에서 만든 MVP -> 개선
- 스트리밍을 구현할 예정, 노드 상태 + 토큰 스트리밍을 동시에 보여주기
- 실시간 스트리밍

## TODO
- [ ] app/schemas/chat.py StreamEvent, to_sse()
- [ ] app/api/routes/chat.py : SSE 구현, stream_with_status 함수
    - [ ] SSE 엔드포인트 추가
- [ ] app/ui.py : 스트리밍 데이터를 받아서 처리할 수 있도록
- [ ] UI에서 확인
- [ ] router 쪽의 이슈 해결을 위한 코드
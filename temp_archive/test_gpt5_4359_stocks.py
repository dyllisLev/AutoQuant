#!/usr/bin/env python3
"""
gpt-5-mini 모델로 실제 4,359개 주식 데이터 테스트
실제 프롬프트 토큰 사용량 확인
"""

import os
import tiktoken
from openai import OpenAI

# OpenAI 클라이언트 초기화
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ 에러: OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
    exit(1)

client = OpenAI(api_key=api_key)
encoder = tiktoken.get_encoding("cl100k_base")

print("=" * 80)
print("gpt-5-mini: 4,359개 주식 데이터 테스트")
print("=" * 80)

# 4,359개 주식 데이터 생성
print("\n📊 4,359개 주식 데이터 생성 중...")
stocks_data = "주식 데이터:\n"
stocks_data += "Code|Name|Price|Change%|RSI\n"

for i in range(4359):
    code = f"{100000 + i:06d}"
    name = f"Stock{i}"
    price = 50000 + (i % 10000)
    change = 0.5 + (i % 100) * 0.01
    rsi = 50 + (i % 40)

    stocks_data += f"{code}|{name}|{price}|+{change:.1f}|{rsi}\n"

print(f"✅ 생성 완료: {len(stocks_data)} 글자")

# 프롬프트 구성
task_instruction = """당신은 한국 주식시장 전문가입니다.
주어진 시장 상황과 주식 데이터를 분석하여, 내일 상승 가능성이 높은 30-40개의 종목을 선별해주세요.

시장 분석:
- 시장 심리: NEUTRAL
- 모멘텀: 70/100
- 추세: DOWNTREND
- 변동성: 17.9
- 상위 섹터: Semiconductors, IT, Finance

선별 기준:
1. 시장 심리와 추세에 부합하는 주식
2. 기술적으로 강한 신호를 보이는 주식
3. 거래량이 증가하는 추세의 주식
4. 산업 섹터 추세를 고려한 주식

응답 형식:
{"candidates": [
    {"code": "100000", "name": "Stock0", "confidence": 75, "reason": "good setup"}
], "total_count": 30}

반드시 JSON만 반환하세요."""

full_prompt = f"{task_instruction}\n\n{stocks_data}"

# 토큰 사전 계산
prompt_tokens = encoder.encode(full_prompt)
token_count = len(prompt_tokens)

print(f"\n📈 프롬프트 토큰 분석:")
print("-" * 80)
print(f"Task instruction: {len(encoder.encode(task_instruction))} tokens")
print(f"Stock data: {len(encoder.encode(stocks_data))} tokens")
print(f"Total: {token_count} tokens")
print(f"Context window (gpt-5-mini): 400,000 tokens")
print(f"사용률: {token_count/400000*100:.2f}%")
print(f"여유: {400000 - token_count:,} tokens")

print(f"\n🤖 API 요청 중...")
print("-" * 80)

try:
    response = client.chat.completions.create(
        model="gpt-5-mini-2025-08-07",
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    print(f"✅ 성공!")
    print(f"\n📊 API 응답 정보:")
    print(f"   입력 토큰 (API 보고): {response.usage.prompt_tokens}")
    print(f"   출력 토큰 (API 보고): {response.usage.completion_tokens}")
    print(f"   총 토큰: {response.usage.prompt_tokens + response.usage.completion_tokens}")

    print(f"\n🔍 토큰 비교:")
    print(f"   사전 계산: {token_count} tokens")
    print(f"   API 보고: {response.usage.prompt_tokens} tokens")
    print(f"   차이: {token_count - response.usage.prompt_tokens} tokens ({(1 - response.usage.prompt_tokens/token_count)*100:.1f}% 손실)")

    print(f"\n📝 응답 내용 (처음 300글자):")
    response_text = response.choices[0].message.content
    print(f"   {response_text[:300]}...")

    # 응답 검증
    if '"candidates"' in response_text and '"code"' in response_text:
        print(f"\n✅ JSON 포맷 검증: PASS")

        import json
        try:
            data = json.loads(response_text)
            num_candidates = len(data.get('candidates', []))
            print(f"   선별된 종목 수: {num_candidates}")
            if 30 <= num_candidates <= 40:
                print(f"   범위 검증: PASS (30-40개 범위)")
            else:
                print(f"   범위 검증: FAIL ({num_candidates}개, 30-40개 범위 아님)")
        except:
            print(f"   JSON 파싱: FAIL")
    else:
        print(f"\n❌ JSON 포맷 검증: FAIL")

    print(f"\n💾 결과 저장...")
    with open('/opt/AutoQuant/test_gpt5_4359_result.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== gpt-5-mini 4,359 주식 테스트 결과 ===\n\n")
        f.write(f"Token Analysis:\n")
        f.write(f"  Pre-calculated: {token_count}\n")
        f.write(f"  API reported: {response.usage.prompt_tokens}\n")
        f.write(f"  Difference: {token_count - response.usage.prompt_tokens} ({(1 - response.usage.prompt_tokens/token_count)*100:.1f}%)\n\n")
        f.write(f"Response:\n")
        f.write(response_text)

    print(f"   저장됨: /opt/AutoQuant/test_gpt5_4359_result.txt")

except Exception as e:
    print(f"❌ 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)

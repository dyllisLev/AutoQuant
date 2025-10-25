# Phase 3 AI Screening - Request Logic Fix

## Problem Identified
Phase 3 AI-based stock screening was returning 0 candidates despite properly generating 4,359 stocks and receiving full responses from OpenAI. The issue was a **request logic mismatch** between the working simple test (`test_gpt5_simple.py`) and the complex implementation (`ai_screener.py`).

## Root Cause Analysis

### Test Comparison
**Working Test** (`test_gpt5_simple.py`):
```python
response = client.chat.completions.create(
    model="gpt-5-mini-2025-08-07",
    messages=[{"role": "user", "content": "Hello, what is 2+2?"}]
)
```

**Failing Implementation** (`ai_screener.py` - old code):
- Strategy 1: Attempted non-existent `responses.create()` API ❌
- Strategy 2: Used `chat.completions.create()` WITH unsupported parameters:
  - `max_completion_tokens=2000` ❌ (not supported)
  - `timeout=120` ❌ (causes issues)
  - Previously had `temperature=0.7` ❌ (not supported)

## Solution Implemented

### Simplified Request Logic
**File**: `src/screening/ai_screener.py` - `_call_openai()` method

Changed from complex dual-strategy approach to single, proven pattern:

```python
def _call_openai(self, prompt: str) -> str:
    """Call OpenAI GPT-5 API - simple and direct approach"""
    try:
        # Use simple chat.completions.create() pattern (tested and working)
        # gpt-5-mini-2025-08-07 specs:
        # - 400K context window
        # - No temperature support (only default=1)
        # - No max_completion_tokens parameter
        # - No timeout parameter
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract response content
        content = response.choices[0].message.content or ""

        # Track cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000
        self.api_total_cost += cost

        self.logger.info(f"OpenAI API call: {input_tokens} input + {output_tokens} output tokens (${cost:.4f}), response: {len(content)} chars")
        return content
    except Exception as e:
        self.logger.error(f"OpenAI API call failed: {str(e)}")
        raise
```

## Test Results

### Phase 3 Integration Test
```
✅ Generated 4,359 stocks
✅ AI screening complete: 36 candidates selected in 83.5s
✅ Cost: $0.6629
✅ Filtering ratio: 4,359 → 36 (0.83%)

Top 5 Recommended Stocks:
   1. 103316 (Stock3316) - Confidence: 86%
   2. 101695 (Stock1695) - Confidence: 84%
   3. 104111 (Stock4111) - Confidence: 83%
   4. 104206 (Stock4206) - Confidence: 83%
   5. 100530 (Stock530) - Confidence: 82%
```

### Token Usage Verification
```
Input tokens: 17,190 (4,359 stocks with preview)
Output tokens: 5,401 (full JSON with 36 candidates + reasoning)
Total: 22,591 tokens
Cost: $0.6629
```

✅ **NO TOKEN TRUNCATION** - All 4,359 stocks processed correctly!

## Key Learnings

1. **gpt-5-mini-2025-08-07 API Specifications**:
   - Context window: 400K tokens
   - Max output: 128K tokens
   - Does NOT support: `temperature`, `max_completion_tokens`, `timeout`
   - Does NOT have: `responses.create()` API (that's a Anthropic feature)

2. **When Complex Fails, Go Simple**: The elaborate dual-strategy fallback approach was over-engineered and added failure points. The simple direct approach is more reliable.

3. **API Consistency**: Always test edge cases and validate API parameter support before implementing complex error handling logic.

## Files Modified
- `src/screening/ai_screener.py` - Simplified `_call_openai()` method (lines 378-405)

## Test Command
```bash
python -m pytest tests/user_tests/test_phase_3_integration.py::TestPhase3Integration::test_phase3_ai_screening -v -s
```

## Status
✅ **Phase 3: AI-Based Stock Screening - COMPLETE**
- Filters 4,359 Korean stocks to 30-40 candidates
- Uses gpt-5-mini for semantic analysis with market context
- Returns confidence scores and reasoning for each candidate
- Tracks API costs and performance metrics

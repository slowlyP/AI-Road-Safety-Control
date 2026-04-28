import os
import json
import logging

from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

LABEL_KR_MAP = {
    "bag": "방치된 포대",
    "box": "박스 낙하물",
    "rock": "낙석",
    "tire": "타이어 파편"
}

api_key = os.environ.get("GEMINI_API_KEY")
client = None

if not api_key:
    logger.critical("🚨 [환경변수 에러] GEMINI_API_KEY가 설정되지 않았습니다.")
else:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"🚨 [클라이언트 생성 실패]: {e}")
        client = None


def generate_report_text(detected_objects, location_address="전방 도로"):
    """
    AI 탐지 결과와 위치 정보를 바탕으로 자연스러운 신고 문구를 생성합니다.
    """

    if not detected_objects:
        return {
            "title": "도로 안전 점검 알림",
            "content": "특이사항이 발견되지 않았으나 안전 운행하시기 바랍니다."
        }

    objects_kr = [LABEL_KR_MAP.get(str(obj), str(obj)) for obj in detected_objects]
    objects_str = ", ".join(objects_kr)

    fallback_result = {
        "title": f"[주의] {objects_str} 발견",
        "content": f"{location_address} 인근에 {objects_str}이(가) 확인되었습니다. 주의 운전 바랍니다."
    }

    if client is None:
        return fallback_result

    prompt = f"""
당신은 도로 안전 관리 전문 AI입니다.
현재 '{location_address}' 부근에서 '{objects_str}'이(가) 확인되었습니다.

운전자들이 즉시 위험을 인지하고 조심할 수 있도록 자연스러운 경고문을 작성하세요.

조건:
- 제목 20자 이내
- 내용 100자 이내
- 반드시 JSON만 출력
- 형식:
{{
  "title": "...",
  "content": "..."
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )

        if not response or not getattr(response, "text", None):
            raise ValueError("AI 응답이 비어 있습니다.")

        parsed = json.loads(response.text)

        if not isinstance(parsed, dict):
            raise ValueError("AI 응답 JSON 형식이 올바르지 않습니다.")

        title = parsed.get("title", fallback_result["title"])
        content = parsed.get("content", fallback_result["content"])

        return {
            "title": str(title)[:30],
            "content": str(content)[:200]
        }

    except google_exceptions.DeadlineExceeded:
        logger.error("🚨 [LLM 타임아웃] API 응답 시간이 초과되었습니다.")
        return fallback_result

    except google_exceptions.ResourceExhausted:
        logger.error("🚨 [LLM 할당량 초과] API 사용량이 너무 많습니다.")
        return fallback_result

    except json.JSONDecodeError as e:
        raw_text = getattr(response, "text", "응답 없음") if "response" in locals() else "응답 없음"
        logger.error(f"🚨 [LLM JSON 파싱 에러] {e} | 원본 응답: {raw_text}")
        return fallback_result

    except Exception as e:
        logger.error(f"🚨 [LLM 알 수 없는 에러] {e}")
        return fallback_result
import os
import streamlit as st
from openai import OpenAI


def build_ai_sales_comment(final_summary: str, industry: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        api_key = st.secrets.get("OPENAI_API_KEY")

    if not api_key:
        return "AI 코멘트를 사용하려면 OPENAI_API_KEY 설정이 필요합니다."

    client = OpenAI(api_key=api_key)

    prompt = f"""
너는 매출 데이터를 읽고 실무적인 코멘트를 해주는 분석가다.

업종: {industry}

아래 요약 리포트를 바탕으로:
1. 가장 중요한 핵심 포인트 2개
2. 위험 신호 1개
3. 바로 해볼 액션 2개

를 한국어로 짧고 명확하게 작성해라.
너무 장황하지 말고, 실무자가 바로 읽을 수 있게 써라.

매출 리포트:
{final_summary}
"""

    response = client.responses.create(
        model="gpt-5.2",
        input=prompt
    )

    return response.output_text.strip()
'''이 코드는 공식 Python 라이브러리 README의 
OpenAI(...); client.responses.create(...); response.output_text 패턴을 따른 거'''
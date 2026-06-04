from openai import OpenAI
import os


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

MODEL = os.getenv("DEFAULT_MODEL")

SYSTEM_PROMPT = """
你是高级 SRE。

你需要根据：
1. 监控
2. 日志
3. SQL

分析根因。

并给出：
- Root Cause
- Impact
- Fix Suggestion
"""


def analyze(user_input, observations):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
用户问题:
{user_input}

工具结果:
{observations}
"""
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
from openai import OpenAI
from tools import get_tools, get_tool_schemas
import json
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

MODEL = os.getenv("DEFAULT_MODEL")

TOOLS = get_tools()
tool_schemas = get_tool_schemas()

class EventDrivenAgent:

    def handle_event(self, event):

        print(f"\n{'='*60}")
        print(f"[事件接收] {event}")
        print(f"{'='*60}")

        messages = [
            {
                "role": "system",
                "content": """
你是一个K8s运维Agent。

你的职责：

1. 分析线上故障
2. 调用工具排查
3. 自动恢复服务

请一步一步推理。
"""
            },
            {
                "role": "user",
                "content": f"收到告警事件: {event}"
            }
        ]

        while True:

            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto"
            )

            msg = response.choices[0].message

            # 输出LLM思考
            if msg.content:
                print(f"\n{'-'*60}")
                print(f"[LLM 思考] {msg.content}")
                print(f"{'-'*60}")

            # 是否调用工具
            if msg.tool_calls:

                tool_call = msg.tool_calls[0]

                tool_name = tool_call.function.name

                args = json.loads(tool_call.function.arguments)

                print(f"\n{'>'*60}")
                print(f"[工具调用] Action: {tool_name}")
                print(f"[参数] Args: {args}")
                print(f"{'>'*60}")

                tool_func = TOOLS[tool_name]

                result = tool_func(**args)

                print(f"\n{'<'*60}")
                print(f"[工具返回] Observation: {result}")
                print(f"{'<'*60}")

                messages.append(msg)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            else:
                print(f"\n{'='*60}")
                print(f"[最终结论]")
                print(f"{msg.content}")
                print(f"{'='*60}")
                break

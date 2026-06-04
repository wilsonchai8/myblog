from openai import OpenAI
import json
import os
import inspect
import tools

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

MODEL = os.getenv("DEFAULT_MODEL")


def get_tool_descriptions():
    """自动从 tools 模块获取工具描述"""
    descriptions = []

    # 获取 tools 模块中所有的函数
    for name, func in inspect.getmembers(tools, inspect.isfunction):
        if not name.startswith('_'):
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            doc = func.__doc__.strip() if func.__doc__ else "未提供描述"

            descriptions.append({
                "name": name,
                "description": doc,
                "params": params
            })

    return descriptions


def build_system_prompt():
    """构建包含工具描述的 system prompt"""
    tool_descs = get_tool_descriptions()

    tool_section = "可用工具：\n\n"
    for i, tool in enumerate(tool_descs, 1):
        tool_section += f"{i}. {tool['name']}\n"
        tool_section += f"{tool['description']}\n"
        tool_section += f"参数: {', '.join(tool['params'])}\n\n"

    return f"""你是一个 SRE 日志分析 Agent。

你需要：
1. 理解用户问题
2. 制定排查计划
3. 返回 JSON

{tool_section}
返回格式：

[
  {{
    "step": 1,
    "tool": "工具名称",
    "args": {{
      "参数名": "参数值"
    }},
    "reason": "为什么执行这一步"
  }}
]
"""


SYSTEM_PROMPT = build_system_prompt()


def make_plan(user_input: str):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    print("\n===== Planner LLM 输出 =====")
    print(content)

    return json.loads(content)

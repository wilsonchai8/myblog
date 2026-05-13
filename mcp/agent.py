import json
import asyncio
import os
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# OpenAI Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

MODEL = os.getenv("DEFAULT_MODEL")


async def call_mcp_tool():
    """
    调用 MCP Server
    """
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 调用 get_monitor_metrics 工具
            result = await session.call_tool("get_monitor_metrics")

            # 解析返回内容
            if result.content and len(result.content) > 0:
                text_content = result.content[0].text
                return json.loads(text_content)
            return None


def analyze_system(metrics):
    """
    交给 LLM 分析
    """

    prompt = f"""
你是一个 SRE 运维专家。

下面是线上监控指标：

{json.dumps(metrics, indent=2)}

请分析：

1. 当前系统是否异常
2. 哪些指标有问题
3. 可能原因
4. 建议下一步排查动作

"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


async def main():

    print("=" * 50)
    print("Step1: 获取监控数据")
    print("=" * 50)

    # 通过 MCP Client SDK 获取数据
    metrics_result = await call_mcp_tool()

    if metrics_result and metrics_result.get("status") == "success":
        metrics = metrics_result.get("data")
    else:
        raise Exception("Failed to get metrics from MCP Server")

    print(json.dumps(metrics, indent=2))

    print()
    print("=" * 50)
    print("Step2: Agent 分析")
    print("=" * 50)

    result = analyze_system(metrics)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())

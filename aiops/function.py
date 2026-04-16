from openai import OpenAI
import json
import os


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

model = os.getenv("DEFAULT_MODEL")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "获取Pod日志用于排查问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string"},
                    "namespace": {"type": "string"}
                },
                "required": ["pod_name"]
            }
        }
    }
]


def get_pod_state(pod_name, namespace):
    # 可以用 kubectl 或 k8s API, 返回：Running / CrashLoopBackOff / OOMKilled 等
    return "CrashLoopBackOff"

def get_pod_logs(pod_name, namespace="default"):
    # 去日志平台上获取对应的日志即可
    return "ERROR: database connection failed\nException: timeout"

def main():
    pod_name = 'payment-pod'
    namespace = 'default'
    pod_state = get_pod_state(pod_name, namespace)
    messages = [
        {
            "role": "system",
            "content": """你是Kubernetes运维专家。

    判断 Pod 状态：
    - 如果是 Running / 正常 → 返回 OK
    - 如果是 CrashLoopBackOff / OOMKilled / Error → 返回 NEED_DEBUG

    只返回 OK 或 NEED_DEBUG"""
        },
        {
            "role": "user",
            "content": f"Pod状态是: {pod_state}"
        }
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=messages
    )

    decision = resp.choices[0].message.content.strip()

    if decision == "OK":
        print("Pod 正常，无需排查")
        exit()

    messages = [
        {
            "role": "system",
            "content": """你是一个Kubernetes故障诊断专家。

当Pod异常时：
1. 必须调用 get_pod_logs 获取日志
2. 根据日志分析问题
3. 输出：
   - 问题原因
   - 根因分析
   - 修复建议
"""
        },
        {
            "role": "user",
            "content": f"Pod {pod_name} 状态是 {pod_state}，请排查问题"
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        tool_call = msg.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        logs = get_pod_logs(**args)
        final_resp = client.chat.completions.create(
            model=model,
            messages=[
                *messages,
                msg,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": logs[:3000]
                }
            ]
        )

        print("\nAI 分析结果:\n")
        print(final_resp.choices[0].message.content)


if __name__ == "__main__":
    main()


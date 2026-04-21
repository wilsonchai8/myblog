from openai import OpenAI
import json
import os
from datetime import datetime, timedelta


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

model = os.getenv("DEFAULT_MODEL")


def get_pod_status(namespace: str = "default", pod_name: str = ""):
    return {
        "namespace": namespace,
        "pod_name": pod_name,
        "status": "CrashLoopBackOff",
        "restart_count": 5,
        "node": "10.10.1.23",
        "events": [
            "2026-04-20 11:42:11 Readiness probe failed: connection refused",
            "2026-04-20 11:42:25 Container restarted",
            "2026-04-20 11:42:25 Last State: Terminated, Reason: OOMKilled"
        ]
    }


def get_business_log(service_name: str = "", start_time: str = "", end_time: str = ""):
    if not start_time:
        start_time = (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    if not end_time:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "service_name": service_name,
        "time_range": {
            "start_time": start_time,
            "end_time": end_time
        },
        "logs": [
            "2026-04-20 11:41:02 [ERROR] order-service create order failed: java.lang.NullPointerException",
            "2026-04-20 11:41:03 [ERROR] order-service db timeout when inserting order record",
            "2026-04-20 11:41:04 [WARN] order-service retry failed, return HTTP 500"
        ]
    }


def get_system_metrics(node_ip: str = "", start_time: str = "", end_time: str = ""):
    if not start_time:
        start_time = (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    if not end_time:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "node_ip": node_ip,
        "time_range": {
            "start_time": start_time,
            "end_time": end_time
        },
        "metrics": {
            "cpu_usage": "91%",
            "memory_usage": "93%",
            "disk_usage": "58%",
            "network_rx": "110MB/s",
            "network_tx": "76MB/s"
        }
    }


TOOL_MAP = {
    "get_pod_status": get_pod_status,
    "get_business_log": get_business_log,
    "get_system_metrics": get_system_metrics,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pod_status",
            "description": "获取 Kubernetes Pod 的运行状态、重启次数和事件信息，用于排查 Pod 异常重启、启动失败、探针失败、CrashLoopBackOff 等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Pod 所在命名空间，默认 default"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 名称或者工作负载名称"
                    }
                },
                "required": ["pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_business_log",
            "description": "获取业务服务日志，用于排查接口报错、HTTP 500、代码异常、数据库超时、调用下游失败等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "服务名称，比如 order-service"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "查询开始时间，格式 YYYY-MM-DD HH:MM:SS"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "查询结束时间，格式 YYYY-MM-DD HH:MM:SS"
                    }
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_metrics",
            "description": "获取节点操作系统监控数据，包括 CPU、内存、磁盘和网络使用情况，用于排查节点负载高、资源瓶颈、系统卡顿等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_ip": {
                        "type": "string",
                        "description": "节点 IP 地址"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "查询开始时间，格式 YYYY-MM-DD HH:MM:SS"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "查询结束时间，格式 YYYY-MM-DD HH:MM:SS"
                    }
                },
                "required": ["node_ip"]
            }
        }
    }
]


def run_agent(user_query: str):
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个线上故障排查专家。"
                "请根据用户问题自主选择最合适的工具。"
                "如果一个工具不足以定位问题，可以继续调用其他工具。"
                "回答时要基于工具返回的事实，不要编造。"
            )
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    while True:
        response = client.chat.completions.create(
            model=model,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
            tools=tools,  # type: ignore[arg-type]
            tool_choice="auto"
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls

        if not tool_calls:
            return message.content

        messages.append(message)  # type: ignore[arg-type]

        for tool_call in tool_calls:
            tool_name = tool_call.function.name  # type: ignore[attr-defined]
            tool_args = json.loads(tool_call.function.arguments or "{}")  # type: ignore[attr-defined]

            print(f"[TOOL] {tool_name} args={tool_args}")

            tool_func = TOOL_MAP[tool_name]
            tool_result = tool_func(**tool_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
            )


if __name__ == "__main__":
    test_queries = [
        "我的 order-service Pod 一直重启，帮我看看怎么回事",
        "下单接口一直返回 500，帮我查一下日志",
        "节点 10.10.1.23 最近特别卡，帮我看下是不是资源打满了",
        "order-service 返回 500，而且 Pod 也反复重启，帮我整体分析一下"
    ]

    for idx, query in enumerate(test_queries, start=1):
        print(f"\n===== 测试 {idx} =====")
        print(f"[USER] {query}")
        answer = run_agent(query)
        print(f"[FINAL] {answer}")

from mcp.server.fastmcp import FastMCP
import random
import time
import datetime
import json
import os

# 创建 MCP Server
mcp = FastMCP("monitor-platform")

# 日志文件路径
LOG_FILE = "mcp_server_calls.log"


def log_call(tool_name: str, result: dict):
    """
    记录工具调用日志
    """
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": tool_name,
        "result": result
    }

    # 追加写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[LOG ERROR] {e}")


# 模拟监控数据
def generate_mock_metrics():
    return {
        "timestamp": int(time.time()),

        # CPU
        "cpu_usage": round(random.uniform(20, 95), 2),

        # 内存
        "memory_usage": round(random.uniform(30, 98), 2),

        # pod 重启次数
        "pod_restart_count": random.randint(0, 15),

        # 接口错误率
        "api_error_rate": round(random.uniform(0, 20), 2),

        # QPS
        "qps": random.randint(100, 5000),

        # RT
        "latency_ms": random.randint(20, 3000),
    }


# MCP Tool
@mcp.tool()
def get_monitor_metrics():
    """
    获取线上监控平台指标
    """

    data = generate_mock_metrics()

    result = {
        "status": "success",
        "data": data
    }

    # 记录调用日志
    log_call("get_monitor_metrics", result)

    return result


if __name__ == "__main__":
    print(f"[MCP Server] Starting... Log file: {os.path.abspath(LOG_FILE)}")
    mcp.run()

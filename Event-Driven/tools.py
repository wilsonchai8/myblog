import inspect
from typing import Dict, Any, List


# 存储工具元数据
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, parameters: Dict[str, Any]):
    """
    装饰器：注册工具函数及其元数据
    """
    def decorator(func):
        _TOOL_REGISTRY[name] = {
            "function": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
        }
        return func
    return decorator


@tool(
    name="query_pod_status",
    description="查询服务Pod状态",
    parameters={
        "type": "object",
        "properties": {
            "service": {
                "type": "string"
            }
        },
        "required": ["service"]
    }
)
def query_pod_status(service):
    print(f"[Tool] 查询 Pod 状态: {service}")
    return f"{service} 有 2 个 Pod CrashLoopBackOff"


@tool(
    name="query_logs",
    description="查询服务日志",
    parameters={
        "type": "object",
        "properties": {
            "service": {
                "type": "string"
            }
        },
        "required": ["service"]
    }
)
def query_logs(service):
    print(f"[Tool] 查询日志: {service}")
    return "数据库连接超时 timeout"


@tool(
    name="restart_service",
    description="重启服务",
    parameters={
        "type": "object",
        "properties": {
            "service": {
                "type": "string"
            }
        },
        "required": ["service"]
    }
)
def restart_service(service):
    print(f"[Tool] 重启服务: {service}")
    return f"{service} 已成功重启"


def get_tools() -> Dict[str, callable]:
    """获取所有工具函数"""
    return {name: info["function"] for name, info in _TOOL_REGISTRY.items()}


def get_tool_schemas() -> List[Dict[str, Any]]:
    """获取所有工具的schema"""
    return [info["schema"] for info in _TOOL_REGISTRY.values()]

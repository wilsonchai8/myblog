import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# 配置
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://你的prometheus地址:9090")
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# Mock 数据
MOCK_DATA = {
    "up": json.dumps([
        {"metric": {"job": "order-service", "instance": "10.0.0.1:8080"}, "value": [1715731200, "1"]},
        {"metric": {"job": "order-service", "instance": "10.0.0.2:8080"}, "value": [1715731200, "0"]}
    ], ensure_ascii=False, indent=2),

    "container_cpu_usage_seconds_total": json.dumps([
        {"metric": {"pod": "order-service-789", "namespace": "prod"}, "value": [1715731200, "0.85"]}
    ], ensure_ascii=False, indent=2),

    "container_memory_usage_bytes": json.dumps([
        {"metric": {"pod": "order-service-789", "namespace": "prod"}, "value": [1715731200, "2147483648"]}
    ], ensure_ascii=False, indent=2),

    "http_requests_total": json.dumps([
        {"metric": {"job": "order-service", "status": "504"}, "value": [1715731200, "127"]},
        {"metric": {"job": "order-service", "status": "200"}, "value": [1715731200, "4523"]}
    ], ensure_ascii=False, indent=2),

    "kube_pod_container_status_restarts_total": json.dumps([
        {"metric": {"pod": "order-service-789", "namespace": "prod"}, "value": [1715731200, "5"]}
    ], ensure_ascii=False, indent=2),
}


def prometheus_query(query: str) -> str:
    """
    调用 Prometheus API 查询监控指标（支持 mock 模式）
    """
    if USE_MOCK:
        return _mock_query(query)

    url = f"{PROMETHEUS_URL}/api/v1/query"
    params = {"query": query}
    try:
        resp = requests.get(url, params=params, timeout=5)
        result = resp.json()
        if result.get("status") == "success":
            return json.dumps(result["data"]["result"], ensure_ascii=False, indent=2)
        return "查询失败"
    except Exception as e:
        return f"请求异常：{str(e)}"


def _mock_query(query: str) -> str:
    """
    根据查询关键词返回对应 mock 数据
    """
    query_lower = query.lower()
    for key, data in MOCK_DATA.items():
        if key in query_lower:
            return data

    # 默认返回一个通用 mock 数据
    return json.dumps([
        {"metric": {"job": "order-service"}, "value": [1715731200, "1"]}
    ], ensure_ascii=False, indent=2)


# Nginx 日志 Mock 数据
NGINX_MOCK_LOGS = [
    '10.0.0.100 - - [14/May/2026:18:30:01 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.101 - - [14/May/2026:18:30:02 +0000] "POST /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.102 - - [14/May/2026:18:30:03 +0000] "GET /api/orders/123 HTTP/1.1" 200 1234 "-" "Mozilla/5.0"',
    '10.0.0.103 - - [14/May/2026:18:30:04 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.104 - - [14/May/2026:18:30:05 +0000] "GET /health HTTP/1.1" 200 100 "-" "kube-probe"',
    '10.0.0.100 - - [14/May/2026:18:30:06 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.101 - - [14/May/2026:18:30:07 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.102 - - [14/May/2026:18:30:08 +0000] "POST /api/payments HTTP/1.1" 200 456 "-" "Mozilla/5.0"',
    '10.0.0.103 - - [14/May/2026:18:30:09 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
    '10.0.0.104 - - [14/May/2026:18:30:10 +0000] "GET /api/orders HTTP/1.1" 504 592 "-" "Mozilla/5.0"',
]


def nginx_log_query(status: str = "", path: str = "", limit: int = 10) -> str:
    """
    查询 nginx 日志（支持 mock 模式）
    :param status: 按状态码过滤，如 "504"
    :param path: 按路径过滤，如 "/api/orders"
    :param limit: 返回日志条数
    """
    if USE_MOCK:
        return _mock_nginx_logs(status, path, limit)

    # 真实实现可以对接 Elasticsearch/Loki 等
    return "真实查询待实现"


def _mock_nginx_logs(status: str = "", path: str = "", limit: int = 10) -> str:
    """
    返回 mock nginx 日志
    """
    logs = NGINX_MOCK_LOGS.copy()

    if status:
        logs = [log for log in logs if f'" {status} ' in log]

    if path:
        logs = [log for log in logs if path in log]

    return "\n".join(logs[:limit])


# 告警平台数据
def check_alarm_platform(service: str = "order-service") -> str:
    """查询告警平台，获取当前服务的告警信息"""
    print(f"[调用工具] check_alarm_platform(service=\"{service}\")")
    alarms = [
        "[CRITICAL] 订单服务 5xx 错误率过高 (当前: 15%, 阈值: 5%)",
        "[WARNING] 订单服务响应时间 P99: 3.2s (阈值: 1s)",
        "[INFO] 订单服务实例数: 3/3 正常"
    ]
    return "\n".join(alarms)


# 业务日志数据
def get_business_logs(service: str = "order-service", keyword: str = "error") -> str:
    """获取业务服务的日志，可按关键词过滤"""
    print(f"[调用工具] get_business_logs(service=\"{service}\", keyword=\"{keyword}\")")
    logs = [
        "[2026-05-25 18:30:01] ERROR OrderService - DB connection timeout: jdbc:mysql://db:3306/orders",
        "[2026-05-25 18:30:02] ERROR OrderService - Failed to create order: java.sql.SQLTransientConnectionException",
        "[2026-05-25 18:30:03] WARN  OrderService - Connection pool is full (active: 20, max: 20)",
        "[2026-05-25 18:30:04] ERROR OrderService - Query timeout: SELECT * FROM orders WHERE id = ? (4.5s)",
        "[2026-05-25 18:30:05] INFO  OrderService - Retrying request... (attempt 2/3)"
    ]
    return "\n".join(logs)


# Nginx 监控指标
def get_nginx_metrics() -> str:
    """获取 Nginx 的监控指标数据"""
    print(f"[调用工具] get_nginx_metrics()")
    metrics = [
        "nginx_requests_total{status=\"5xx\"}: 127 in last 5 minutes",
        "nginx_requests_total{status=\"2xx\"}: 4523 in last 5 minutes",
        "nginx_connections_active: 245",
        "nginx_upstream_response_time{upstream=\"order-service\"}: 2.8s (P99)"
    ]
    return "\n".join(metrics)

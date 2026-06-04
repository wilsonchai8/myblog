

def query_alarm(service: str = "", **kwargs):
    """查询服务监控告警信息"""
    return {
        "service": service,
        "p99": "5.2s",
        "error_rate": "18%",
        "status": "critical"
    }


def query_logs(keyword: str = "", service: str = "", **kwargs):
    """查询服务日志，支持关键词过滤"""
    logs = [
        "ERROR db timeout after 3000ms",
        "ERROR db timeout after 3000ms",
        "WARN redis retry",
        "ERROR mysql connection failed",
    ]

    if keyword:
        logs = [x for x in logs if keyword.lower() in x.lower()]

    return logs


def analyze_errors(logs):
    """分析错误日志"""
    db_timeout = sum(1 for x in logs if "timeout" in x)

    if db_timeout >= 2:
        return "大量 DB 超时"

    return "未知错误"

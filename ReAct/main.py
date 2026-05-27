import os
from openai import OpenAI
from dotenv import load_dotenv
from data_sources import (
    nginx_log_query,
    check_alarm_platform,
    get_business_logs
)

# 加载环境变量
load_dotenv()

# 初始化 LLM
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("API_BASE_URL")
)

MODEL = os.getenv("DEFAULT_MODEL") or "gpt-4o"  # 默认模型


# ==============================================
# 经典显式 ReAct 模式
# ==============================================
def react_agent_explicit(alarm_info: str):
    """
    经典显式 ReAct 模式：
    Thought → Action → Observation → ... → Final Answer
    """
    print("===== 故障排查 AI Agent 启动 (经典 ReAct 模式) =====\n")
    print(f"故障信息: {alarm_info}\n")

    system_prompt = """你是一个专业的线上故障排查专家。你需要通过 ReAct 模式来逐步排查问题。

可用工具：
- check_alarm_platform(service): 查询告警平台
- nginx_log_query(status, path, limit): 查询 Nginx 日志
- get_business_logs(service, keyword): 获取业务日志

你必须严格按照以下格式输出：

Thought: 你的思考过程，分析当前情况并决定下一步做什么
Action: 要调用的工具和参数，例如：check_alarm_platform(service="order-service")
Observation: （工具返回的结果，不需要你输出）

或者，当你认为已经收集到足够信息时：

Thought: 我已经收集到足够的信息，可以得出结论了
Final Answer: 完整的故障排查报告，包括故障现象、根因定位、解决方案

注意：
1. 每轮只输出一个 Thought + Action 或 Thought + Final Answer
2. 不要输出其他额外内容
3. Action 只能调用上面列出的工具"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请帮我排查以下故障：{alarm_info}"}
    ]

    max_rounds = 8
    round_count = 0

    while round_count < max_rounds:
        round_count += 1
        print(f"--- [第 {round_count} 轮] ---")

        # 1. LLM 生成 Thought + Action
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1
        )

        reply = response.choices[0].message.content or ""
        print(reply)

        # 2. 检查是否是 Final Answer
        if "Final Answer:" in reply:
            print("\n===== 排查完成 =====")
            break

        # 3. 解析 Action 并执行
        if "Action:" in reply:
            # 提取 Action 内容
            action_part = reply.split("Action:", 1)[1].strip()

            # 执行对应的工具
            observation = ""
            if "check_alarm_platform" in action_part:
                # 解析参数
                service = "order-service"
                if 'service="' in action_part:
                    start = action_part.find('service="') + 9
                    end = action_part.find('"', start)
                    service = action_part[start:end]
                observation = check_alarm_platform(service)

            elif "nginx_log_query" in action_part:
                status: str = ""
                if 'status="' in action_part:
                    start = action_part.find('status="') + 8
                    end = action_part.find('"', start)
                    status = action_part[start:end]
                observation = nginx_log_query(status=status)

            elif "get_business_logs" in action_part:
                service = "order-service"
                keyword = "error"
                if 'service="' in action_part:
                    start = action_part.find('service="') + 9
                    end = action_part.find('"', start)
                    service = action_part[start:end]
                if 'keyword="' in action_part:
                    start = action_part.find('keyword="') + 9
                    end = action_part.find('"', start)
                    keyword = action_part[start:end]
                observation = get_business_logs(service=service, keyword=keyword)

            # 打印 Observation
            print(f"Observation: {observation}\n")

            # 加入对话历史
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Observation: {observation}"})

        else:
            print("未找到有效的 Action，结束排查\n")
            break

    if round_count >= max_rounds:
        print("===== 达到最大轮次，结束排查 =====")


# ==============================================
# 运行 Agent
# ==============================================
if __name__ == "__main__":
    # 模拟线上告警
    alarm = "订单服务接口超时，服务响应慢，部分用户报错504"

    # 启动经典 ReAct 模式
    react_agent_explicit(alarm)

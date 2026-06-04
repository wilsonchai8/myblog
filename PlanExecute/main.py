from planner import make_plan
from executor import Executor
from analyzer import analyze

user_input = "订单服务大量 504"

# Step1:
# LLM 制定计划
plan = make_plan(user_input)

# Step2:
# 执行计划
executor = Executor()

observations = executor.run(plan)

# Step3:
# LLM 分析结果
result = analyze(user_input, observations)

print("\n========== 最终结论 ==========")
print(result)
import inspect
import tools


def get_tools():
    """自动从 tools 模块获取所有工具函数"""
    tool_dict = {}
    for name, func in inspect.getmembers(tools, inspect.isfunction):
        if not name.startswith('_'):
            tool_dict[name] = func
    return tool_dict


TOOLS = get_tools()


class Executor:

    def run(self, plan):

        observations = []

        for task in plan:

            tool_name = task["tool"]
            args = task["args"]

            print(f"\n执行: {tool_name} \n参数: {args}", )

            result = TOOLS[tool_name](**args)

            print("结果:")
            print(result)

            observations.append({
                "step": task["step"],
                "tool": tool_name,
                "result": result
            })

        return observations

# 可用工具清单

排障过程中可以调用的脚本工具。

## scripts/get_mysql_state

查询 MySQL 连接状态和指标。

**用途：**
- 验证数据库连通性
- 获取连接数、线程数等指标
- 检查数据库实例健康状态

**使用方式：**
```bash
./scripts/get_mysql_state [host] [port]
```

**参数：**
- `host`（可选）` - 数据库地址，默认 10.21.4.15
- `port`（可选）` - 数据库端口，默认 3306

**输出示例：**
```json
{
  "host": "10.21.4.15",
  "port": 3306,
  "status": "unreachable",
  "error": "dial tcp 10.21.4.15:3306: i/o timeout",
  "suggestions": [...]
}
```

**返回字段说明：**
- `status`: 连接状态（reachable/unreachable）
- `connection_attempts`: 连接尝试记录
- `metrics`: MySQL 指标（threads_connected, connections 等）
- `error`: 错误信息（如有）
- `suggestions`: 建议检查项

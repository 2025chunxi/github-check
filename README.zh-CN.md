# github-credibility-check

用于基于证据评估 GitHub 仓库可信度和实际采用风险的 Codex Skill。

> 当前状态：`v0.1.0-beta`。证据采集、评分和校准工作流已经测试；启发式结论
> 仍然只是辅助决策，不是操纵或安全性的证明。

[English](README.md)

## 主要能力

- 采集仓库、提交、贡献者、Release、Tag、代码树、测试、CI、许可证、Issue/PR
  和软件包注册表证据。
- 支持 `quick`、`standard` 和 `deep` 三种审计模式。
- 将仓库可信度与实际采用风险分开。
- 评估 Star 完整性、声明可验证性、代码实质、社区实质、营销与实现、商业冲突。
- A=1 或 B=1 严重覆盖规则必须提供直接证据和准确原文。
- 使用固定 commit 的校准案例，并通过负面对照避免错误认定“奖励换 Star”。
- 输出确定性的 JSON 和 Markdown 报告，明确标注证据边界。

## 安装

从最新 GitHub Release 下载 `github-credibility-check.skill`，将归档中的
`github-credibility-check` 顶层目录安装到 `$CODEX_HOME/skills` 或
`~/.codex/skills`，然后新建 Codex 任务以重新加载元数据。

GitHub 安装器可使用源码路径 `skill/github-credibility-check`。

## 构建与验证

要求 Python 3.11 或更高版本。PyYAML 仅供仓库发布工具使用。

```bash
python -m pip install -r requirements.txt
python scripts/build_release.py
```

输出：`dist/github-credibility-check.skill`。

构建会运行评分回归测试、严格 Skill 校验、8 个校准案例验证、归档检查，以及
覆盖整个仓库的密钥、PII、个人路径和归档安全扫描。CI 不执行实时 GitHub 请求。

## 认证与隐私

`GITHUB_TOKEN` 是可选环境变量，用于提高 API 限额。它只会写入请求头，不会
进入报告。不要把 token 放进命令参数、评分卡、测试夹具或 Issue。

## 证据边界

- Star 异常和比例本身不能证明购买或自动化 Star。
- 可信仓库仍可能存在维护、安全、许可证或兼容风险。
- 缺少外部证据时必须降低置信度，不能静默编造。
- 生产采用前仍需执行最新安全和兼容性检查。

## 许可证

MIT，详见 [LICENSE](LICENSE)。

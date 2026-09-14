# skill-auditor — Pre-Marketplace QA for Agent Skills

[![CI](https://github.com/Hahaknight/skill-auditor/actions/workflows/ci.yml/badge.svg)](https://github.com/Hahaknight/skill-auditor/actions/workflows/ci.yml)
[![self-audit: SHIPPABLE](https://img.shields.io/badge/self--audit-98%2F100%20SHIPPABLE-brightgreen)](#测试与验证)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 在你把 skill 上架到付费市场（Agensi / Fleece / ClaudeSkills…）之前，
> 抓出会导致**拒审、退款、账号风险**的问题。证据驱动，拒绝模板话术。

简体中文

## 为什么存在

注入话术、硬编码密钥、危险 shell 命令，是 skill 在市场上架扫描中被拒的高频原因——付费市场普遍在上架流程加了安全扫描，过不了就上不了架；带着问题上线，等来的是退款和差评。

skill-auditor 把上架前质检做成一条命令。

## 快速开始

```bash
git clone https://github.com/Hahaknight/skill-auditor.git
python skill-auditor/scripts/audit_skill.py --path /path/to/your-skill
```

## 12 项检查

| # | 检查 | 抓什么 |
|---|---|---|
| S1 | 提示注入模式 | "ignore previous instructions" 等劫持话术 |
| S2 | 硬编码密钥 | sk-/AKIA/ghp_/xox 形态 token |
| S3 | 危险 shell | 递归强删、远程脚本管道、提权 |
| S4 | 外传端点 | collector 服务、webhook 式上传 URL |
| S5 | 混淆 | base64 eval、exec blob |
| Q1 | Frontmatter 合规 | name/description 规则（长度、保留字） |
| Q2 | 触发语义 | description 是否说明"何时用"——弱触发=退款之源 |
| Q3 | 体量 | SKILL.md >500 行 = token 成本投诉 |
| Q4 | 引用完整性 | 断链文件=工单之源 |
| Q5 | 依赖可解析 | 声明了 bins 却装不上="跑不起来"退款 |
| P1 | 出品证明 | 无 LICENSE = 下架/IP 风险 |
| P2 | 填充密度 | TODO/placeholder 密度——"半成品感"量化 |

## 评分与判定

- CRITICAL（S1-S5 命中）= 直接 DO NOT LIST
- 85+ = SHIPPABLE；70-84 = FIX MINOR；<70 = DO NOT LIST

## 测试与验证

`tests/` 内置 24 项 pytest 用例：单元级（frontmatter 规则、五类特征的正/负例、大小写敏感性、证据定位）+ 端到端金样本对照：

| 样本 | 分数 | 判定 |
|---|---|---|
| `tests/fixtures/poisoned-skill`（每类缺陷各埋一处） | 0/100 | DO NOT LIST ✅ |
| `tests/fixtures/good-skill`（干净技能） | ≥85 | SHIPPABLE ✅ |
| `tests/fixtures/exempt-skill`（auditignore 豁免语义） | ≥85 | SHIPPABLE ✅ |
| skill-auditor 自身（CI `self-audit` 任务） | 98/100 | SHIPPABLE ✅ |

```bash
pip install pytest && pytest tests/ -v      # 测试套件
python scripts/audit_skill.py --path .      # 自审计（CI 每次运行强制 SHIPPABLE）
```

## 已知边界

**能发现**：文本形态的注入话术、密钥/令牌样式、危险命令模式、外传端点样式、结构缺陷（frontmatter / 断链 / 体量 / 依赖声明）——即市场扫描的主审维度。

**不能保证**：语义级注入（不含特征词的诱导）、运行时行为、加密或分片外传。本工具是形态学静态扫描：每条 finding 都带证据（文件/行/命中片段），报告前请人工核对、杀掉误报——它给的是"哪里值得看"，不是终审判决。

- 特征定义文件可经包内 `auditignore` 豁免（安全工具自带特征码的行业标准做法）
- 密钥检测是形态学匹配，建议配合 gitleaks 做深度扫描

## License

MIT © 2026 Hahaknight

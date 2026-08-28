# skill-auditor — Pre-Marketplace QA for Agent Skills

> 在你把 skill 上架到付费市场（Agensi / Fleece / ClaudeSkills…）之前，
> 抓出会导致**拒审、退款、账号风险**的问题。证据驱动，拒绝模板话术。

[English](README.en.md) · 简体中文

## 为什么存在

2026 年一项对 22,511 个公开 skill 的安全审计发现：**平均每个 skill 有 6.3 个问题**（注入漏洞、暴露密钥、危险 shell 命令）。付费市场全部加了安全扫描（Agensi 8 项），过不了就上不了架；带着问题上线，等来的是退款和差评。

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

## 实测证据

三组对照样本全部符合预期（完整输出见 [audit/golden-verification](../audit/golden-verification-skill-auditor.txt)）：

| 样本 | 分数 | 判定 |
|---|---|---|
| 投毒样本（6 类缺陷注入） | 0/100 | DO NOT LIST ✅ |
| 工业级成熟技能（30 文件/8300 行） | 98/100 | SHIPPABLE ✅ |
| skill-auditor 自身 | 97/100 | SHIPPABLE ✅ |

## 已知边界

- 静态扫描：不能替代动态沙箱执行，但覆盖市场扫描的主审维度
- 特征定义文件可经包内 `auditignore` 豁免（安全工具自带特征码的行业标准做法）
- 密钥检测是形态学匹配，建议配合 gitleaks 做深度扫描

## License

MIT © 2026 Hahaknight

# 实战案例：用 skill-auditor 首扫 digital-employee-pack

> 一个真实技能包的完整审查记录：输入 → 发现 → 修复 → 复扫验证。
> 审查对象为作者自己的另一个仓库 [digital-employee-pack](https://github.com/Hahaknight/digital-employee-pack)（中文办公技能包：周报/会议纪要/PPT 大纲），避免无上下文评判他人项目。

## 1. 输入

- 仓库：`Hahaknight/digital-employee-pack` @ main（2026-09-15 快照）
- 审查范围：`free-sample/skills/` 下三个技能包——`meeting-minutes`、`ppt-outline`、`weekly-report`
- 环境：Python 3.11，skill-auditor master（CI 同版本）

## 2. 命令

```bash
git clone https://github.com/Hahaknight/digital-employee-pack.git
cd digital-employee-pack
for s in meeting-minutes ppt-outline weekly-report; do
  python skill-auditor/scripts/audit_skill.py --path free-sample/skills/$s --json report-$s.json
done
```

## 3. 原始报告（首扫）

| 技能 | 得分 | 判定 | S1-S5 安全项 | 问题 |
|---|---|---|---|---|
| meeting-minutes | 97/100 | SHIPPABLE | 全 PASS | **P1 WARN**：包内无 LICENSE |
| ppt-outline | 95/100 | SHIPPABLE | 全 PASS | P1 WARN + **P2 FAIL**：`XXX` 占位符（6.29/千词 > 5 阈值） |
| weekly-report | 95/100 | SHIPPABLE | 全 PASS | P1 WARN + **P2 FAIL**：`XXX` 占位符（6.21/千词） |

命中证据（P2，替换为可读占位前的原文）：

```
weekly-report/SKILL.md:26: - 【完成】XXX：具体结果 + 数据（如：接口响应从 800ms 降到 200ms）
ppt-outline/SKILL.md:26: - 讲稿提示：这页口头补充 XXX
```

## 4. 修复 diff

```diff
--- a/free-sample/skills/weekly-report/SKILL.md
- - 【完成】XXX：具体结果 + 数据（如：接口响应从 800ms 降到 200ms）
+ - 【完成】〔一句话成果〕：具体结果 + 数据（如：接口响应从 800ms 降到 200ms）

--- a/free-sample/skills/ppt-outline/SKILL.md
- - 讲稿提示：这页口头补充 XXX
+ - 讲稿提示：这页口头补充关键数据与来源

新增文件: LICENSE（仓库根，MIT）
新增文件: free-sample/skills/{meeting-minutes,ppt-outline,weekly-report}/LICENSE（每包一份——市场上架按包分发，P1 按包内判定）
```

## 5. 复扫结果

| 技能 | 首扫 | 复扫 | 变化 |
|---|---|---|---|
| meeting-minutes | 97 | **98** | P1 WARN → PASS |
| ppt-outline | 95 | **98** | P1 WARN → PASS，P2 FAIL → PASS |
| weekly-report | 95 | **98** | P1 WARN → PASS，P2 FAIL → PASS |

剩余 2 分为 Q5 N/A（纯提示词技能无二进制依赖，属设计使然）。

## 结论与边界

- 三个技能安全维度（注入/密钥/危险命令/外传/混淆）首扫即全绿——这类纯文档技能的主要风险确实集中在**出品证明（License）与"半成品感"（占位符）**，与 P1/P2 检查的设计判断一致
- P2 对模板类技能天然偏严：模板占位符是该品类的固有写法，但买家视角"XXX=没写完"成立，改用〔中文填写指引〕是零成本改进
- 本次为静态扫描结论；动态行为未测（本品类为纯提示词，无动态面）

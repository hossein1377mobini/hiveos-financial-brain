# درخت محتوایی — Agent Learning

> مسیر: `docs/06-Research/agents/`
| **آخرین به‌روزرسانی:** 2026-07-16 (فاز محتوا تکمیل شد)

## ساختار

```
agents/
├── _inbox/                  ← ورودی خام — هر چی داری اینجا بریز
├── _index.md                ← این فایل — درخت محتوایی + وضعیت
│
├── 01-Fundamentals/         ← مبانی ایجنت‌ها
│   ├── 01-what-is-an-agent.md
│   ├── 02-agent-architectures.md
│   ├── 03-reasoning-and-planning.md
│   └── 04-tools-and-function-calling.md
│
├── 02-Multi-Agent-Systems/  ← سیستم‌های چندعامله
│   ├── 01-orchestration-patterns.md
│   ├── 02-communication-and-coordination.md
│   ├── 03-task-decomposition.md
│   └── 04-human-in-the-loop.md
│
├── 03-Frameworks/           ← فریمورک‌ها و ابزارها
│   ├── 01-langchain-langgraph.md
│   ├── 02-autogen-crewai.md
│   ├── 03-claude-code-codex.md
│   └── 04-custom-agent-frameworks.md
│
├── 04-Advanced-Patterns/    ← الگوهای پیشرفته
│   ├── 01-reflection-and-self-correction.md
│   ├── 02-multi-step-reasoning.md
│   ├── 03-memory-systems.md
│   └── 04-evaluation-and-testing.md
│
├── 05-Use-Cases/            ← کاربردها
│   ├── 01-coding-agents.md
│   ├── 02-research-agents.md
│   ├── 03-analytics-agents.md
│   └── 04-automation-agents.md
│
└── 06-HiveOS-Specific/      ← مخصوص HiveOS
    ├── 01-domain-architecture.md
    ├── 02-flow-engine-deep-dive.md
    ├── 03-agent-blueprint-design.md
    └── 04-adding-new-domains.md
```

## وضعیت فایل‌ها

| پوشه | وضعیت | توضیح |
|------|--------|-------|
|| `_inbox/` | 🟢 باز | هر چی داری بنداز اینجا |
|| `01-Fundamentals/` | 🟢 کامل | ✅ all 4 files |
|| `02-Multi-Agent-Systems/` | 🟢 کامل | ✅ all 4 files |
|| `03-Frameworks/` | 🟢 کامل | ✅ all 4 files |
|| `04-Advanced-Patterns/` | 🟢 ۳ از ۴ | ✅ reflection · ✅ multi-step-reasoning · ✅ memory · ✅ evaluation |
|| `05-Use-Cases/` | 🟢 کامل | ✅ all 4 files |
|| `06-HiveOS-Specific/` | 🟢 کامل | ✅ all 4 files |

## توضیح دسته‌بندی

| دسته | محتوا |
|------|--------|
| **01-Fundamentals** | مفهوم Agent، معماری‌ها (ReAct, Plan-and-Execute, ...)، reasoning، planning، tool use |
| **02-Multi-Agent-Systems** | الگوهای orchestration (مدیر, ناظر, peer-to-peer)، communication بین agentها، task decomposition |
| **03-Frameworks** | LangChain, LangGraph, AutoGen, CrewAI, Claude Code, Codex — نحوه کار، مقایسه |
| **04-Advanced-Patterns** | Reflection, self-correction, memory systems (short-term/long-term), evaluation |
| **05-Use-Cases** | agentهای کدنویسی، تحقیق، تحلیل، اتوماسیون — case study |
| **06-HiveOS-Specific** | معماری domain‌ها، flow engine، blueprint design، اضافه کردن domain جدید |

## نحوه کار

1. تو `_inbox/` هر چی داری — لینک، فایل، یادداشت — بنداز
2. من میام هر چی توی `_inbox/` هست رو می‌خونم، دسته‌بندی می‌کنم و می‌ریزم توی پوشه‌های مرتبط
3. اگه خودم سرچ کنم، مستقیم توی پوشه‌های درست می‌زارم
4. بعد از پردازش، محتوای `_inbox/` بایگانی می‌شه

## آمار نهایی فاز محتوا

| دسته | تعداد فایل | حجم کل |
|------|-----------|--------|
| `01-Fundamentals/` | ۴ فایل | ~۶۵KB |
| `02-Multi-Agent-Systems/` | ۴ فایل | ~۶۰KB |
| `03-Frameworks/` | ۴ فایل | ~۷۵KB |
| `04-Advanced-Patterns/` | ۴ فایل | ~۶۰KB |
| `05-Use-Cases/` | ۴ فایل | ~۱۵KB |
| `06-HiveOS-Specific/` | ۴ فایل | ~۲۵KB |
| **جمع کل** | **۲۴ فایل** | **~۳۰۰KB** |

> **✅ فاز محتوا (Phase Content — Agent Learning) تکمیل شد.**  
> هر ۶ دسته پر شده‌اند. محتوا شامل مبانی، معماری، سیستم‌های چندعاملی، فریمورک‌ها، الگوهای پیشرفته، کاربردها و مخصوص HiveOS است.
>
> **قدم بعدی:** می‌توانیم به سراغ Phase بعدی برویم یا محتوای موجود را در قالب Domainهای HiveOS پیاده‌سازی کنیم.

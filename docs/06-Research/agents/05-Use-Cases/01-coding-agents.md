# عامل‌های کدنویسی — Coding Agents (کاربردها و سناریوها)

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶

---

## ۱. مقدمه

**عامل‌های کدنویسی (Coding Agents)** یکی از موفق‌ترین کاربردهای AI Agentها هستند. این عامل‌ها می‌توانند کد بنویسند، دیباگ کنند، ریفکتور کنند، تست بنویسند و حتی Pull Request باز کنند.

| ابزار | نوع | قابلیت‌ها |
|-------|-----|-----------|
| **Claude Code (Anthropic)** | CLI Agent | کدنویسی، ویرایش، دیباگ، PR |
| **Codex CLI (OpenAI)** | CLI Agent | کدنویسی در Sandbox، auto-edit |
| **GitHub Copilot** | IDE Plugin | تکمیل کد، چت |
| **Cursor** | IDE | ویرایش هوشمند، agent mode |
| **Devin** | Platform |项目管理 مستقل |
| **Windsurf (Codeium)** | IDE | Cascade agent |

**سناریوهای کلیدی:** توسعه feature جدید، رفع باگ، بازنویسی کد، نوشتن تست، Code Review

---

## ۲. معماری یک Coding Agent

```text
┌──────────────────────────────────────┐
│         Coding Agent                  │
│                                       │
│  ┌────────┐  ┌────────┐  ┌────────┐  │
│  │ درک     │  │ برنامه │  │ کدنویسی│  │
│  │ مسئله   │──▶│ ریزی   │──▶│        │  │
│  └────────┘  └────────┘  └────────┘  │
│       │          │           │        │
│       ▼          ▼           ▼        │
│  ┌────────┐  ┌────────┐  ┌────────┐  │
│  │ تحلیل   │  │ انتخاب  │  │ نوشتن  │  │
│  │ نیازمندی│  │ رویکرد  │  │ کد     │  │
│  └────────┘  └────────┘  └────────┘  │
│                                       │
│  ┌────────┐  ┌────────┐  ┌────────┐  │
│  │ تست    │──▶│ دیباگ  │──▶│ commit │  │
│  └────────┘  └────────┘  └────────┘  │
│                                       │
│  ابزارها: [Filesystem] [Terminal]    │
│           [Git] [Browser] [Debugger] │
└──────────────────────────────────────┘
```

---

## ۳. سناریوهای کاربردی

| سناریو | عامل | توضیح |
|--------|------|-------|
| **توسعه Feature جدید** | Claude Code | از توضیحات تا کد کامل |
| **رفع Bug** | Codex CLI | دیباگ + رفع + تست |
| **Code Review** | Code Review Agent | بررسی خودکار + پیشنهاد |
| **Refactoring** | Refactor Agent | بازنویسی با حفظ رفتار |
| **نوشتن Test** | Test Agent | تولید تست واحد + یکپارچه‌سازی |
| **Migration** | Migration Agent | ارتقای نسخه، تغییر فریمورک |

---

## ۴. Coding Agents در HiveOS

HiveOS می‌تواند از Coding Agentها به عنوان **Worker Agent** در یک Flow استفاده کند:

```yaml
# HiveOS flow با coding agent
name: auto-code-review
orchestrator: mothership
steps:
  - agent: code-reviewer
    model: claude-sonnet-4
    task: "بررسی Pull Request #42"
    tools: [git-diff, filesystem, lint]
  - agent: test-writer
    depends_on: [code-reviewer]
    task: "نوشتن تست برای تغییرات"
    tools: [pytest, git]
  - agent: pr-updater
    depends_on: [test-writer]
    task: "بروزرسانی PR با نتایج"
```

---

**فایل‌های مرتبط:** `docs/06-Research/agents/03-Frameworks/03-claude-code-codex.md`

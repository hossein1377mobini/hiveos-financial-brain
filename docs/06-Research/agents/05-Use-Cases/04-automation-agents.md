# عامل‌های اتوماسیون — Automation Agents (کاربردها و سناریوها)

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶

---

## ۱. مقدمه

**عامل‌های اتوماسیون (Automation Agents)** وظایف تکراری و زمان‌بر را به صورت خودکار انجام می‌دهند. برخلاف اسکریپت‌های سنتی، این عامل‌ها **تطبیق‌پذیر (adaptive)** هستند — اگر شرایط تغییر کند، خود را تطبیق می‌دهند.

### تفاوت با اتوماسیون سنتی:

| اتوماسیون سنتی (RPA) | Automation Agent |
|---------------------|------------------|
| بر اساس قوانین ثابت (Rule-based) | بر اساس استدلال (Reasoning-based) |
| اگر صفحه تغییر کند، می‌شکند | خود را با تغییرات تطبیق می‌دهد |
| فقط کارهای تکراری | کارهای پیچیده + استثناها |
| نیاز به تعریف دقیق هر مرحله | هدف را می‌گویی، خودش مسیر را پیدا می‌کند |

---

## ۲. انواع Automation Agents

| نوع | مثال | ابزارها |
|-----|------|---------|
| **Process Automation** | پردازش خودکار فاکتورها | PDF Reader, Email, Excel |
| **Workflow Automation** | هماهنگی بین چند سیستم | API, Webhook, Database |
| **Data Entry** | ورود خودکار داده | OCR, Form Filler |
| **Monitoring** | نظارت و هشدار | Web Scraper, API Poller |
| **Reporting** | تولید گزارش دوره‌ای | BI Tools, Email Sender |

---

## ۳. معماری Automation Agent

```text
┌──────────────────────────────────────┐
│       Automation Agent                │
│                                       │
│  Trigger → [درک وضعیت] → [تصمیم] → [اقدام] │
│                                       │
│  Triggers:                            │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │زمان‌بند│ │رویداد│ │درخواست│          │
│  │Cron  │ │Event │ │API   │          │
│  └──────┘ └──────┘ └──────┘          │
└──────────────────────────────────────┘
```

### مثال: اتوماسیون پردازش فاکتور

```yaml
name: invoice-processor
trigger:
  type: email
  condition: "موضوع شامل 'فاکتور'"
steps:
  - agent: document-reader
    task: "خواندن PDF فاکتور"
  - agent: data-extractor
    task: "استخراج مبالغ، تاریخ، طرف حساب"
  - agent: validator
    task: "اعتبارسنجی با سفارش مرتبط"
  - agent: approver
    task: "HITL — تأیید انسانی برای مبالغ > ۱۰۰ میلیون"
  - agent: bookkeeper
    task: "ثبت در دفاتر حسابداری"
```

---

## ۴. Automation Agents در HiveOS

HiveOS از Automation Agentها برای **پردازش خودکار محتوا** استفاده می‌کند:

```python
# HiveOS — Cron-based Automation Agent
from hiveos.cron import CronJob

# هر شب ساعت ۲ بامداد، محتوای _inbox را پردازش کن
job = CronJob(
    name="inbox-processor",
    schedule="0 2 * * *",
    agent="content-processor",
    task="پردازش فایل‌های جدید در _inbox و دسته‌بندی خودکار"
)
```

**سناریوهای اتوماسیون در HiveOS:**
- پردازش خودکار فاکتورها و اسناد مالی
- تولید گزارش‌های دوره‌ای
- هماهنگی بین عامل‌های مختلف
- پشتیبان‌گیری خودکار

---

**فایل‌های مرتبط:**
- `docs/06-Research/agents/02-Multi-Agent-Systems/01-orchestration-patterns.md`
- `src/hiveos/playground/playground.py`

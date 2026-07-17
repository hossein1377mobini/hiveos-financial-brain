# طراحی Blueprint عامل‌ها در HiveOS — Agent Blueprint Design

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **فایل‌های مرتبط:** `src/hiveos/agent/` · `docs/02-Architecture/02-agent-blueprints.md`

---

## ۱. Agent Blueprint چیست؟

یک **Agent Blueprint** (طرحوارهٔ عامل) تعریف‌کنندهٔ **نوع** و **قابلیت‌های** یک عامل است. مثل یک **فرم استخدام** است — مشخص می‌کند عامل چه نقشی دارد، به چه ابزارهایی دسترسی دارد، و چطور باید رفتار کند.

### ساختار یک Blueprint:

```yaml
# نمونه Blueprint برای تحلیل‌گر مالی
id: financial-analyst
version: 1.0.0
domain: accounting

metadata:
  label: "تحلیل‌گر مالی"
  description: "تحلیل صورت‌های مالی و محاسبه نسبت‌ها"
  author: HiveOS Team
  icon: 📊

agent:
  model: claude-sonnet-4
  temperature: 0.3        # دمای پایین برای دقت بالا
  system_prompt: |
    شما یک تحلیل‌گر مالی حرفه‌ای هستید.
    وظیفه شما تحلیل صورت‌های مالی و استخراج نسبت‌ها است.
    همیشه اعداد را با دقت محاسبه کنید و منابع را ذکر کنید.

tools:
  - id: financial-statement-reader
    required: true
  - id: ratio-analyzer
    required: true
  - id: web-search
    required: false
  - id: pdf-generator
    required: false

memory:
  short_term_limit: 20    # حداکثر ۲۰ پیام در حافظهٔ کوتاه‌مدت
  long_term: true         # حافظهٔ بلندمدت فعال
  persistent_keys:        # کلیدهایی که بین جلسات حفظ شوند
    - last_analysis_date
    - company_portfolio

limits:
  max_steps: 25
  max_tool_calls_per_step: 3
  timeout_seconds: 300

output:
  format: markdown        # فرمت پیش‌فرض خروجی
  schema:                 # اسکیما برای خروجی ساختاریافته
    type: object
    properties:
      company_name: { type: string }
      ratios: { type: array }
      recommendation: { type: string }
```

---

## ۲. انواع Blueprint

HiveOS پنج نوع Blueprint دارد:

| نوع | توضیح | مثال |
|-----|-------|------|
| **Worker** | عامل اجرایی — کار اصلی را انجام می‌دهد | data-collector, calculator |
| **Supervisor** | عامل ارشد — برنامه‌ریزی و تخصیص | orchestrator, planner |
| **Reviewer** | عامل بازبین — خروجی‌ها را بررسی می‌کند | quality-checker, validator |
| **Service** | عامل خدماتی — قابلیت مشترک ارائه می‌دهد | search-service, auth-service |
| **Support** | عامل نظارتی — سلامت سیستم را رصد می‌کند | monitor, logger |

---

## ۳. مثال‌های Blueprint واقعی

### ۳.۱ Worker Agent — جمع‌آوری‌کنندهٔ داده

```yaml
id: data-collector
type: worker
domain: general

agent:
  model: gpt-4o-mini
  temperature: 0.1       # دمای بسیار پایین — دقت حرف اول را می‌زند
  system_prompt: |
    شما یک جمع‌آوری‌کنندهٔ داده هستید.
    وظیفه شما: یافتن و استخراج اطلاعات دقیق از منابع مشخص.
    همیشه منبع اطلاعات را ذکر کنید.

tools:
  - web-search
  - pdf-reader
  - api-client
```

### ۳.۲ Supervisor Agent — ارکستراتور

```yaml
id: orchestrator
type: supervisor
domain: general

agent:
  model: claude-sonnet-4
  temperature: 0.5
  system_prompt: |
    شما یک مدیر ارشد (Supervisor) هستید.
    وظیفه شما:
    ۱. تحلیل وظیفهٔ ورودی
    ۲. تجزیه به زیروظایف
    ۳. تخصیص به عامل‌های مناسب
    ۴. پیگیری و جمع‌آوری نتایج
    ۵. گزارش نهایی

capabilities:
  - task-decomposition
  - agent-dispatch
  - result-aggregation
  - error-handling
```

---

## ۴. Blueprint Registration

Blueprintها در **Domain Registry** ثبت می‌شوند:

```python
from hiveos.domain import DomainRegistry
from hiveos.agent import AgentBlueprint

registry = DomainRegistry(storage=storage)

# ثبت Blueprint جدید
blueprint = AgentBlueprint.from_yaml("""
id: payroll-calculator
type: worker
domain: accounting
agent:
  model: claude-sonnet-4
  temperature: 0.1
  system_prompt: |
    شما متخصص محاسبه حقوق و دستمزد هستید.
    با قوانین کار ایران و تأمین اجتماعی آشنا هستید.
tools:
  - salary-calculator
  - tax-table
  - insurance-table
""")

registry.register_blueprint(blueprint)

# جستجوی Blueprint
results = registry.search_blueprints(
    domain="accounting",
    type="worker"
)
```

---

## ۵. Blueprint در عمل

```python
# اسپاون کردن عامل از روی Blueprint
from hiveos.agent import AgentFactory

factory = AgentFactory(registry=registry)

# ساخت عامل جدید
agent = factory.create_agent(
    blueprint_id="financial-analyst",
    config_overrides={
        "temperature": 0.2  # override
    }
)

# اجرا
result = await agent.run("تحلیل صورت‌های مالی شرکت X برای سال ۱۴۰۴")
```

---

**فایل‌های مرتبط:**
- `docs/02-Architecture/02-agent-blueprints.md` — مستندات معماری
- `tests/test_agent.py` — تست‌های Agent

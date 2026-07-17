# Flow Engine در HiveOS — معماری و عملکرد

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **فایل‌های مرتبط:** `src/hiveos/playground/playground.py` · `src/hiveos/flow/` · `tests/test_playground.py`

---

## ۱. مقدمه: Flow چیست؟

در HiveOS، یک **Flow** یک **گردش کار چندمرحله‌ای (multi-step workflow)** است که تعیین می‌کند:

- **کدام عامل‌ها** در چه **ترتیبی** اجرا شوند
- چه **ابزارهایی** در دسترس باشند
- وابستگی‌ها و **ارتباط** بین مراحل چگونه باشد
- خروجی هر مرحله به کدام مرحلهٔ بعد **برود**

---

## ۲. انواع Flow

| نوع | توضیح | مثال |
|-----|-------|------|
| **Sequential** | مراحل پشت‌سرهم | تحقیق → تحلیل → نوشتن |
| **Parallel** | مراحل هم‌زمان | جستجوی هم‌زمان در چند منبع |
| **DAG** | گراف با وابستگی‌های پیچیده | تحلیل مالی با چند ورودی |
| **Supervisor** | عامل ارشد زیروظایف را تخصیص می‌دهد | تحلیل اعتباری بانکی |
| **Conditional** | مسیر بر اساس شرط تغییر می‌کند | اگر مبلغ > threshold → HITL |

### مثال Flow ساده:

```yaml
name: simple-report
orchestrator: sequential
steps:
  - id: research
    agent: research-agent
    task: "تحقیق درباره موضوع"
  
  - id: analyze
    agent: analyst-agent
    task: "تحلیل نتایج تحقیق"
    depends_on: [research]
  
  - id: write
    agent: writer-agent
    task: "نوشتن گزارش نهایی"
    depends_on: [analyze]
```

---

## ۳. معماری Flow Engine

```text
┌────────────────────────────────────────────────┐
│            Flow Engine                          │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Validate │─▶│  Plan   │─▶│ Execute  │      │
│  │ (YAML)  │  │ (DAG)   │  │ (Steps)  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│       │            │            │               │
│       ▼            ▼            ▼               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Syntax   │  │ Topo.   │  │ Agent    │      │
│  │ Check    │  │ Sort     │  │ Dispatch │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                │
│  ┌──────────────────────────────────────┐      │
│  │  State Management (StorageEngine)    │      │
│  └──────────────────────────────────────┘      │
│                                                │
│  ┌──────────────────────────────────────┐      │
│  │  Brain — Event Stream + Trace       │      │
│  └──────────────────────────────────────┘      │
└────────────────────────────────────────────────┘
```

---

## ۴. پیاده‌سازی در کد

### ۴.۱ تعریف Flow

```python
from hiveos.playground import PlaygroundEngine

engine = PlaygroundEngine()

flow_yaml = """
name: tax-calculation
orchestrator: dag
steps:
  - id: get-salary
    agent: data-collector
    task: "دریافت اطلاعات حقوق"
    tools: [hr-system-api]

  - id: calc-tax
    agent: tax-calculator
    task: "محاسبه مالیات حقوق ۱۴۰۴"
    depends_on: [get-salary]
    tools: [tax-table-1404, deduction-calc]

  - id: calc-insurance
    agent: insurance-calc
    task: "محاسبه حق بیمه تأمین اجتماعی"
    depends_on: [get-salary]
    tools: [insurance-table-1404]

  - id: generate-payslip
    agent: report-writer
    task: "تولید فیش حقوقی"
    depends_on: [calc-tax, calc-insurance]
    tools: [payslip-template]
"""

# اعتبارسنجی
validation = engine.validate_flow(flow_yaml)
assert validation["valid"] == True

# اجرا
result = engine.run_flow(flow_yaml, {
    "employee_id": "EMP-12345",
    "month": "فروردین",
    "year": 1404
})
```

### ۴.۲ Flow Library

HiveOS یک **Flow Library** برای ذخیره و بازیابی Flowها دارد:

```python
from hiveos.playground.flow_library import FlowLibrary

library = FlowLibrary(storage=storage)

# ذخیره Flow
library.save_flow(
    name="monthly-tax-report",
    flow=flow_yaml,
    tags=["حسابداری", "مالیات", "گزارش"],
    description="تولید گزارش مالیات ماهانه"
)

# لیست Flowهای ذخیره‌شده
flows = library.list_flows(tags=["حسابداری"])

# بارگذاری Flow
flow = library.load_flow("monthly-tax-report")

# به‌روزرسانی
library.update_flow("monthly-tax-report", flow=new_version)

# حذف
library.delete_flow("old-flow-name")
```

---

## ۵. جریان داده بین مراحل (Data Flow)

خروجی هر مرحله از طریق **متغیرهای زمینه (Context Variables)** به مرحلهٔ بعد منتقل می‌شود:

```yaml
steps:
  - id: step-1
    agent: agent-a
    output_var: data_a        # ذخیره خروجی در data_a
  
  - id: step-2
    agent: agent-b
    depends_on: [step-1]
    input: ${data_a}          # ورودی از data_a
    output_var: data_b

  - id: step-3
    agent: agent-c
    depends_on: [step-1, step-2]
    input:
      source_a: ${data_a}
      source_b: ${data_b}
```

---

## ۶. رویدادها و رهگیری (Events & Tracing)

هر اجرای Flow توسط **Brain Event Stream** رهگیری می‌شود:

```python
# رویدادهای تولیدشده حین اجرای یک Flow
events = [
    {"type": "flow.started", "flow": "tax-calculation", "timestamp": "..."},
    {"type": "step.started", "step": "get-salary", "agent": "data-collector"},
    {"type": "step.completed", "step": "get-salary", "duration_ms": 1500},
    {"type": "step.started", "step": "calc-tax", "agent": "tax-calculator"},
    {"type": "tool.called", "tool": "tax-table-1404", "args": {"salary": 50000000}},
    {"type": "step.completed", "step": "calc-tax", "result": {"tax": 5000000}},
    {"type": "flow.completed", "flow": "tax-calculation", "total_duration_ms": 8500}
]
```

---

## ۷. Flow Templates

HiveOS دارای قالب‌های از پیش تعریف‌شده برای وظایف رایج است:

```python
# لیست قالب‌های موجود
templates = engine.list_templates()

# دریافت قالب
template = engine.get_template("financial-report")

# شخصی‌سازی قالب
customized = engine.customize_template(
    template_id="financial-report",
    overrides={
        "agent": "premium-analyst",
        "tools": ["advanced-ratio-analyzer"]
    }
)
```

---

## ۸. Flow CLI

```bash
# اعتبارسنجی Flow
hive flow validate prototype/tax-flow.yml

# اجرای Flow
hive flow run prototype/tax-flow.yml

# لیست Flowهای ذخیره‌شده
hive flow list

# مشاهده وضعیت Flow
hive flow state tax-calculation

# پاک کردن وضعیت
hive flow clear-state tax-calculation
```

---

**فایل‌های مرتبط:**
- `src/hiveos/playground/playground.py` — PlaygroundEngine
- `src/hiveos/playground/flow_library.py` — Flow Library
- `tests/test_playground.py` — ۱۴ تست

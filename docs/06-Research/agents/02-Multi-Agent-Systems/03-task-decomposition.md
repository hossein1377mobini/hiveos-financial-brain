# تجزیه وظایف در سیستم‌های چندعاملی — Task Decomposition in Multi-Agent Systems

> **نویسنده:** تیم مستندات HiveOS
> **تاریخ:** جولای ۲۰۲۶
> **منابع:** BabyAGI · HuggingGPT · Microsoft TaskWeaver · AutoGPT · LangGraph Documentation · HiveOS Flow Engine

---

## ۱. مقدمه: چرا تجزیه وظایف حیاتی است؟

یک **عامل هوش مصنوعی (AI Agent)** وقتی با یک وظیفهٔ پیچیده مواجه می‌شود — مثل «یک تحلیل جامع از صورت‌های مالی شرکت X تهیه کن» — نمی‌تواند این کار را یک‌باره انجام دهد. چالش‌ها:

| چالش | توضیح | مشکل در صورت عدم تجزیه |
|------|-------|----------------------|
| **پنجرهٔ زمینه (Context Window)** | LLMها محدودیت token دارند | وظیفه در یک فراخوانی جا نمی‌شود |
| **تخصص‌گرایی (Specialization)** | هر عامل در حوزه‌ای متخصص است | یک عامل از همه چیز سر درمی‌آورد اما هیچ‌کس عمیق نیست |
| **ردیابی (Traceability)** | باید بتوان هر مرحله را ردیابی کرد | جعبه سیاه — نمی‌دانیم چه شد |
| **بازیابی از خطا (Error Recovery)** | خطا در یک مرحله نباید کل کار را خراب کند | شکست آبشاری (cascading failure) |

**Task Decomposition** (تجزیه وظایف) فرایند شکستن یک وظیفهٔ بزرگ به زیروظایف (subtasks) کوچک‌تر، مشخص‌تر و قابل اجراست. این فرایند قلب سیستم‌های چندعاملی است.

> **تشبیه برای مخاطب ایرانی:** مثل یک **مدیر پروژه ساختمانی** است که پروژهٔ ساخت یک برج را به فازهای (فونداسیون، اسکلت، تأسیسات، نما) و هر فاز را به فعالیت‌های روزانه (بتن‌ریزی، جوشکاری، لوله‌کشی) تجزیه می‌کند. هر فعالیت به یک پیمانکار تخصصی سپرده می‌شود.

---

## ۲. سطوح تجزیه (Levels of Decomposition)

تجزیه وظایف در سه سطح انجام می‌شود:

### ۲.۱ سطح استراتژیک (Strategic Level)

تبدیل **هدف (Goal)** به **ماموریت‌ها (Missions)**.

| مؤلفه | مثال |
|-------|------|
| **هدف** | «تحلیل سلامت مالی شرکت X برای سرمایه‌گذاری» |
| **ماموریت ۱** | جمع‌آوری صورت‌های مالی ۳ سال اخیر |
| **ماموریت ۲** | محاسبه نسبت‌های مالی (نقدینگی، سودآوری، اهرمی) |
| **ماموریت ۳** | مقایسه با رقبا و میانگین صنعت |
| **ماموریت ۴** | تولید گزارش نهایی با توصیه سرمایه‌گذاری |

### ۲.۲ سطح تاکتیکی (Tactical Level)

تبدیل هر **ماموریت** به **وظایف (Tasks)** با وابستگی‌های مشخص:

```
ماموریت ۱: جمع‌آوری صورت‌های مالی
├── وظیفه ۱.۱: جستجوی صورت‌های مالی در وب
├── وظیفه ۱.۲: استخراج داده‌های ترازنامه ← وابسته به ۱.۱
├── وظیفه ۱.۳: استخراج داده‌های صورت سود و زیان ← وابسته به ۱.۱
├── وظیفه ۱.۴: استخراج داده‌های جریان نقدی ← وابسته به ۱.۱
└── وظیفه ۱.۵: اعتبارسنجی داده‌های استخراج‌شده ← وابسته به ۱.۲, ۱.۳, ۱.۴
```

### ۲.۳ سطح عملیاتی (Operational Level)

تبدیل هر **وظیفه** به **گام‌های عملی (Steps)** که عامل می‌تواند یک‌به‌یک اجرا کند:

```
وظیفه ۱.۲: استخراج داده‌های ترازنامه
├── گام ۱: دریافت فایل PDF صورت مالی
├── گام ۲: تبدیل PDF به متن با PyMuPDF
├── گام ۳: شناسایی بخش ترازنامه در متن
├── گام ۴: استخراج مقادیر (دارایی‌ها، بدهی‌ها، حقوق صاحبان سهام)
├── گام ۵: ساختاردهی به JSON
└── گام ۶: ذخیره در پایگاه داده
```

---

## ۳. روش‌های تجزیه وظایف (Decomposition Methods)

### ۳.۱ تجزیه خطی (Linear / Sequential Decomposition)

ساده‌ترین روش: وظایف **یکی پس از دیگری** اجرا می‌شوند. هر وظیفه به خروجی وظیفهٔ قبلی وابسته است.

```text
ورودی → [وظیفه ۱] → [وظیفه ۲] → [وظیفه ۳] → خروجی
```

**مثال:** 
```python
# ساختار خطی در LangGraph
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("write", write_node)
graph.add_edge("search", "analyze")
graph.add_edge("analyze", "write")
graph.add_edge("write", END)
```

**مناسب برای:** وظایف با وابستگی‌های زنجیره‌ای (تحقیق → تحلیل → نوشتن)

### ۳.۲ تجزیه موازی (Parallel / Fan-Out Decomposition)

وظایف **مستقل** به صورت هم‌زمان اجرا می‌شوند. نتایج در یک نقطه جمع (Fan-In) می‌شوند.

```text
         ┌── [وظیفه A] ──┐
         │                │
ورودی ──┼── [وظیفه B] ──┼── [ادغام] ── خروجی
         │                │
         └── [وظیفه C] ──┘
```

**مثال:**
```python
# Fan-out/Fan-in در LangGraph
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)

graph.add_node("research_standards", research_node)
graph.add_node("research_laws", research_node)
graph.add_node("research_market", research_node)
graph.add_node("merge_results", merge_node)

# Fan-out: هر سه تحقیق مستقل
graph.add_edge("start", "research_standards")
graph.add_edge("start", "research_laws")
graph.add_edge("start", "research_market")

# Fan-in: جمع‌آوری نتایج
graph.add_edge("research_standards", "merge_results")
graph.add_edge("research_laws", "merge_results")
graph.add_edge("research_market", "merge_results")
graph.add_edge("merge_results", END)
```

**مناسب برای:** وظایف مستقل مثل تحقیق هم‌زمان درباره موضوعات مختلف

### ۳.۳ تجزیه سلسله‌مراتبی (Hierarchical Decomposition)

وظایف در سطوح مختلف سازماندهی می‌شوند. یک **عامل ارشد (Supervisor Agent)** وظایف را به عامل‌های زیردست تخصیص می‌دهد.

```text
┌────────────────────────────────┐
│        Supervisor Agent        │
│  (تجزیه + تخصیص + پیگیری)     │
└──┬──────────┬──────────┬───────┘
   │          │          │
   ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐
│Expert │ │Expert │ │Expert │
│  A   │ │  B   │ │  C   │
└──────┘ └──────┘ └──────┘
```

**مثال پیاده‌سازی در HiveOS:**
```python
# Supervisor Flow در HiveOS
flow = {
    "id": "financial-analysis",
    "orchestrator": "supervisor",  # Supervisor mode
    "steps": [
        {
            "agent": "supervisor-agent",
            "task": "تجزیه وظیفه کلان به زیروظایف",
            "output_var": "subtasks"
        },
        {
            "agent": "data-collector",
            "depends_on": ["subtasks"],
            "parallel": True  # اجرای موازی
        },
        {
            "agent": "financial-analyst",
            "depends_on": ["data-collector"]
        },
        {
            "agent": "report-writer",
            "depends_on": ["financial-analyst", "data-collector"]
        }
    ]
}
```

### ۳.۴ تجزیه پویا (Dynamic Decomposition)

شبیه **تجزیه خطی** اما برنامه‌ریزی اولیه وجود ندارد — هر گام بعدی بر اساس نتیجهٔ گام قبلی تعیین می‌شود. این الگو توسط **ReAct** و **AutoGPT** محبوب شده.

```text
ورودی → [گام ۱] → [تصمیم] → [گام ۲] → [تصمیم] → [گام ۳] → خروجی
               ↘️            ↘️
            (تغییر مسیر)   (تقسیم به دو زیرمسیر)
```

**مزایا:** انعطاف بالا در مواجهه با شرایط غیرمنتظره
**معایب:** هزینهٔ بیشتر LLM، عدم قطعیت در زمان اجرا

---

## ۴. الگوریتم‌های تجزیه (Decomposition Algorithms)

### ۴.۱ تجزیه مبتنی بر LLM (LLM-Based Decomposition)

LLM خودش تصمیم می‌گیرد وظیفه را چطور تجزیه کند:

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

decompose_prompt = PromptTemplate(
    template="""شما یک برنامه‌ریز هوشمند هستید.

وظیفه کلان: {task}

این وظیفه را به زیروظایف مشخص و قابل اجرا تجزیه کن.
هر زیروظیفه باید:
۱. یک خروجی مشخص داشته باشد
۲. قابل تخصیص به یک عامل تخصصی باشد
۳. وابستگی‌هایش مشخص باشد

فرمت خروجی (JSON):
{{
  "subtasks": [
    {{
      "id": 1,
      "name": "...",
      "description": "...",
      "assigned_to": "agent_type",
      "depends_on": [],
      "expected_output": "..."
    }}
  ]
}}

تجزیه وظیفه:""",
    input_variables=["task"]
)

chain = LLMChain(llm=llm, prompt=decompose_prompt)
subtasks = chain.run(task="تهیه گزارش مالی از شرکت X")
```

### ۴.۲ تجزیه مبتنی بر قالب (Template-Based Decomposition)

استفاده از **الگوهای از پیش تعریف‌شده (Templates)** برای تجزیه وظایف پرتکرار:

```yaml
# flow-templates/financial-analysis.yml
name: تحلیل مالی
decomposition:
  method: template
  steps:
    - name: جمع‌آوری داده
      agent: data-collector
      tools: [web_search, pdf_reader]
    - name: محاسبه نسبت‌ها
      agent: financial-analyst
      tools: [calculator, ratio_analyzer]
      depends_on: [جمع‌آوری داده]
    - name: تحلیل روند
      agent: trend-analyst
      tools: [chart_generator, statistics]
      depends_on: [محاسبه نسبت‌ها]
    - name: گزارش نهایی
      agent: report-writer
      tools: [markdown, latex]
      depends_on: [تحلیل روند]
```

### ۴.۳ تجزیه مبتنی on DAG (Directed Acyclic Graph)

پیچیده‌ترین و انعطاف‌پذیرترین روش. وظایف در یک **گراف جهتی بدون دور** سازماندهی می‌شوند:

```text
          ┌──────────┐
          │ شروع     │
          └────┬─────┘
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
┌──────────┐ ┌──────┐ ┌──────┐
│ تحقیق A  │ │تحقیق B│ │تحقیق C│  ← سطح ۱ (موازی)
└─────┬────┘ └──┬───┘ └──┬───┘
      │         │        │
      └────┬────┴────┬───┘
           ▼         ▼
      ┌────────┐ ┌───────┐
      │تحلیل AB│ │تحلیل C│      ← سطح ۲ (ترتیبی)
      └───┬────┘ └───┬───┘
          │          │
          └─────┬────┘
                ▼
          ┌──────────┐
          │گزارش نهایی│          ← سطح ۳
          └──────────┘
```

**HiveOS Flow Engine از این روش استفاده می‌کند.** در HiveOS، Flow یک DAG است که گره‌های آن agentها و یال‌های آن وابستگی‌ها هستند.

---

## ۵. تجزیه در عمل — سناریوهای واقعی

### ۵.۱ سناریو: تحلیل اعتبار مشتری بانکی

```yaml
flow: credit-scoring
goal: تعیین اعتبار مشتری برای دریافت وام ۵۰۰ میلیون تومانی

decomposition:
  method: dag
  steps:
    - agent: identity-verifier
      task: احراز هویت و اعتبارسنجی مدارک
      tools: [national-id-api, document-ocr]
    
    - agent: credit-history-checker
      task: بررسی سابقه اعتباری در بانک مرکزی
      tools: [bank-api, credit-database]
    
    - agent: financial-statement-analyzer
      task: تحلیل صورت‌های مالی و گردش حساب
      tools: [pdf-extractor, ratio-analyzer]
    
    - agent: risk-scorer
      task: محاسبه امتیاز ریسک
      tools: [ml-model, scoring-engine]
      depends_on: 
        - identity-verifier
        - credit-history-checker
        - financial-statement-analyzer
    
    - agent: decision-maker
      task: تصمیم نهایی (تأیید/رد/شرطی)
      tools: [policy-engine, human-approval]
      depends_on: [risk-scorer]
```

### ۵.۲ سناریو: تحقیق و تولید محتوا

```
Goal: تولید مقاله ۳۰۰۰ کلمه‌ای درباره هوش مصنوعی در حسابداری

تجزیه توسط Supervisor Agent:

۱. تحقیق (موازی):
   ├── AI در حسابداری مالی (Search Agent)
   ├── AI در حسابرسی (Search Agent) 
   └── AI در مالیات (Search Agent)

۲. تحلیل و ترکیب (ترتیبی):
   ├── ترکیب نتایج تحقیق ← خلاصه هر بخش (Analyst Agent)
   └── شناسایی شکاف‌های محتوایی (Analyst Agent)

۳. نگارش (ترتیبی):
   ├── نگارش مقدمه (Writer Agent)
   ├── نگارش بدنه اصلی (Writer Agent)
   ├── نگارش نتیجه‌گیری (Writer Agent)
   └── ویرایش یکپارچه (Editor Agent)

۴. کیفیت (ترتیبی):
   ├── بررسی صحت علمی (Reviewer Agent)
   ├── بهینه‌سازی SEO (SEO Agent)
   └── تولید نسخه نهایی (Publisher Agent)
```

---

## ۶. چالش‌ها و راهکارها در تجزیه وظایف

| چالش | توضیح | راهکار |
|------|-------|--------|
| **وابستگی‌های پنهان (Hidden Dependencies)** | زیروظایفی که ظاهراً مستقل هستند اما در عمل وابستگی دارند | استفاده از DAG و تحلیل خودکار وابستگی‌ها |
| **تجزیه بیش از حد (Over-Decomposition)** | شکستن وظیفه به قطعات ریز که سربار هماهنگی را افزایش می‌دهد | حد مشخصی برای اندازهٔ زیروظایف تعیین کنید |
| **تجزیه کم (Under-Decomposition)** | زیروظایف هنوز آنقدر بزرگ‌اند که یک عامل نمی‌تواند انجام دهد | معیار مشخص: هر زیروظیفه باید در ۱-۲ فراخوانی LLM قابل انجام باشد |
| **تغییر شرایط (Changing Context)** | محیط خارجی حین اجرا تغییر می‌کند و برنامه نیاز به اصلاح دارد | تجزیه پویا (Dynamic Decomposition) |
| **هزینهٔ LLM** | فراخوانی LLM برای تجزیه هزینه‌بر است | کش کردن (caching) الگوهای پرتکرار، template-based برای وظایف استاندارد |

### قوانین سرانگشتی (Rules of Thumb) برای تجزیه:

1. **قانون ۵±۲:** هر وظیفه را حداکثر به ۷ زیروظیفه تقسیم کنید (ظرفیت حافظهٔ کاری انسان)
2. **قانون استقلال:** اگر دو زیروظیفه نیازی به خروجی هم ندارند، باید موازی اجرا شوند
3. **قانون واحد:** هر زیروظیفه باید خروجی **قابل اندازه‌گیری** داشته باشد
4. **قانون تخصص:** هر زیروظیفه باید به عاملی تخصیص داده شود که در آن حوزه تخصص دارد

---

## ۷. پیاده‌سازی در HiveOS

**HiveOS Flow Engine** از **تجزیه مبتنی بر DAG** با قابلیت اجرای موازی پشتیبانی می‌کند:

```python
# HiveOS Flow Definition — تجزیه خودکار با Supervisor Agent
from hiveos.mothership import Mothership
from hiveos.playground import FlowRunner

# یک Flow با Supervisor باعث تجزیه خودکار وظیفه می‌شود
flow_yaml = """
name: credit-analysis
orchestrator: supervisor
agents:
  - role: supervisor
    model: claude-sonnet-4
    task: "تجزیه وظیفه کلان به زیروظایف و تخصیص به عامل‌ها"
  - role: worker
    domain: accounting
    count: 3
  - role: worker
    domain: legal
    count: 1
  - role: reporter
    model: gpt-4o
constraints:
  max_depth: 3
  timeout: 300
"""

# اجرا
result = await Mothership.run_flow("credit-analysis", {
    "task": "تحلیل اعتبار مشتری با درآمد ماهیانه ۵۰ میلیون تومان و سابقه ۵ ساله"
})
```

**ویژگی‌های تجزیه در HiveOS:**

| ویژگی | توضیح |
|-------|-------|
| **تجزیه خودکار با Supervisor** | LLM Supervisor به صورت پویا وظیفه را تجزیه می‌کند |
| **قالب‌های از پیش تعریف‌شده** | استفاده از flow templates برای وظایف استاندارد |
| **اجرای موازی** | Fan-out زیروظایف مستقل و Fan-in نتایج |
| **کنترل عمق (Max Depth)** | جلوگیری از تجزیهٔ بی‌نهایت |
| **اعتبارسنجی DAG** | تشخیص دور (cycle) و وابستگی‌های غیرممکن |

---

## ۸. مقایسه روش‌های تجزیه

| معیار | خطی (Sequential) | موازی (Parallel) | سلسله‌مراتبی (Hierarchical) | پویا (Dynamic) |
|-------|-----------------|------------------|---------------------------|----------------|
| **سرعت اجرا** | کند | سریع (موازی) | متوسط | کند |
| **انعطاف‌پذیری** | کم | کم | متوسط | زیاد |
| **هزینه LLM** | کم | متوسط | زیاد | زیاد |
| **شفافیت (Traceability)** | زیاد | زیاد | متوسط | کم |
| **پیش‌بینی‌پذیری** | زیاد | زیاد | متوسط | کم |
| **مناسب برای** | وظایف خطی ساده | وظایف مستقل متعدد | وظایف سازمانی | وظایف اکتشافی |

---

## ۹. جمع‌بندی و نکات کلیدی

| # | نکته |
|---|------|
| ۱ | **تجزیه وظایف (Task Decomposition)** کلید مقیاس‌پذیری سیستم‌های چندعاملی است |
| ۲ | تجزیه در **سه سطح** انجام می‌شود: استراتژیک (هدف→ماموریت)، تاکتیکی (ماموریت→وظیفه)، عملیاتی (وظیفه→گام) |
| ۳ | **چهار روش اصلی:** خطی، موازی، سلسله‌مراتبی، پویا — هر کدام برای سناریوی خاصی مناسب است |
| ۴ | **DAG** انعطاف‌پذیرترین روش برای نمایش وابستگی‌های بین زیروظایف است |
| ۵ | تجزیه می‌تواند **دستی (Template-based)**، **نیمه‌خودکار (LLM-assisted)** یا **کاملاً خودکار (Dynamic)** باشد |
| ۶ | **HiveOS Flow Engine** از تجزیه مبتنی بر DAG با supervisor پویا پشتیبانی می‌کند |
| ۷ | **بازیابی از خطا** در تجزیه حیاتی است — شکست یک زیروظیفه نباید کل Flow را از بین ببرد |
| ۸ | **تست تجزیه:** بهترین راه برای تست، اجرای یک وظیفه با دو روش مختلف تجزیه و مقایسه نتایج است |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل مرتبط:** `docs/06-Research/agents/02-Multi-Agent-Systems/01-orchestration-patterns.md` (الگوهای ارکستراسیون)

# معماری HiveOS v1.0 — سند معماری سیستم عامل چندعاملی کسب‌وکار

> **نسخه:** v0.12 (پیشنویس معماری)
> **تاریخ:** جولای ۲۰۲۶
> **نویسنده:** تیم معماری HiveOS
> **مخاطب:** توسعه‌دهندگان، معماران سیستم، سرمایه‌گذاران فنی

---

## فهرست

1. [Executive Summary — خلاصه اجرایی](#1-executive-summary)
2. [System Overview — نمای کلی سیستم](#2-system-overview)
3. [Goal System — سیستم هدف](#3-goal-system)
4. [Brain Runtime — زمان اجرای شناختی](#4-brain-runtime)
5. [Kernel — هسته](#5-kernel)
6. [Planner — برنامه‌ریز](#6-planner)
7. [Workflow Runtime — زمان اجرای گردش کار](#7-workflow-runtime)
8. [Memory Model — مدل حافظه](#8-memory-model)
9. [Event Bus — گذرگاه رویداد](#9-event-bus)
10. [Tool Bus — گذرگاه ابزار](#10-tool-bus)
11. [Domain SDK — کیت توسعه دامنه](#11-domain-sdk)
12. [Plugin API — رابط برنامه‌نویسی افزونه](#12-plugin-api)
13. [Bridge to Future Versions — پل به نسخه‌های آینده](#13-bridge-to-future-versions)
14. [Architecture Decision Records — تصمیمات معماری](#14-architecture-decision-records)

---

## 1. Executive Summary — خلاصه اجرایی

### What is HiveOS?

HiveOS یک **سیستم عامل برای عامل‌های هوش مصنوعی کسب‌وکار (Operating System for Business AI Agents)** است. درست مثل اینکه لینوکس به برنامه‌ها سرویس‌های بنیادی (فایل سیستم، شبکه، حافظه) می‌دهد، HiveOS به عامل‌های هوش مصنوعی سرویس‌های بنیادی می‌دهد: حافظه، برنامه‌ریزی، اجرا، یادگیری، و ارتباط.

### Current Status

پروژه هم‌اکنون در **نسخه v0.12.0** است و لایه‌های زیر ساخته شده‌اند:

| لایه | وضعیت | توضیح |
|------|--------|-------|
| **Flow Engine** | ✅ | موتور اجرای جریان‌های کاری ترتیبی با پشتیبانی DAG |
| **Mothership** | ✅ | سرور مرکزی برای ثبت agent، مسیریابی وظایف، ارتباطات |
| **Enterprise** | ✅ | RBAC، Audit Trail، Multi-tenant، Pricing |
| **Brain** | ✅ | Event Stream، Decision Tracer، Approval Gate |
| **Playground** | ✅ | Canvas بصری، Component Engine با ۱۰ نوع کامپوننت |
| **Learning** | ✅ | Execution Logger، Analytics، Pattern Recognition |
| **Storage** | ✅ | StorageEngine مبتنی بر SQLite |
| **Domain Registry** | ✅ | ثبت، کشف، یادگیری دامنه‌ها |
| **Desktop** | ✅ | پوسته بومی ویندوز (pywebview) + PWA |
| **Accounting Domain** | ✅ | ۲۹ agent، ۶ flow، ۴۸۰+ فایل دانش |
| **Agent Learning** | ✅ | ۲۴ فایل مستندات آموزشی (~۳۰۰KB) |

**۴۳۶ تست** — همگی پاس.

### The Gap

چیزی که هنوز وجود ندارد، یک **سیستم شناختی منسجم (Cognitive Runtime)** است. الان agentها مستقیماً tool صدا می‌زنند یا flowهای ساده اجرا می‌کنند. اما سیستم هنوز:

- **Goal را به عنوان موجودیت مستقل** نمی‌شناسد — نمی‌توان بین Missionها اولویت‌بندی کرد
- **چرخه شناختی کامل** (Perceive → Reason → Plan → Execute → Observe → Reflect → Learn → Adapt) ندارد
- **Brain فاقد هویت منسجم** است — Planner, Runtime, Memory, Reflection هر کدوم مسیر خودشون می‌رن
- **Observer درون Runtime** وجود ندارد — نمی‌توان در لحظه Metrics جمع کرد
- **Event Sourcing** برای Debug و بازسازی State در نظر گرفته نشده
- **Semantic Memory (Entity-based)** بین Memory و Knowledge Graph وجود ندارد

این سند معماری برای اولین بار **Brain Runtime** را به عنوان چارچوب شناختی مرکزی تعریف می‌کند و نقشه راه رسیدن از وضعیت فعلی به v1.0 را مشخص می‌کند.

---

## 2. System Overview — نمای کلی سیستم

### 2.1 Philosophy — فلسفه طراحی

HiveOS بر اساس ۵ اصل معماری ساخته می‌شود:

| اصل | توضیح | مثال |
|-----|-------|------|
| **۱. Kernel Minimalism** | هسته کمترین مسئولیت ممکن را دارد | هسته Planning نمی‌کند — Planner را اجرا می‌کند |
| **۲. Everything is a Plugin** | همه چیز از طریق Plugin API اضافه می‌شود | Domainها، Agentها، Tools، حتی Runtime |
| **۳. Event-Driven** | همه چیز از طریق رویدادها ارتباط برقرار می‌کند | هیچ کامپوننتی مستقیماً کامپوننت دیگر را صدا نمی‌زند |
| **۴. Memory First** | حافظه لایه اول است، نه یک افزونه | هر تصمیم در حافظه ثبت می‌شود |
| **۵. Human in the Loop** | انسان همیشه می‌تواند مداخله کند | Approval Gate در همه نقاط تصمیم‌گیری |

### 2.2 Seven Layers — هفت لایه

معماری HiveOS v1.0 از ۷ لایه تشکیل شده است. مهم: این لایه‌ها **به ترتیب نسخه‌ها** نیستند — نسخه‌ها **افق‌های (horizons)** تکامل هستند، هر کدام یک لایه جدید را به بلوغ می‌رسانند.

```
                    ┌─────────────────────────────────┐
                    │        Domain SDK (لایه ۷)       │
                    │  ابزار توسعه‌دهنده برای ساخت دامنه │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │       Plugin API (لایه ۶)         │
                    │     افزونه‌های شخص ثالث           │
                    └────────────────┬────────────────┘
                                     │
┌────────────────────────────────────────────────────────────────────┐
│                    ┌───────────────┐  ┌───────────────┐            │
│                    │   Planner    │  │   Runtime    │  لایه ۴ و ۵ │
│                    │  برنامه‌ریز  │  │    اجرا       │            │
│                    └───────┬───────┘  └───────┬───────┘            │
│     ┌──────────────────────┴──────────────────┴──────────────┐   │
│     │                    Tool Bus (لایه ۳)                    │   │
│     │           گذرگاه ابزار — ارتباط استاندارد ابزارها        │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │          Event Bus (لایه ۲) — گذرگاه رویداد              │   │
│     │              ستون فقرات ارتباطی سیستم                    │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │   Memory Model (لایه ۱) — مدل حافظه                      │   │
│     │   Session · Agent · Company · Domain · Long-term        │   │
│     └──────────────────────────┬──────────────────────────────┘   │
│                                │                                  │
│     ┌──────────────────────────▼──────────────────────────────┐   │
│     │            Kernel (لایه ۰) — هسته                       │   │
│     │     StorageEngine · Config · Logging · Lifecycle        │   │
│     └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 2.3 Naming Convention — قرارداد نام‌گذاری

| موجودیت | کنوانسیون | مثال |
|---------|-----------|-------|
| **نسخه** | Semantic Versioning | v0.12.0, v1.0.0 |
| **دامنه** | kebab-case | `accounting`, `tax-iran` |
| **Agent Blueprint** | kebab-case | `financial-analyst` |
| **Tool** | kebab-case | `financial-statement-reader` |
| **Flow** | kebab-case | `tax-calculation-flow` |
| **Event Type** | `domain:entity:action` | `flow:step:completed` |
| **Namespace** | `snake_case` | `domain_registry` |
| **JSON Key** | `snake_case` | `installed_at` |

---

## 3. Goal System — سیستم هدف

### 3.1 Why a Goal System?

در معماری قبلی، "کاربر یه چیزی می‌گه" مستقیماً می‌رفت به Planner. ولی Goal به عنوان یک موجودیت مستقل وجود نداشت. این یعنی:

- نمی‌توان بین چند Mission همزمان اولویت‌بندی کرد
- نمی‌توان Budget مصرف LLM را تخمین زد
- نمی‌توان ضرب‌الاجل (Deadline) تعیین کرد
- نمی‌توان ریسک را ارزیابی کرد
- نمی‌توان وابستگی بین Goalها را مدیریت کرد

### 3.2 Goal Structure

```json
{
  "goal_id": "goal_abc123",
  "mission": "بستن ماهانه حسابداری شرکت X برای فروردین ۱۴۰۴",
  "type": "mission",
  "status": "pending",
  
  "owner": "finance-manager",
  "priority": "high",
  "deadline": "1404-02-10T20:00:00",
  
  "budget": {
    "max_llm_cost": 5.0,
    "max_execution_time_ms": 600000
  },
  
  "context": {
    "company": "X",
    "period": "Farvardin 1404",
    "domain": "accounting"
  },
  
  "risk_level": "medium",
  "dependencies": [],
  "parent_goal": null,
  "sub_goals": [],
  
  "success_criteria": [
    "همه تراکنش‌های ماه ثبت شده باشند",
    "تراز آزمایشی متوازن باشد",
    "گزارش سود و زیان تولید شده باشد"
  ],
  
  "metadata": {
    "created_at": "2026-07-20T08:00:00Z",
    "source": "user",
    "version": 1
  }
}
```

### 3.3 Goal Types

| Type | مثال | Planning Level | LLM Cost |
|------|------|---------------|----------|
| **Query** | "قیمت سهم X چقدر است؟" | Immediate | ~$0.01 |
| **Task** | "محاسبه مالیات حقوق کارمند ۱۲۳۴۵" | Template | ~$0.05 |
| **Mission** | "بستن ماهانه حسابداری فروردین" | Strategic | ~$0.50 |
| **Project** | "پیاده‌سازی سیستم مدیریت انبار تا پایان سال" | Strategic (multi-goal) | ~$5.00+ |

### 3.4 Goal Lifecycle

```
Created ──→ Validated ──→ Queued ──→ Active ──→ Completed
                │                      │
                ▼                      ▼
            Rejected              Failed / Cancelled
```

| State | توضیح |
|-------|-------|
| `created` | کاربر Goal را تعریف کرده |
| `validated` | سیستم بررسی کرده: domain موجود است؟ وابستگی‌ها برقرار است؟ |
| `queued` | در صف انتظار — اولویت‌بندی با Scheduler |
| `active` | تحویل به Planner → تبدیل به ExecutionPlan |
| `completed` | با موفقیت به اتمام رسیده |
| `failed` | پس از همه Retryها شکست خورده |
| `cancelled` | توسط کاربر لغو شده |
| `rejected` | در مرحله Validation رد شده |

### 3.5 Goal → Planner → Execution Plan

```
                     ┌──────────┐
                     │  Goal    │
                     └────┬─────┘
                          │
               ┌──────────▼──────────┐
               │   Goal Service      │
               │  - Validate         │
               │  - Estimate Cost    │
               │  - Priority Score   │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │   Planner           │
               │  - Decompose        │
               │  - Match Capability │
               │  - Build DAG        │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │   ExecutionPlan     │
               └─────────────────────┘
```

### 3.6 Goal Service API

```python
class GoalService:
    """مدیریت چرخه حیات Goalها"""
    
    def create(self, mission: str, metadata: dict) -> Goal:
        """ایجاد Goal جدید از متن مأموریت"""
    
    def get(self, goal_id: str) -> Goal:
        """دریافت Goal با شناسه"""
    
    def list(self, status: str = None, owner: str = None) -> list[Goal]:
        """لیست Goalها با فیلتر"""
    
    def update_status(self, goal_id: str, status: str):
        """به‌روزرسانی وضعیت"""
    
    def resolve_dependencies(self, goal_id: str) -> bool:
        """بررسی وابستگی‌ها — آیا همه برقرارند؟"""
    
    def estimate(self, goal_id: str) -> dict:
        """تخمین هزینه و زمان"""
    
    def cancel(self, goal_id: str):
        """لغو یک Goal"""
```

### 3.7 Priority Scheduling

Goalها بر اساس یک **امتیاز اولویت** زمان‌بندی می‌شوند:

```
priority_score = 
    priority_weight(priority) * 10 +
    deadline_urgency(deadline) * 8 +      # نزدیک‌تر = امتیاز بیشتر
    dependency_count * 5 +                  # وابستگی‌های بیشتر = زودتر
    estimated_value * 3                     # ارزش تجاری (در صورت مشخص بودن)
```

**نکته پیاده‌سازی:** Priority Scheduling در v0.12 طراحی می‌شود ولی در v0.13 همراه با Planner پیاده‌سازی می‌شود.

---

## 4. Brain Runtime — زمان اجرای شناختی

### 4.1 What is Brain Runtime?

**Brain Runtime** مفهوم مرکزی معماری HiveOS v1.0 است.它不是 یک ماژول جدید — بلکه **چارچوبی است که Planner, Runtime, Observer, Reflection, Memory و Learning را در یک چرخه شناختی واحد سازمان می‌دهد.**

Brain Runtime = Cognitive Operating System برای Agentها.

### 4.2 The Cognitive Cycle — چرخه شناختی

```
                    ┌─────────────────────────┐
                    │      MISSION (GOAL)     │
                    │      "بستن ماهانه"      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
               ┌───│     1. PERCEPTION       │───┐
               │   │  درک Goal و Context     │   │
               │   │  تشخیص Domain, Type     │   │
               │   └────────────┬────────────┘   │
               │                │                │
               │   ┌────────────▼────────────┐   │
               │   │    2. REASONING         │   │
               │   │  تحلیل: چطور انجام بدم؟  │   │
               │   │  انتخاب سطح Planning    │   │
               │   │  (Immediate/Template/   │   │
               │   │   Strategic)            │   │
               │   └────────────┬────────────┘   │
               │                │                │
               │   ┌────────────▼────────────┐   │
               │   │    3. PLANNING          │   │
               │   │  تولید ExecutionPlan    │   │
               │   │  Capability Matching    │   │
               │   │  Dependency Graph (DAG) │   │
               │   └────────────┬────────────┘   │
               │                │                │
    ┌──────────┼────────────────┼────────────────┼──────────┐
    │          │                │                │          │
    │   ┌──────▼────────────────▼────────────────▼──────┐  │
    │   │           4. EXECUTION + OBSERVATION          │  │
    │   │  ┌────────────────┐  ┌──────────────────┐    │  │
    │   │  │ Phase Executor │  │ Observer         │    │  │
    │   │  │ State Machine  │  │ Metrics · Events  │    │  │
    │   │  │ HITL · Retry   │  │ Logging · Tracing │    │  │
    │   │  └────────────────┘  └──────────────────┘    │  │
    │   └──────────────────────┬──────────────────────┘  │
    │                          │                          │
    │   ┌──────────────────────▼──────────────────────┐  │
    │   │         5. EVALUATION                       │  │
    │   │  آیا Agent موفق بود؟ Metrics:               │  │
    │   │  duration, token_cost, errors, quality_score│  │
    │   └──────────────────────┬──────────────────────┘  │
    │                          │                          │
    └──────────┬────────────────┼────────────────┬────────┘
               │                │                │
    ┌──────────▼────────────────▼────────────────▼──────┐
    │              6. REFLECTION                       │
    │  تحلیل: چه شد؟ چه اشتباه کردیم؟ چطور بهتر کنیم؟  │
    │  Success/Fail Pattern Detection                  │
    │  Mistake Analysis · Improvement Suggestions      │
    └──────────────────────┬──────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────┐
    │             7. MEMORY UPDATE                     │
    │  ذخیره یادگیری‌ها در Company Memory              │
    │  ذخیره Patternها در Knowledge Graph              │
    └──────────────────────┬──────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────┐
    │             8. ADAPTATION                        │
    │  تغییر رفتار بر اساس یادگیری‌ها                   │
    │  • تنظیم پارامترهای Planner                      │
    │  • پیشنهاد Agent/Tool جدید                       │
    │  • اصلاح Flow Templateها                         │
    │  • Replan در صورت نیاز                           │
    └──────────────────────┬──────────────────────────┘
                           │
                           ▼
                  مأموریت بعدی / چرخه جدید
```

### 4.3 Cognitive Cycle vs Old Architecture

| جنبه | معماری قدیم (سند قبلی) | Brain Runtime (جدید) |
|------|----------------------|---------------------|
| **ساختار** | کامپوننت‌های مستقل: Planner → Runtime → Reflection | چرخه شناختی واحد ۸ مرحله‌ای |
| **Brain** | فقط EventStream + DecisionTracer + ApprovalGate | **چارچوب اصلی** — همه چیز درون Brain |
| **Planner** | یک کامپوننت جدا | بخشی از مراحل ۲-۳ (Reasoning + Planning) |
| **Runtime** | سیستم اجرا | مرحله ۴ (Execution + Observation) |
| **Reflection** | v0.15 — دیر و جدا | مرحله ۶ — بخشی از چرخه از روز اول |
| **Observer** | وجود نداشت | بخشی از Runtime — از روز Metrics جمع می‌کند |
| **Adaptation** | وجود نداشت | مرحله ۸ — چرخه را می‌بندد |
| **Memory** | حافظه غیرفعال | مراحل ۷-۸ — Memory فعال و یادگیرنده |

### 4.4 Relationship to Existing Code

| مؤلفه موجود | نقش در Brain Runtime | تغییر |
|-------------|---------------------|-------|
| **Planner** (جدید) | Reasoning + Planning | minor — باید Goal-aware شود |
| **Flow Engine** (موجود) | بخشی از Execution | major — State Machine شود |
| **Component Engine** | بخشی از Execution | minor |
| **EventStream** | زیرساخت Observation | minor → Event Bus |
| **DecisionTracer** | بخشی از Observer | minor — Metrics اضافه شود |
| **ApprovalGate** | HITL در Execution | minor — API استاندارد |
| **Learning Logger** | ورودی Reflection | major — Observer structure |
| **Analytics** | Reflection | minor |
| **StorageEngine** | زیرساخت همه مراحل | بدون تغییر |

### 4.5 Implementation Across Versions

Brain Runtime یک Feature نیست که در یک نسخه ساخته شود — یک **چارچوب معماری** است:

| نسخه | بخش Brain Runtime | تحویل |
|------|------------------|-------|
| v0.12 | **تعریف** — معماری و چرخه | این سند |
| v0.13 | **Reasoning + Planning** | Goal → Execution Plan |
| v0.14 | **Execute + Observe** | Runtime با Observer داخلی |
| v0.15 | **Reflect + Learn** | Reflection Engine |
| v0.16 | **Memory + Adapt** | Knowledge Graph + Company |
| v1.0 | **یکپارچه** | Cognitive Cycle کامل |

## 5. Kernel — هسته

### 5.1 Definition — تعریف

هسته (**Kernel**) کمترین مجموعه سرویس‌هایی است که هر کامپوننت دیگر برای کار کردن به آن نیاز دارد. هسته **نمی‌داند** Planner چیست، Runtime چیست، یا Domain چیست.

### 5.2 Responsibilities — مسئولیت‌ها

| سرویس | مسئولیت | وضعیت فعلی |
|-------|---------|-----------|
| **StorageEngine** | persistence key-value در SQLite | ✅ موجود |
| **Config Management** | بارگذاری تنظیمات از YAML + env | ✅ موجود (جزئی) |
| **Logging** | ثبت رویدادهای سیستمی | ✅ موجود |
| **Lifecycle Manager** | شروع و توقف graceful کامپوننت‌ها | ❌ نیاز به ساخت |
| **Dependency Injection** | ثبت و کشف سرویس‌های داخلی | ❌ نیاز به ساخت |
| **Health Check** | بررسی سلامت خود هسته | ❌ نیاز به ساخت |

### 5.3 Kernel API

```python
class Kernel:
    """
    هسته HiveOS — یک container برای سرویس‌های بنیادی.
    
    Usage:
        kernel = Kernel(storage=StorageEngine("hiveos.db"))
        kernel.register("memory", MemoryService())
        kernel.register("event_bus", EventBus())
        
        await kernel.start()    # شروع همه سرویس‌ها
        await kernel.shutdown() # توقف graceful
    """
    
    def __init__(self, storage: StorageEngine, config: dict = None):
        self.storage = storage
        self.config = config or {}
        self._services: dict[str, Service] = {}
        self._lifecycle: LifecycleManager = LifecycleManager()
    
    def register(self, name: str, service: Service):
        """ثبت یک سرویس در هسته"""
        self._services[name] = service
    
    def get(self, name: str) -> Service:
        """دسترسی به یک سرویس ثبت‌شده"""
        return self._services[name]
    
    async def start(self):
        """شروع همه سرویس‌ها به ترتیب وابستگی"""
        for name, svc in self._topological_services():
            await svc.start()
    
    async def shutdown(self):
        """توقف همه سرویس‌ها به ترتیب معکوس"""
        for name, svc in reversed(self._topological_services()):
            await svc.shutdown()
```

### 3.4 Kernel Boundaries — مرزهای هسته

**هسته این کارها را انجام می‌دهد:** ذخیره‌سازی، ثبت سرویس، مدیریت چرخه حیات، لاگینگ.

**هسته این کارها را انجام نمی‌دهد:**
- برنامه‌ریزی (Planning) ← این کار Planner است
- اجرای workflow ← این کار Runtime است
- مدیریت حافظه هوشمند ← این کار Memory Service است
- مسیریابی پیام ← این کار Event Bus است
- مدیریت ابزار ← این کار Tool Bus است

---

## 6. Planner — برنامه‌ریز

### 6.1 Why Planner Before Runtime?

سوال: چرا **اول Planner** و بعد Runtime؟

پاسخ: چون Runtime باید **Plan را اجرا کند**، نه اینکه خودش تصمیم بگیرد. اگر Runtime را بدون Planner بسازیم، همان execution engine ساده‌ای می‌شود که الان داریم — فقط با state management بهتر. Runtimeای که برای اجرای Plan طراحی شده باشد، با Runtimeای که مستقیماً agentها را صدا می‌زند، **کاملاً تفاوت دارد**.

تفاوت Runtime با و بدون Planner:

| ویژگی | Runtime بدون Planner | Runtime با Planner |
|-------|--------------------|-------------------|
| **ورودی** | "این کار را انجام بده" | یک Plan ساختاریافته با DAG |
| **تصمیم‌گیری** | خود Runtime تصمیم می‌گیرد چطور اجرا کند | Plan از قبل تصمیمات را گرفته |
| **Error Recovery** | محدود (بیشتر Retry) | می‌تواند Plan را اصلاح کند یا Replan کند |
| **قابلیت ممیزی** | متوسط (logging) | کامل (هر تصمیم در Plan ثبت شده) |
| **بهینه‌سازی** | سخت | می‌توان Planهای مختلف را مقایسه کرد |

### 6.2 Architecture — معماری Planner

```
User Goal (مثلاً: "تحلیل مالی شرکت X برای سرمایه‌گذاری")
    │
    ▼
┌─────────────────────────────────────────────┐
│              Planner                         │
│                                              │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Goal Analyzer   │  │  Decomposition   │  │
│  │  تحلیل هدف       │─▶│  تجزیه به زیر     │  │
│  │  (مبهم → واضح)   │  │  وظایف           │  │
│  └──────────────────┘  └────────┬─────────┘  │
│                                 │            │
│  ┌──────────────────────────────▼──────────┐ │
│  │  Capability Matcher                     │ │
│  │  تطبیق زیروظایف با agentهای موجود       │ │
│  └──────────────────────────┬──────────────┘ │
│                             │                │
│  ┌──────────────────────────▼──────────────┐ │
│  │  Dependency Resolver                    │ │
│  │  تعیین وابستگی‌ها و ترتیب اجرا (DAG)    │ │
│  └──────────────────────────┬──────────────┘ │
│                             │                │
│  ┌──────────────────────────▼──────────────┐ │
│  │  Plan Validator                         │ │
│  │  بررسی: آیا Plan قابل اجراست؟          │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  خروجی: ExecutionPlan (DAG کامل)             │
└─────────────────────────────────────────────┘
    │
    ▼
ExecutionPlan → Runtime
```

### 6.3 Three Levels of Planning — سه سطح برنامه‌ریزی

Planner سه سطح دارد. انتخاب سطح بر اساس **پیچیدگی** و **عدم قطعیت** هدف است:

```
پیچیدگی بالا ▲
              │
              │    سطح ۳: Strategic Planning
              │    (LLM-intensive، بازنگری پویا)
              │
              │    سطح ۲: Template-Based Planning
              │    (استفاده از Flowهای از پیش تعریف‌شده)
              │
              │    سطح ۱: Immediate Planning
              │    (وظایف ساده، یک agent)
              └───────────────────────────────► عدم قطعیت بالا
```

#### Level 1 — Immediate Planning

برای وظایف ساده که نیاز به یک agent دارند:

```yaml
# ورودی: "قیمت سهم X را بررسی کن"
execution_plan:
  type: immediate
  agents:
    - id: market-researcher
      task: "بررسی قیمت سهم X"
      tools: [stock-api, web-search]
  output: "گزارش قیمت سهم"
```

**هزینه LLM:** بسیار کم (صفر — فقط انتخاب agent)
**زمان اجرا:** < ۱ ثانیه

#### Level 2 — Template-Based Planning

برای وظایف تکراری که Flow template دارند:

```yaml
# ورودی: "محاسبه مالیات حقوق برای کارمند ۱۲۳۴۵"
execution_plan:
  type: template-based
  template: payroll-tax-calculation
  parameters:
    employee_id: "EMP-12345"
    month: "فروردین"
    year: 1404
  agents:
    - id: salary-calculator
      task: "محاسبه حقوق ناخالص"
      tools: [hr-system-api, attendance-system]
    - id: tax-calculator
      depends_on: [salary-calculator]
      task: "محاسبه مالیات حقوق طبق جدول ۱۴۰۴"
      tools: [tax-table-1404, deduction-calc]
    - id: insurance-calculator
      depends_on: [salary-calculator]
      task: "محاسبه حق بیمه تأمین اجتماعی"
      tools: [insurance-table-1404]
    - id: payslip-generator
      depends_on: [tax-calculator, insurance-calculator]
      task: "تولید فیش حقوقی"
      tools: [payslip-template]
```

**هزینه LLM:** کم (فقط پر کردن پارامترها)
**زمان اجرا:** < ۵ ثانیه

#### Level 3 — Strategic Planning

برای اهداف بلندمدت و پیچیده:

```yaml
# ورودی: "یک تحلیل جامع از سلامت مالی شرکت X برای سرمایه‌گذاری تهیه کن"
execution_plan:
  type: strategic
  goal: "تحلیل سلامت مالی شرکت X"
  
  # تجزیه خودکار توسط LLM
  decomposition_strategy: llm-guided
  max_depth: 3
  max_branches: 5
  
  # خروجی میانی در هر مرحله
  checkpoint: true
  human_review_points:
    - بعد از بخش مالی
    - قبل از توصیه نهایی
  
  # آیتم‌های Plan (توسط LLM تولید می‌شود):
  phases:
    - phase: 1
      name: "جمع‌آوری داده"
      parallel:
        - agent: financial-scraper
          task: "دریافت صورت‌های مالی ۳ سال اخیر"
        - agent: market-researcher
          task: "تحلیل صنعت و رقبا"
        - agent: news-analyzer
          task: "بررسی اخبار و ریسک‌های حقوقی"
    
    - phase: 2
      name: "تحلیل"
      depends_on: [phase-1]
      agents:
        - agent: ratio-analyzer
          task: "محاسبه و تفسیر نسبت‌های مالی"
          input_from: [financial-scraper]
        - agent: risk-assessor
          task: "ارزیابی ریسک‌های عملیاتی و مالی"
          input_from: [news-analyzer, market-researcher]
    
    - phase: 3
      name: "گزارش نهایی"
      depends_on: [phase-2]
      agents:
        - agent: report-writer
          task: "تدوین گزارش سرمایه‌گذاری"
          input_from: [ratio-analyzer, risk-assessor]
        - agent: reviewer
          task: "بررسی کیفیت و دقت گزارش"
```

**هزینه LLM:** متوسط تا زیاد (تجزیه + هر agent)
**زمان اجرا:** ۳۰ ثانیه تا ۵ دقیقه

### 6.4 ExecutionPlan Data Structure — ساختار داده Plan

```json
{
  "plan_id": "plan_abc123",
  "goal": "تحلیل مالی شرکت X",
  "type": "strategic",
  "created_at": "2026-07-20T10:00:00Z",
  "status": "ready",
  
  "phases": [
    {
      "id": "phase-1",
      "name": "جمع‌آوری داده",
      "parallel": true,
      "agents": [
        {
          "agent_id": "financial-scraper",
          "domain": "accounting",
          "task": "دریافت صورت‌های مالی",
          "tools": ["web-scraper", "pdf-extractor"],
          "expected_output": "structured_financial_data",
          "timeout": 120
        }
      ],
      "depends_on": []
    }
  ],
  
  "variables": {
    "input": {"company": "X"},
    "intermediate": {},
    "output": {}
  },
  
  "human_review_points": ["phase-2/output"],
  "metadata": {
    "total_agents": 7,
    "estimated_duration": 180,
    "llm_cost_estimate": 0.15
  }
}
```

### 6.5 Planner Implementation Path — مسیر پیاده‌سازی

| Step | کار | تخمین |
|------|-----|-------|
| 1 | `Planner` class با Immediate mode | ۱ روز |
| 2 | Template matcher (سطح ۲) | ۲ روز |
| 3 | LLM-guided decomposition (سطح ۳) | ۳ روز |
| 4 | Plan Validator (DAG, cycle detection) | ۱ روز |
| 5 | Plan storage + تاریخچه | ۱ روز |
| 6 | API endpoints | ۱ روز |
| 7 | Desktop UI برای نمایش Plan | ۲ روز |
| 8 | تست‌ها | ۲ روز |
| **جمع** | | **۱۳ روز** |

---

## 7. Workflow Runtime — زمان اجرای گردش کار

### 7.1 Definition — تعریف

Runtime سیستمی است که **ExecutionPlan** را دریافت کرده و آن را **اجرا، رهگیری، و مدیریت** می‌کند. Runtime **نمی‌داند** Plan چطور ساخته شده — فقط آن را اجرا می‌کند.

### 7.2 Runtime vs Current Flow Engine

| ویژگی | Flow Engine (فعلی) | Runtime (هدف) |
|-------|-------------------|---------------|
| **ورودی** | Flow YAML دستی | ExecutionPlan از Planner |
| **State Management** | JSON فایلی | StorageEngine + State Machine |
| **Pause/Resume** | ❌ ندارد | ✅ بله |
| **Schedule** | ❌ ندارد | ✅ Cron + Event + Webhook |
| **HITL** | ❌ ندارد | ✅ Approval Gate داخلی |
| **Parallel** | ❌ ترتیبی | ✅ موازی واقعی |
| **Error Recovery** | Retry ساده | Retry + Skip + Replan + Abort |
| **Observability** | Console log | Event Stream + Metrics |
| **Timeout** | agent-level | workflow-level + agent-level |

### 7.3 Workflow State Machine — ماشین حالت Workflow

```
     ┌──────────┐
     │  Created │
     └────┬─────┘
          │ Schedule / Trigger
          ▼
     ┌──────────┐
     │  Planned  │ ← Planner یک ExecutionPlan تولید کرد
     └────┬─────┘
          │ Execute
          ▼
     ┌──────────┐
     │  Running  │
     └────┬─────┘
          │
     ┌────┴────┐──── ─ ─ ─ ─ ─
     │         │               │
     ▼         ▼               ▼
┌────────┐ ┌────────┐  ┌──────────┐
│Paused  │ │Failed  │  │Completed │
└───┬────┘ └────────┘  └──────────┘
    │ Resume
    ▼
 ┌──────────┐
 │  Running  │
 └──────────┘
```

حالت‌های ممکن:

| State | معنی | امکان Resume |
|-------|------|-------------|
| `created` | Workflow ایجاد شده اما شروع نشده | — |
| `planned` | ExecutionPlan آماده است | — |
| `running` | در حال اجرا | ✅ |
| `paused` | متوقف شده (دستی یا HITL) | ✅ |
| `failed` | شکست خورده (بعد از همه retryها) | ❌ (Replan شود) |
| `cancelled` | لغو شده توسط کاربر | ❌ |
| `completed` | موفق | — |
| `completed_with_errors` | موفق با خطا در برخی مراحل | — |

### 7.4 State Persistence — ذخیره‌سازی State

هر Workflow به این شکل در StorageEngine ذخیره می‌شود:

```python
workflow_state = {
    "id": "wf_abc123",
    "plan_id": "plan_def456",
    "status": "running",
    "started_at": "2026-07-20T10:00:00Z",
    "phases": {
        "phase-1": {
            "status": "completed",
            "started_at": "...",
            "completed_at": "...",
            "agents": {
                "financial-scraper": {
                    "status": "completed",
                    "result": "{...}",
                    "token_count": 1500,
                    "duration_ms": 8500
                }
            }
        },
        "phase-2": {
            "status": "running",
            "agents": {
                "ratio-analyzer": {
                    "status": "running",
                    "started_at": "..."
                }
            }
        }
    },
    "variables": {
        "input": {...},
        "phase-1/output": "{...}",
        "phase-2/ratio-analyzer/output": None
    },
    "timeline": [
        {"type": "phase_started", "phase": "phase-1", "at": "..."},
        {"type": "agent_completed", "agent": "financial-scraper", "at": "..."},
        {"type": "phase_completed", "phase": "phase-1", "at": "..."},
    ]
}
```

### 7.5 Trigger Types — انواع شروع

Runtime از ۴ نوع Trigger پشتیبانی می‌کند:

| Trigger | توضیح | مثال |
|---------|-------|------|
| **Manual** | اجرای دستی توسط کاربر | دکمه "Run" در Dashboard |
| **Cron** | اجرای زمان‌بندی شده | "هر روز ساعت ۸ صبح: تولید گزارش دیروز" |
| **Event** | اجرا در پاسخ به یک رویداد | "وقتی فاکتوری با مبلغ > ۵۰ میلیون ثبت شد: شروع تأیید" |
| **Webhook** | اجرا در پاسخ به درخواست HTTP خارجی | "ERP سیستم خارجی: یک مشتری جدید ثبت شده" |

### 7.6 HITL — Human in the Loop

Runtime نقاط توقف برای **تأیید انسانی** را پشتیبانی می‌کند:

```yaml
# داخل ExecutionPlan:
human_review_points:
  - id: approve-invoice
    phase: phase-2
    description: "تأیید فاکتور بالای ۵۰ میلیون"
    required_role: "finance-manager"
    timeout: 86400  # 24 ساعت فرصت
    on_timeout: "notify-escalate"
    actions:
      - approve
      - reject
      - modify
```

وقتی Runtime به یک HITL point می‌رسد:
1. Workflow را به حالت `paused` می‌برد
2. یک ApprovalGate در Brain ایجاد می‌کند
3. اعلان به کاربر/نقش مربوطه ارسال می‌شود
4. منتظر می‌ماند تا کاربر approve/reject کند
5. بعد از تصمیم، Workflow ادامه می‌یابد

### 7.7 Error Handling — مدیریت خطا

Runtime ۴ استراتژی برای مدیریت خطا دارد که در ExecutionPlan مشخص می‌شود:

```yaml
error_strategies:
  - type: retry
    max_attempts: 3
    backoff: exponential  # 2s → 4s → 8s
  
  - type: skip
    continue_workflow: true
    mark_as: skipped
  
  - type: replan
    trigger: "runtime_error"
    replan_from: "failed-agent"  # Planner دوباره از اینجا Plan می‌دهد
  
  - type: abort
    human_notification: true
    fallback_output: "خطا در اجرا — نیاز به بررسی دستی"
```

### 7.8 Observer — رصدکننده

Runtime باید از روز اول یک **Observer داخلی** داشته باشد — نه اینکه Reflection را به v0.15 موکول کند.

```text
Agent Started
    ↓
┌───────────────────┐
│   Observer        │
│                   │
│  Metrics:         │
│  ├─ duration_ms   │
│  ├─ token_count   │
│  ├─ model_used    │
│  ├─ retry_count   │
│  ├─ error_count   │
│  └─ quality_score │
│                   │
│  Events:          │
│  ├─ agent:started │
│  ├─ tool:called   │
│  ├─ phase:done    │
│  └─ error:occured │
└─────────┬─────────┘
          │
          ▼
    ┌──────────┐
    │ Event Bus│──→ Event Store
    └──────────┘
          │
          ▼
    ┌──────────┐
    │Reflection│  (در v0.15 از همین داده‌ها استفاده می‌کند)
    └──────────┘
```

**معماری Observer:**

```python
class Observer:
    """رصدکننده داخلی Runtime — Metrics + Events"""
    
    def on_agent_started(self, agent_id: str, phase: str, model: str):
        """ثبت شروع Agent"""
    
    def on_agent_completed(self, agent_id: str, result: dict):
        """ثبت پایان Agent با Metrics"""
    
    def on_tool_called(self, tool_id: str, duration_ms: int, success: bool):
        """ثبت فراخوانی Tool"""
    
    def on_error(self, source: str, error: str, context: dict):
        """ثبت خطا"""
    
    def get_metrics(self, workflow_id: str) -> dict:
        """گرفتن Metrics یک Workflow"""
    
    def get_timeline(self, workflow_id: str) -> list[dict]:
        """گرفتن Timeline کامل یک Workflow"""
```

**Observer چه تفاوتی با EventStream فعلی دارد؟**

| ویژگی | EventStream (فعلی) | Observer (جدید) |
|-------|-------------------|-----------------|
| **Scope** | فقط Brain | کل Runtime |
| **Metrics** | ندارد | duration, tokens, errors, quality |
| **Structured** | آزاد | Schema ثابت |
| **Query** | ندارد | get_metrics(), get_timeline() |
| **Integration** | فقط emit | Observer → Event Bus → Store |

### 7.9 Runtime Implementation Path — مسیر پیاده‌سازی

| Step | کار | تخمین |
|------|-----|-------|
| 1 | State Machine (WorkflowState class) | ۱ روز |
| 2 | **Observer** — Metrics + Events | **۱ روز** (اضافه جدید) |
| 3 | Phase Executor (اجرای sequential/parallel) | ۲ روز |
| 4 | Persistence (StorageEngine) | ۱ روز |
| 5 | Pause/Resume | ۱ روز |
| 6 | HITL integration | ۲ روز |
| 7 | Schedule (cron) | ۲ روز |
| 8 | Event triggers | ۲ روز |
| 9 | Error strategies | ۲ روز |
| 10 | Observability (metrics + events) | ۱ روز |
| 11 | API endpoints | ۱ روز |
| 12 | Desktop UI | ۲ روز |
| 13 | تست‌ها | ۳ روز |
| **جمع** | | **۲۲ روز** (+۱ روز برای Observer)

---

## 8. Memory Model — مدل حافظه

### 8.1 Five Levels of Memory — پنج سطح حافظه

حافظه در HiveOS یک لایه واحد نیست — یک **سلسله‌مراتب** است. هر سطح scope و ماندگاری متفاوتی دارد:

```
تنظیمات                     وسعت
  │                          │
  ▼                          ▼
┌──────────────────────────────────────────────┐
│   Level 5: Long-Term Memory                  │  ▲
│   حافظه بلندمدت — تاریخچه فشرده همه چیز     │  │
│   scope: ∞ · retention: برای همیشه           │  │
├──────────────────────────────────────────────┤  │
│   Level 4: Company Memory                    │  │
│   حافظه سازمانی — خط‌مشی‌ها، قوانین، ترجیحات │  │
│   scope: کل سازمان · retention: تا تغییر    │  │
├──────────────────────────────────────────────┤  │
│   Level 3: Domain Memory                     │  │
│   حافظه دامنه — دانش تخصصی هر حوزه           │  │
│   scope: یک Domain · retention: تا بروزرسانی│  │
├──────────────────────────────────────────────┤  │
│   Level 2: Agent Memory                      │  │
│   حافظه عامل — context و تجربه هر Agent      │  │
│   scope: یک Agent · retention: تا پایان سشن│  │
├──────────────────────────────────────────────┤  │
│   Level 1: Session Memory                    │  │
│   حافظه نشست — چت instant یک کاربر          │  │
│   scope: یک تعامل · retention: کوتاه‌مدت    │  │
└──────────────────────────────────────────────┘  │
                                                  ▼
ماندگاری                        سرعت دسترسی
```

### 8.2 Level 1: Session Memory

حافظه **چت instant** کاربر با سیستم:

| ویژگی | مقدار |
|-------|-------|
| **scope** | یک مکالمه کاربر-سیستم |
| **مدت** | تا پایان session (max ۲۴ ساعت) |
| **ذخیره‌سازی** | in-memory (Redis/SQLite اختیاری) |
| **محتوای اصلی** | تاریخچه پیام‌ها، context فعلی |
| **API** | `kernel.get("session").push(msg)` `kernel.get("session").get_context()` |

### 8.3 Level 2: Agent Memory

حافظه هر Agent در طول اجرای یک Workflow:

| ویژگی | مقدار |
|-------|-------|
| **scope** | یک Agent Flow در یک Execution |
| **مدت** | طول عمر Agent (از spawn تا complete) |
| **ذخیره‌سازی** | in-memory (بخشی در StorageEngine) |
| **محتوای اصلی** | ورودی phase قبل، خروجی Agentهای وابسته، ابزارهای در دسترس |
| **API** | `agent.memory.set("key", value)` `agent.memory.get("key")` |

این سطح هم‌اکنون به صورت ضمنی از طریق `depends_on` و `output_var` در Flow Engine وجود دارد — اما باید explicit شود.

### 8.4 Level 3: Domain Memory

حافظه تخصصی **هر Domain** — محتوایی که بین جلسات مختلف حفظ می‌شود:

| ویژگی | مقدار |
|-------|-------|
| **scope** | یک Domain خاص (مثلاً accounting) |
| **مدت** | تا بروزرسانی بعدی domain |
| **ذخیره‌سازی** | StorageEngine — namespace جدا |
| **API** | `domain.memory.set("tax-rates-1404", {...})` |

در وضعیت فعلی، این سطح تا حدی از طریق `DomainRegistry` و `learn()` وجود دارد — اما API استاندارد ندارد.

### 8.5 Level 4: Semantic Memory — حافظه معنایی (بین Domain و Company)

ChatGPT در نقد خود به درستی اشاره کرد که بین Domain Memory (سطح ۳) و Company Memory (سطح ۵) یک شکاف وجود دارد — **حافظه Entity-based**.

Semantic Memory نه Key-Value ساده است و نه Knowledge Graph کامل — بلکه **موجودیت‌ها و روابط پایه سازمان** را ذخیره می‌کند:

```json
{
  "entities": {
    "company_x": {
      "type": "company",
      "attributes": {
        "industry": "technology",
        "size": "50-100 employees",
        "founded": 1398
      },
      "relationships": {
        "has_project": ["project_alpha", "project_beta"],
        "preferred_vendor": ["vendor_a"],
        "has_contract": ["contract_123"]
      }
    },
    "project_alpha": {
      "type": "project",
      "attributes": {
        "budget": 50000000,
        "status": "active",
        "start_date": "1403-06-01"
      }
    }
  }
}
```

| ویژگی | مقدار |
|-------|-------|
| **scope** | یک سازمان — Entityهای اصلی |
| **مدت** | تا بروزرسانی دستی |
| **ذخیره‌سازی** | StorageEngine + JSON relationships |
| **API** | `semantic.get_entity(id)` `semantic.query_related(entity_type, relationship)` |

**تفاوت Semantic Memory با Knowledge Graph:**

| Semantic Memory (سطح ۴) | Knowledge Graph (v0.16) |
|-------------------------|------------------------|
| Entityهای اصلی و روابط مستقیم | گراف کامل با Inference |
| دستی / نیمه‌خودکار | خودکار از داده‌های Runtime |
| Query ساده (کی، چی، کجا) | Query پیچیده (الگو، مسیر، تحلیل) |
| StorageEngine | موتور گراف اختصاصی |

### 8.6 Level 5: Company Memory — حافظه سازمانی

**مهم‌ترین مزیت رقابتی HiveOS — در v0.16 ساخته می‌شود:**

حافظه **سازمانی** که بین همه Agentها و Domainها مشترک است:

```python
class CompanyMemory:
    """
    حافظه سازمانی — خط‌مشی‌ها، قوانین، تصمیمات گذشته.
    همه Agentها به این حافظه دسترسی read دارند.
    فقط Agentهای مجاز (با role معین) می‌توانند بنویسند.
    """
    
    def get_policy(self, domain: str, key: str) -> dict:
        """دریافت خط‌مشی سازمانی"""
        # مثال: company_memory.get_policy("accounting", "invoice-approval-threshold")
        # → {"amount": 50000000, "required_role": "finance-manager"}
    
    def get_decision(self, context: str) -> list[dict]:
        """یافتن تصمیمات مشابه گذشته"""
        # مثال: company_memory.get_decision("vendor-X late delivery")
        # → [{"date": "1403-10-15", "decision": "removed", "reason": "..."}]
    
    def record_decision(self, context: str, decision: dict):
        """ثبت یک تصمیم جدید برای استفاده در آینده"""
    
    def get_preference(self, domain: str, key: str) -> Any:
        """دریافت ترجیح سازمانی"""
        # مثال: company_memory.get_preference("procurement", "preferred-software-vendor")
        # → {"name": "Company X", "reason": "قیمت + پشتیبانی"}
```

**نوع داده‌هایی که در Company Memory ذخیره می‌شود:**

| دسته | مثال |
|------|-------|
| **Policies** | "فاکتورهای بالای ۵۰ میلیون نیاز به تأیید مدیر مالی" |
| **Accounting Rules** | "روش استهلاک: خط مستقیم، ۵ سال" |
| **Preferred Vendors** | "برای خرید نرم‌افزار، اول با شرکت X تماس بگیر" |
| **Previous Decisions** | "دی ۱۴۰۳: شرکت Y به خاطر تأخیر از لیست حذف شد" |
| **Risk Appetite** | "حداکثر ریسک در معاملات ارزی: ۳٪ سرمایه" |
| **Tax Strategy** | "روش بهینه کاهش مالیات در حوزه خدمات فناوری" |
| **Organizational Context** | "شرکت در مرحله رشد سریع — سرمایه‌گذاری جسورانه‌تر" |

### 8.7 Level 6: Long-Term Memory — حافظه بلندمدت

حافظه فشرده و aggregateشده از تاریخچه کامل سیستم:

| ویژگی | مقدار |
|-------|-------|
| **scope** | کل سیستم — همه Workflowها، همه Agentها |
| **مدت** | برای همیشه (تا حذف دستی) |
| **ذخیره‌سازی** | StorageEngine + فشرده‌سازی دوره‌ای |
| **API** | جستجوی تاریخی، تحلیل روندها |

### 8.8 Memory Access Rules — قوانین دسترسی

```
┌─────────────┐  read/write  ┌─────────────────┐
│ Session     │◄────────────►│ User (کاربر)     │
└──────┬──────┘              └─────────────────┘
       │
       │  read
       ▼
┌─────────────┐  read/write  ┌─────────────────┐
│ Agent       │◄────────────►│ Executing Agent  │
└──────┬──────┘              └─────────────────┘
       │
       │  read (از Domain Registry)
       ▼
┌─────────────┐              ┌─────────────────┐
│ Domain      │◄─── write ──│ Domain Admin     │
└──────┬──────┘              └─────────────────┘
       │
       │  read
       ▼
┌─────────────┐              ┌─────────────────┐
│ Company     │◄─── write ──│ Authorized Roles  │
│ Memory      │              │ (finance-manager, │
└──────┬──────┘              │  compliance, etc) │
       │                     └─────────────────┘
       │  read (all)
       ▼
┌─────────────┐
│ Long-Term   │◄─── write ──│ System (خودکار)
└─────────────┘
```

---

## 9. Event Bus — گذرگاه رویداد

### 9.1 Why Event Bus?

در وضعیت فعلی، کامپوننت‌ها یا مستقیماً هم را صدا می‌زنند (مثل `FlowEngine → Hermes subprocess`)، یا اصلاً باخبر نمی‌شوند که در کامپوننت دیگر چه گذشت. Event Bus این مشکلات را حل می‌کند:

1. **جفت‌زدایی (Decoupling):** کامپوننت‌ها فقط رویداد publish می‌کنند — نمی‌دانند چه کسی subscribe کرده
2. **گسترش‌پذیری:** اضافه کردن یک قابلیت جدید فقط نیاز به subscribe به رویدادهای موجود دارد
3. **ممیزی:** همه رویدادها در Event Store ذخیره می‌شوند — تاریخچه کامل سیستم

### 9.2 Event Schema

```json
{
  "id": "evt_h3k2j9",
  "type": "flow:phase:agent:completed",
  "source": "runtime:phase-executor",
  "timestamp": "2026-07-20T10:00:15.123Z",
  "workflow_id": "wf_abc123",
  "correlation_id": "plan_def456",
  "payload": {
    "agent_id": "financial-scraper",
    "phase": "phase-1",
    "status": "completed",
    "duration_ms": 8500,
    "result_summary": "Financial statements extracted for 3 years"
  },
  "metadata": {
    "token_cost": 1500,
    "model": "claude-sonnet-4"
  }
}
```

قواعد نام‌گذاری رویدادها:

| الگو | مثال |
|------|-------|
| `system:*` | `system:startup`, `system:shutdown` |
| `kernel:*` | `kernel:service:registered`, `kernel:service:failed` |
| `planner:*` | `planner:plan:created`, `planner:plan:rejected` |
| `runtime:*` | `runtime:workflow:started`, `runtime:phase:completed` |
| `flow:*` | `flow:step:agent:started`, `flow:step:completed` |
| `domain:*` | `domain:installed`, `domain:learning:completed` |
| `brain:*` | `brain:gate:created`, `brain:gate:approved` |
| `memory:*` | `memory:company:policy:updated` |

### 9.3 Pub/Sub API

```python
class EventBus:
    """گذرگاه رویداد مرکزی — بر اساس Pub/Sub الگو"""
    
    def publish(self, event: Event):
        """انتشار یک رویداد — همه subscriberهای مرتبط مطلع می‌شوند"""
    
    def subscribe(self, event_type: str, handler: Callable):
        """ثبت handler برای یک نوع رویداد خاص"""
    
    def subscribe_pattern(self, pattern: str, handler: Callable):
        """ثبت handler با wildcard: 'flow:*:completed'"""
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """حذف handler"""
```

### 9.4 Event Store

همه رویدادها در **Event Store** ذخیره می‌شوند (StorageEngine-backed):

| سرویس | ذخیره‌سازی | مدت |
|-------|-----------|------|
| **Current Workflow Events** | In-memory + StorageEngine | تا اتمام workflow |
| **Historical Events** | StorageEngine (فشرده) | ۳۰ روز |
| **Archived Events** | فایل JSON فشرده | ۱ سال |
| **Audit Events** | StorageEngine (غیر قابل حذف) | برای همیشه |

### 9.5 Current Brain EventStream vs Future Event Bus

| ویژگی | EventStream (فعلی) | Event Bus (هدف) |
|-------|------------------|-----------------|
| **scope** | فقط Brain | کل سیستم |
| **persistence** | StorageEngine | StorageEngine + tiered storage |
| **pub/sub** | ❌ فقط emit | ✅ subscribe + pattern |
| **correlation** | ❌ | ✅ correlation_id |
| **schema** | آزاد | استاندارد |
| **performance** | صف واحد (deque) | prioritized queue |

### 9.6 Event Sourcing Roadmap — مسیر رویدادنگاری

ChatGPT پیشنهاد داد از همین امروز **Event Sourcing** را در نظر بگیریم. Event Sourcing یعنی به جای ذخیره State فعلی، **همه رویدادهایی که به State منجر شده‌اند** ذخیره شوند.

```
State → Events → Rebuild State (از روی Events)
```

| مرحله | توضیح | زمان |
|-------|-------|------|
| **امروز** | Event Bus — انتشار رویدادها | v0.14 |
| **v0.15** | Event Store با قابلیت Query | |
| **v0.17** | Event Sourcing کامل — بازسازی State از Events | |
| **v2.0** | Event Sourcing + CQRS | بعد از v1.0 |

**چرا از امروز Event Sourcing نمی‌کنیم؟**

Event Sourcing جذاب است اما:
1. **پیچیدگی:** Versioning، Snapshot، Rebuild State نیاز به زیرساخت جدی دارد
2. **برای v1.0 با یک کاربر:** overhead بیش از نیاز است
3. **Event Bus فعلی:** ۸۰٪ فایده Event Sourcing را با ۲۰٪ هزینه می‌دهد

**تصمیم:** Event Bus (v0.14) → Event Store با Query (v0.15) → Event Sourcing (v0.17 → v2.0)

---

## 10. Tool Bus — گذرگاه ابزار

### 10.1 Current Problem

در وضعیت فعلی:
- هر Agent مستقیماً `subprocess.run(["hermes", "chat", ...])` صدا می‌زند
- ابزارها در `agent.tools` لیست می‌شوند اما runtime تضمین نمی‌کند که ابزار در دسترس است
- هیچ Schema استانداردی برای تعریف ابزار وجود ندارد
- امکان اشتراک ابزار بین Agentها محدود است

### 10.2 Tool Bus Architecture

Tool Bus یک **لایه انتزاع** بین Agent و ابزارهاست:

```
Agent
  │
  │  Tool Call: {"tool": "web-search", "args": {"query": "..."}}
  ▼
┌─────────────────────────────────────────┐
│           Tool Bus                       │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │ Registry │  │ Validator│  │ Cache │  │
│  │ (کشف)    │  │ (اعتبار) │  │ (کش) │  │
│  └──────────┘  └──────────┘  └──────┘  │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         Rate Limiter                ││
│  │         محدودکننده نرخ              ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │         Security Layer              ││
│  │   مجوزها، اعتبارسنجی ورودی/خروجی    ││
│  └─────────────────────────────────────┘│
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐ ┌────────┐ ┌────────────┐
│ Built-in│ │ Domain │ │ 3rd Party │
│ Tools  │ │ Tools  │ │ Tools     │
└────────┘ └────────┘ └────────────┘
```

### 10.3 Tool Schema

```json
{
  "tool_id": "web-search",
  "name": "جستجوی وب",
  "description": "جستجوی اطلاعات در اینترنت",
  "version": "1.0.0",
  "source": "built-in",
  "auth_required": false,
  
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "عبارت جستجو",
        "required": true
      },
      "limit": {
        "type": "integer",
        "description": "تعداد نتایج",
        "default": 5,
        "minimum": 1,
        "maximum": 50
      }
    }
  },
  
  "output_schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "url": {"type": "string"},
        "description": {"type": "string"}
      }
    }
  },
  
  "rate_limit": {
    "max_per_minute": 30,
    "max_per_hour": 500
  },
  
  "cost": {
    "per_call": 0.001,
    "currency": "USD"
  },
  
  "timeout": 15
}
```

### 10.4 Built-in Tools — ابزارهای پیش‌فرض

| ابزار | توضیح | وضعیت |
|-------|-------|--------|
| `web-search` | جستجوی وب | ✅ موجود |
| `web-extract` | استخراج محتوای صفحه | ✅ موجود |
| `read-file` | خواندن فایل | ✅ موجود |
| `write-file` | نوشتن فایل | ✅ موجود |
| `execute-python` | اجرای کد Python | ✅ موجود |
| `database-query` | پرس‌وجوی SQLite | ✅ موجود |
| `memory-read` | خواندن از حافظه | 🔧 در دست ساخت |
| `memory-write` | نوشتن در حافظه | 🔧 در دست ساخت |
| `notify` | ارسال اعلان (Telegram, Slack, ...) | ✅ موجود |
| `schedule` | زمان‌بندی وظایف | ❌ نیاز به ساخت |

ابزارهای دامنه (مثلاً برای Accounting):

| ابزار | توضیح | وضعیت |
|-------|-------|--------|
| `financial-statement-reader` | استخراج داده از صورت‌های مالی PDF | ✅ موجود |
| `ratio-analyzer` | محاسبه نسبت‌های مالی | ✅ موجود |
| `tax-calculator` | محاسبه مالیات بر اساس قوانین ایران | ❌ needs data |
| `payslip-generator` | تولید فیش حقوقی | ❌ needs data |

### 10.5 Tool Bus Implementation Path

| Step | کار | تخمین |
|------|-----|-------|
| 1 | Tool Schema تعریف | ۱ روز |
| 2 | Tool Registry (کشف + ثبت) | ۱ روز |
| 3 | Tool Validator | ۱ روز |
| 4 | Rate Limiter | ۱ روز |
| 5 | Security Layer | ۲ روز |
| 6 | Cache Layer | ۱ روز |
| 7 | Adapt Built-in Tools به Schema جدید | ۲ روز |
| 8 | تست‌ها | ۲ روز |
| **جمع** | | **۱۱ روز** |

### 10.6 Stateless Tools — ابزارهای بدون حالت

ChatGPT تأکید کرد: **"من Toolها را Stateless نگه می‌دارم. تمام State داخل Runtime باشد."**

این اصل مهمی است:
- **Toolها** داده را می‌گیرند، پردازش می‌کنند، نتیجه برمی‌گردانند — هیچ State داخلی ندارند
- **Runtime** تمام State (Context, Metrics, Results) را مدیریت می‌کند
- **Memory** State پایدار را ذخیره می‌کند

```python
# درست — Tool Stateless
class WebSearchTool(BaseTool):
    async def run(self, query: str) -> dict:
        return await search_web(query)  # فقط ورودی→خروجی

# نادرست — Tool با State داخلی
class BadTool(BaseTool):
    def __init__(self):
        self.cache = {}  # ❌ State در Tool
    async def run(self, query: str) -> dict:
        if query in self.cache:
            return self.cache[query]  # ❌
```

**استثنا:** Rate Limiter و Cache در Tool Bus (نه خود Tool) می‌توانند stateful باشند — چون اینها زیرساخت هستن، نه منطق ابزار.

---

## 11. Domain SDK — کیت توسعه دامنه

### 11.1 Purpose — هدف

Domain SDK مجموعه‌ای از ابزارها، کلاس‌ها، و CLI commands است که به یک توسعه‌دهنده اجازه می‌دهد **یک Domain جدید برای HiveOS بسازد** بدون اینکه نیاز به شناخت عمیق از هسته داشته باشد.

### 11.2 SDK Components

```
domain-sdk/
├── templates/              # قالب‌های آماده
│   ├── basic-domain/       # دامنه ساده
│   ├── knowledge-domain/   # دامنه دانش‌محور (مثل Accounting)
│   └── service-domain/     # دامنه سرویس‌محور (مثل Notification)
├── cli/                    # CLI tools
│   ├── hive domain init    # ایجاد دامنه جدید
│   ├── hive domain build   # اعتبارسنجی و build
│   ├── hive domain test    # تست دامنه
│   └── hive domain publish # انتشار دامنه
├── core/                   # کلاس‌های پایه
│   ├── BaseDomain.py       # کلاس پایه دامنه
│   ├── BaseAgent.py        # کلاس پایه agent
│   ├── BaseTool.py         # کلاس پایه ابزار
│   └── BaseFlow.py         # کلاس پایه flow
└── validators/             # اعتبارسنجی
    ├── validate_manifest.py
    └── validate_schema.py
```

### 11.3 SDK Usage Example — مثال استفاده

```bash
# 1. ایجاد دامنه جدید
hive domain init accounting
# Creates: domains/accounting/
# ├── domain.yaml
# ├── agents/
# ├── flows/
# ├── tools/
# └── knowledge/

# 2. تعریف agent
hive domain add-agent accounting financial-analyst

# 3. تعریف flow
hive domain add-flow accounting financial-report

# 4. اعتبارسنجی
hive domain build accounting

# 5. تست
hive domain test accounting

# 6. نصب در HiveOS
hive domain install accounting

# 7. انتشار (برای رجیستری عمومی)
hive domain publish accounting
```

### 11.4 Package Format — فرمت بسته دامنه

دامنه‌ها به صورت `.tar.gz` یا یک repository مستقل توزیع می‌شوند:

```yaml
# domain.yaml — مانیفست دامنه
domain:
  name: accounting
  version: 1.0.0
  label:
    fa: "حسابداری ایران"
    en: "Iranian Accounting"
  description:
    fa: "دامنه تخصصی حسابداری ایران شامل قوانین، استانداردها و محاسبات"
    en: "Specialized domain for Iranian accounting"
  
  author: HiveOS Team
  license: MIT
  
  engine_requirement: ">= 0.12.0"
  
  dependencies:
    - general >= 1.0.0
  
  capabilities:
    - financial-statement-analysis
    - tax-calculation
    - payroll-processing
    - audit-support
  
  entry_points:
    agents: agents/blueprints/
    flows: flows/
    knowledge: knowledge/
    tools: tools/
```

### 11.5 SDK Classes

```python
from hiveos.sdk import BaseDomain, BaseAgent, BaseTool

class AccountingDomain(BaseDomain):
    """دامنه حسابداری — رجیستر شده در Domain Registry"""
    
    name = "accounting"
    version = "1.0.0"
    dependencies = ["general"]


class FinancialAnalyst(BaseAgent):
    """یک agent برای تحلیل صورت‌های مالی"""
    
    name = "financial-analyst"
    domain = "accounting"
    tools = ["financial-statement-reader", "ratio-analyzer"]
    
    async def run(self, task: str, context: dict) -> dict:
        # اجرای تحلیل مالی
        statements = await self.call_tool("financial-statement-reader", {
            "path": context["financial_statement_path"]
        })
        ratios = await self.call_tool("ratio-analyzer", {
            "data": statements
        })
        return {"ratios": ratios, "analysis": self._interpret(ratios)}


class FinancialStatementReader(BaseTool):
    """ابزار خواندن صورت‌های مالی از PDF"""
    
    name = "financial-statement-reader"
    description = "Extract financial data from PDF statements"
    
    parameters = {
        "path": {"type": "string", "required": True}
    }
    
    async def run(self, path: str) -> dict:
        # منطق استخراج
        return {"balance_sheet": ..., "income_statement": ...}
```

---

## 12. Plugin API — رابط برنامه‌نویسی افزونه

### 12.1 Philosophy

Plugin API به توسعه‌دهندگان شخص ثالث اجازه می‌دهد بدون تغییر در هسته HiveOS، قابلیت اضافه کنند. مهم‌ترین تفاوت Plugin API با Domain SDK:

| Domain SDK | Plugin API |
|-----------|-----------|
| برای ساخت Domainهای جدید | برای گسترش هر بخش از سیستم |
| قراردادهای مشخص (manifest, agents, flows) | آزاد — می‌تواند هر نوع توسعه‌ای باشد |
| نصب از طریق Domain Registry | نصب از طریق Plugin Manager |

### 12.2 Plugin Types

| نوع | توضیح | مثال |
|-----|-------|------|
| **Tool Plugin** | ابزار جدید اضافه می‌کند | `stock-market-api` |
| **UI Plugin** | صفحه جدید به Dashboard اضافه می‌کند | `custom-chart` |
| **Trigger Plugin** | نوع Trigger جدید | `slack-command` |
| **Auth Plugin** | روش تأیید هویت جدید | `saml-sso` |
| **Storage Plugin** | backend ذخیره‌سازی جدید | `postgres-storage` |
| **Notification Plugin** | کانال اعلان جدید | `whatsapp-notify` |

### 12.3 Plugin Lifecycle

```
کشف (Discovery)
    │
    ▼
ثبت (Registration)
    │
    ▼
فعال‌سازی (Activation)
    │
    ▼
اجرا (Runtime)
    │
    ▼
غیرفعال‌سازی (Deactivation)
    │
    ▼
حذف (Removal)
```

### 12.4 Plugin Manifest

```yaml
# plugin.yaml
plugin:
  name: stock-market-api
  version: 1.0.0
  type: tool
  
  author: Third Party Dev
  
  engine_requirement: ">= 0.14.0"
  
  hooks:
    register_tools:
      - id: stock-price
        handler: tools/stock_price.py
  
  config:
    api_key_env: STOCK_API_KEY
    rate_limit: 100  # calls per minute
```

### 12.5 Hooks — نقاط اتصال

هر Plugin می‌تواند در نقاط مشخصی از سیستم "hook" شود:

```python
class StockMarketPlugin(Plugin):
    """Plugin بورس — ابزار جستجوی قیمت سهام"""
    
    hooks = {
        # بعد از ثبت Plugin در سیستم
        "on_activate": "self._setup_api",
        
        # قبل از اجرای هر ابزار از این Plugin
        "before_tool_call": "self._check_rate_limit",
        
        # بعد از اتمام هر ابزار
        "after_tool_call": "self._log_usage",
        
        # در هنگام shutdown
        "on_deactivate": "self._cleanup",
        
        # افزودن endpoint جدید به Dashboard API
        "register_api_routes": "self._add_routes",
    }
```

---

## 13. Bridge to Future Versions — پل به نسخه‌های آینده

این بخش نشان می‌دهد هر نسخه آینده از کدام لایه‌های معماری استفاده می‌کند و چه خروجی‌هایی تحویل می‌دهد.

### 13.1 Version Map

```
نسخه    لایه‌ها          خروجی اصلی
──────  ───────────────  ───────────────────────────────
v0.12   معماری            ۲۰ صفحه سند معماری + Brain Runtime
                          + Goal System

v0.13   Goal + Planner    Goal Service · 3 سطح planning
                          · Goal Validator · Priority
                          · Plan Validator · API · Desktop UI
                          · Capability Matcher

v0.14   Runtime + Observer State Machine · Phase Executor
                          · Pause/Resume · HITL
                          · Observer (Metrics + Events)
                          · Schedule · Error Strategies
                          · Event Bus پایه

v0.15   Reflection        ۶ ماژول Reflection
                          · Success/Fail Analyzer
                          · Mistake Pattern Detection
                          · Improvement Suggestion
                          · Learning Persistence
                          · Cross-agent Knowledge Transfer
                          · Performance Trend Analysis
                          · Event Store Query

v0.16   Knowledge Graph   ۳ لایه گراف
    (+ Semantic Memory)   · Entity Extraction
                          · Relationship Mapping
                          · Query Engine
                          · Visualization
                          · Semantic Memory API
                          · Cross-Domain Linking

v0.17   Company Memory    ۶ دسته حافظه سازمانی
                          · Company Memory Service
                          · Policy Engine
                          · Decision Logger
                          · Preference Store
                          · Event Sourcing پایه
                          · Integration با Planner + Runtime + Graph

v1.0    یکپارچه‌سازی همه   Cognitive Cycle کامل
                          · Brain Runtime چرخه ۸ مرحله‌ای
                          · Adaptation Engine
                          · اولین Release پایدار عمومی
```

### 13.2 Updated Roadmap — مسیر اصلاح‌شده

بر اساس نقدهای ChatGPT و تصمیمات معماری تیم:

```
v0.12 ─── Architecture Document (همین سند)
   │
   ▼
v0.13 ─── Goal System + Planner
   │
   ▼
v0.14 ─── Runtime + Observer + Event Bus پایه
   │
   ▼
v0.15 ─── Reflection Engine + Event Store Query
   │
   ▼
v0.16 ─── Knowledge Graph + Semantic Memory
   │
   ▼
v0.17 ─── Company Memory + Event Sourcing پایه
   │
   ▼
v1.0  ─── Integration + Brain Runtime Cognitive Cycle کامل
```

**چرا Knowledge Graph جلوتر از Company Memory آمده؟**

ChatGPT پرسید: "چرا Knowledge Graph را آخر می‌گذاری؟ Reflection بدون Graph فقط Log تحلیل می‌کند. ولی با Graph می‌تواند الگوها را کشف کند."

پاسخ: حق با اوست. ترتیب جدید:
1. **Observer** (v0.14) — داده جمع می‌کند
2. **Reflection** (v0.15) — از داده یاد می‌گیرد
3. **Knowledge Graph** (v0.16) — یادگیری‌ها را ساختار می‌دهد
4. **Company Memory** (v0.17) — ساختارها را به خط‌مشی تبدیل می‌کند

### 13.3 Cogntive Cycle Completion Roadmap

| نسخه | چرخه شناختی | 
|------|-------------|
| v0.13 | Perception + Reasoning + Planning |
| v0.14 | **Execute + Observe** |
| v0.15 | **Evaluate + Reflect** |
| v0.16 | **Learn** (از طریق Graph) |
| v0.17 | **Adapt + Memory Update** |
| v1.0 | **چرخه کامل — Adaptation Engine** |

### 13.4 Dependencies Between Layers — وابستگی بین لایه‌ها

```
           v0.12
             │
             ▼
┌──────────────────────┐
│       v0.13          │
│  Goal + Planner      │
└──────────┬───────────┘
           │ Goal + Plan
           ▼
┌──────────────────────┐
│       v0.14          │
│  Runtime + Observer  │◄── Plan را اجرا می‌کند + Metrics جمع می‌کند
│  Event Bus پایه      │
└──────────┬───────────┘
           │ Execution + Observation
           ▼
┌──────────────────────┐
│       v0.15          │
│     Reflection       │◄── از Observer Metrics یاد می‌گیرد
│  Event Store Query   │
└──────────┬───────────┘
           │ Patternها
           ▼
┌──────────────────────┐
│       v0.16          │
│  Knowledge Graph     │◄── Reflection Patternها را ساختار می‌دهد
│  Semantic Memory     │
└──────────┬───────────┘
           │ Entityها + روابط
           ▼
┌──────────────────────┐
│       v0.17          │
│  Company Memory      │◄── از Graph Policy استخراج می‌کند
│  Event Sourcing پایه │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│        v1.0          │
│  Cognitive Cycle     │
│  کامل + Integration  │
└──────────────────────┘
```

### 13.5 What NOT to Build — چه چیزی ساخته نمی‌شود

تا نسخه v1.0، این موارد **ساخته نمی‌شوند**:

| مورد | دلیل |
|------|-------|
| **CRM** | هسته هنوز شکل نگرفته — CRM یک دامنه است، نه یک لایه |
| **HR Module** | دامنه منابع انسانی بعداً به عنوان Domain اضافه می‌شود |
| **ERP Integration** | API یکپارچه برای اتصال به ERP بعد از v1.0 |
| **Mobile App** | تمرکز روی دسکتاپ و PWA |
| **Public Domain Registry** | ابتدا Domain SDK باید تثبیت شود |
| **Multi-language Support** | فقط فارسی و انگلیسی در v1.0 |
| **Real-time Collaboration** | بعد از v1.0 |

---

## 14. Architecture Decision Records — تصمیمات معماری

### 14.1 ADR-001: Planner Before Runtime

**وضعیت:** ✅ پذیرفته شده
**زمینه:** ChatGPT پیشنهاد داده بود Runtime قبل از Planner ساخته شود. تیم معماری تصمیم گرفت اول Planner ساخته شود.
**دلیل:** Runtime باید Plan را اجرا کند. اگر Runtime بدون Planner ساخته شود، همان execution engine ساده فعلی می‌شود — فقط با state management بهتر.
**پیامد:** Timeline v0.13 = Planner, v0.14 = Runtime.

### 14.2 ADR-002: Event Bus replaces Brain EventStream

**وضعیت:** ✅ پذیرفته شده
**زمینه:** Brain EventStream در حال حاضر فقط رویدادهای Brain را مدیریت می‌کند. نیاز به یک Event Bus مرکزی برای کل سیستم وجود دارد.
**راهکار:** Event Bus گسترش‌یافته EventStream فعلی خواهد بود — با pub/sub + correlation + schema استاندارد.
**پیامد:** EventStream فعلی به تدریج جایگزین می‌شود. نیازی به بازنویسی کامل نیست — می‌توان Event Bus را به عنوان wrapper نوشت.

### 14.3 ADR-003: Memory Model — 5 Levels → 6 Levels with Semantic Memory

**وضعیت:** ✅ پذیرفته شده
**زمینه:** نیاز به ساختار حافظه چندسطحی. ChatGPT پیشنهاد اضافه کردن Semantic Memory (Entity-based) بین Domain و Company Memory را داد.
**راهکار:** ۶ سطح Session → Agent → Domain → **Semantic** → Company → Long-term. Semantic Memory موجودیت‌ها و روابط پایه سازمان را ذخیره می‌کند — پل بین Key-Value Memory و Knowledge Graph.
**پیامد:** Semantic Memory در v0.12 طراحی و در v0.16 همراه با Knowledge Graph پیاده‌سازی می‌شود.

### 14.4 ADR-004: Tool Bus with Registry + Rate Limiter + Security

**وضعیت:** ✅ پذیرفته شده
**زمینه:** ابزارها در وضعیت فعلی فاقد schema استاندارد و کنترل دسترسی هستند.
**راهکار:** Tool Bus به عنوان لایه میانی با Registry (کشف)، Validator (اعتبارسنجی)، Rate Limiter (محدودکننده نرخ)، و Security Layer (امنیت).
**پیامد:** همه ابزارهای موجود باید به Schema جدید مهاجرت کنند (تغییر backward-compatible).

### 14.5 ADR-005: Domain SDK separates from Plugin API

**وضعیت:** ✅ پذیرفته شده
**زمینه:** Domain SDK و Plugin API هر دو به توسعه‌دهندگان کمک می‌کنند قابلیت اضافه کنند اما دامنه و هدف متفاوتی دارند.
**راهکار:** دو API مجزا — Domain SDK برای ساخت Domainهای جدید با قراردادهای مشخص، Plugin API برای گسترش هر بخش از سیستم.
**پیامد:** Domain SDK در v0.12 طراحی می‌شود (همین سند) و در v0.17 بعد از تثبیت Runtime پیاده‌سازی می‌شود.

### 14.6 ADR-006: English + Persian as Primary Languages

**وضعیت:** ✅ پذیرفته شده
**زمینه:** مخاطبان HiveOS هم فارسی‌زبان و هم انگلیسی‌زبان هستند.
**راهکار:** تمام مستندات معماری دو زبانه. کد و API به انگلیسی. مستندات کاربری به فارسی.
**پیامد:** این سند و تمام اسناد معماری بعدی دو زبانه نوشته می‌شوند.

### 14.7 ADR-007: Kernel Minimalism — هسته کمترین مسئولیت

**وضعیت:** ✅ پذیرفته شده
**زمینه:** وسوسه‌انگیز است که هسته کارهای بیشتری انجام دهد (مثلاً Planning یا Scheduling).
**راهکار:** هسته فقط StorageEngine + Service Registry + Config + Logging + Lifecycle. هر چیز دیگر یک سرویس مستقل است.
**پیامد:** هسته نازک باقی می‌ماند و هر لایه به صورت مستقل قابل تست و جایگزینی است.

### 14.8 ADR-008: StorageEngine Remains SQLite

**وضعیت:** ✅ پذیرفته شده (برای v1.0)
**زمینه:** انتخاب backend ذخیره‌سازی.
**راهکار:** SQLite از طریق StorageEngine فعلی برای v1.0 کافی است. Plugin API امکان اضافه کردن PostgreSQL, Redis و غیره را بعداً فراهم می‌کند.
**پیامد:** نیاز به schema migration system قوی‌تر — فعلاً MigrationRunner ساده موجود کافی است.

### 14.9 ADR-009: Goal System as First-Class Entity

**وضعیت:** ✅ پذیرفته شده (جدید — پس از نقد ChatGPT)
**زمینه:** در معماری قبلی، "کاربر یه چیزی می‌گفت" مستقیماً به Planner می‌رفت. Goal به عنوان موجودیت مستقل وجود نداشت.
**راهکار:** Goal یک First-Class Entity با type, priority, deadline, budget, risk, owner, dependencies, success_criteria. Goal System شامل GoalService برای CRUD + Validation + Priority Scheduling + Cost Estimation.
**پیامد:** Planner دیگر مستقیماً Prompt را نمی‌شکند — Goal را می‌شکند. هر Mission (بستن ماهانه، تحلیل مالی) اول به Goal تبدیل می‌شود و بعد به Planner داده می‌شود.

### 14.10 ADR-010: Brain Runtime Cognitive Cycle

**وضعیت:** ✅ پذیرفته شده (جدید — پس از نقد ChatGPT)
**زمینه:** Brain در معماری قبلی فقط EventStream + DecisionTracer + ApprovalGate بود — فاقد هویت شناختی منسجم.
**راهکار:** Brain Runtime به عنوان **چارچوب شناختی مرکزی** با چرخه ۸ مرحله‌ای: Perceive → Reason → Plan → Execute + Observe → Evaluate → Reflect → Memory Update → Adapt. Planner, Runtime, Observer, Reflection, Memory و Learning زیر مجموعه Brain Runtime هستند.
**پیامد:** معماری از "مجموعه کامپوننت‌های خوب" به "سیستم شناختی منسجم" تبدیل می‌شود. Timeline پیاده‌سازی در ۵ نسخه (v0.13 تا v1.0).

### 14.11 ADR-011: Observer is Part of Runtime

**وضعیت:** ✅ پذیرفته شده (جدید — پس از نقد ChatGPT)
**زمینه:** Runtime در معماری قبلی Reflection را به v0.15 موکول کرده بود — بدون Observer داخلی.
**راهکار:** Observer از روز اول Runtime (v0.14) Metrics + Events را جمع می‌کند. Reflection (v0.15) از داده‌های Observer استفاده می‌کند. Observer شامل: duration_ms, token_count, model_used, retry_count, error_count, quality_score.
**پیامد:** تاخیر در Observer وجود ندارد. Reflection از داده‌های از قبل موجود استفاده می‌کند.

### 14.12 ADR-012: Knowledge Graph Before Company Memory

**وضعیت:** ✅ پذیرفته شده (جدید — پس از نقد ChatGPT)
**زمینه:** ChatGPT پرسید: "چرا Knowledge Graph را آخر می‌گذاری؟ Reflection بدون Graph فقط Log تحلیل می‌کند."
**راهکار:** ترتیب جدید: Observer (v0.14) → Reflection (v0.15) → Knowledge Graph (v0.16) → Company Memory (v0.17). Knowledge Graph به Reflection قدرت کشف الگو می‌دهد. Company Memory از هر دو تغذیه می‌کند.
**پیامد:** Timeline تغییر کرد: v0.15 Reflection → v0.16 Knowledge Graph → v0.17 Company Memory.

---

## Appendix A: Glossary — واژه‌نامه

| انگلیسی | فارسی | توضیح |
|---------|-------|-------|
| **Agent** | عامل | یک موجودیت هوش مصنوعی که وظیفه‌ای را انجام می‌دهد |
| **Blueprint** | طرحواره | تعریف نوع و قابلیت‌های یک Agent |
| **Brain Runtime** | زمان اجرای شناختی | چارچوب شناختی مرکزی با چرخه Perceive → Reason → Plan → Execute+Observe → Evaluate → Reflect → Memory Update → Adapt |
| **Company Memory** | حافظه سازمانی | حافظه مشترک بین همه Agentها برای خط‌مشی‌ها و تصمیمات |
| **DAG** | گراف جهتی بدون دور | Directed Acyclic Graph — مدل وابستگی‌ها |
| **Domain** | دامنه | یک حوزه تخصصی از دانش (مثل حسابداری، مالیات) |
| **Domain SDK** | کیت توسعه دامنه | ابزارهای ساخت Domain جدید |
| **Event Bus** | گذرگاه رویداد | سیستم Pub/Sub مرکزی برای ارتباط کامپوننت‌ها |
| **Event Sourcing** | رویدادنگاری | ذخیره همه رویدادها به جای State — بازسازی State از Events |
| **Execution Plan** | برنامه اجرا | خروجی Planner — یک DAG کامل از agentها و وابستگی‌ها |
| **Flow** | جریان | یک گردش کار چندمرحله‌ای |
| **Goal** | هدف | یک موجودیت مستقل شامل mission, priority, deadline, budget, risk, owner, dependencies, success_criteria |
| **Goal System** | سیستم هدف | سرویس مدیریت چرخه حیات Goalها — ایجاد، اعتبارسنجی، اولویت‌بندی، تخمین هزینه |
| **HITL** | انسان در حلقه | Human in the Loop — نقاط تأیید انسانی |
| **Kernel** | هسته | کمترین مجموعه سرویس‌های بنیادی |
| **Knowledge Graph** | گراف دانش | ارتباط بین موجودیت‌های سازمانی با قابلیت Inference |
| **Observer** | رصدکننده | جزء داخلی Runtime برای جمع‌آوری Metrics و Events در لحظه |
| **Planner** | برنامه‌ریز | کامپوننتی که Goal را به Plan تبدیل می‌کند |
| **Plugin** | افزونه | توسعه شخص ثالث برای گسترش سیستم |
| **Reflection** | بازاندیشی | یادگیری از اجراهای گذشته — تحلیل الگوهای موفقیت و شکست |
| **Runtime** | زمان اجرا | کامپوننتی که Plan را اجرا و مدیریت می‌کند |
| **Semantic Memory** | حافظه معنایی | حافظه entity-based بین Domain و Company — موجودیت‌ها و روابط پایه سازمان |
| **StorageEngine** | موتور ذخیره‌سازی | لایه persistence مبتنی بر SQLite |
| **Tool** | ابزار | قابلیت قابل استفاده توسط Agent (Stateless) |
| **Tool Bus** | گذرگاه ابزار | لایه مدیریت و امنیت ابزارها — Stateless, Registry, Validator, Rate Limiter |
| **Workflow** | گردش کار | یک اجرای کامل از یک Goal |

---

## Appendix B: Current File Map — نقشه فایل‌های فعلی

```
src/hiveos/
├── __init__.py
├── cli.py                  # CLI main entry
├── dsl.py                  # Flow DSL parser
├── engine.py               # Flow Engine (current)
├──
├── brain/                  # Brain — Event Stream, Decision Tracer, Approval Gate
│   ├── event_stream.py
│   ├── decision_tracer.py
│   └── approval_gate.py
├── cli/                    # CLI commands
│   ├── main.py
│   ├── run.py
│   └── build.py
├── dashboard/              # FastAPI Dashboard
│   └── server.py
├── desktop/                # pywebview Desktop Shell
│   └── app.py
├── domain/                 # Domain Registry
│   ├── manager.py
│   └── registry.py
├── learning/               # Learning — Logger + Analytics
│   ├── logger.py
│   └── analytics.py
├── license/                # Licensing
├── mothership/             # Mothership — Agent Registry, Task Router, Comms
│   ├── agent_registry.py
│   ├── task_router.py
│   ├── communication_bus.py
│   ├── resilience.py
│   └── server.py
├── playground/             # Playground — Canvas, Component Engine
│   ├── playground.py
│   ├── component_engine.py
│   ├── runner.py
│   └── library.py
├── registry/               # Package Registry
├── storage/                # StorageEngine
│   ├── engine.py
│   └── migrations.py
├── sync/                   # Knowledge Sync
├── update/                 # Auto-updater
├── utils/                  # Utilities
│   ├── config.py
│   ├── knowledge.py
│   └── validator.py
└── workspace/              # Multi-tenant Workspaces
```

---

> **نویسنده:** تیم معماری HiveOS — جولای ۲۰۲۶
> 
> **نسخه:** v0.12 (پیشنویس معماری)
> 
> **فایل‌های مرتبط:**
> - `docs/02-Architecture/01-high-level-arch.md` — نمای کلی معماری قبلی
> - `docs/02-Architecture/03-domain-plugin-system.md` — معماری Domain Plugin
> - `docs/02-Architecture/04-architecture-v1.0.en.md` — نسخه انگلیسی این سند

# الگوهای Orchestration در سیستم‌های چندعامله (Multi-Agent Systems)

> **مسیر:** `docs/06-Research/agents/02-Multi-Agent-Systems/01-orchestration-patterns.md`
> **آخرین به‌روزرسانی:** 2026-07-16
> **منابع:** arXiv 2601.13671, Galileo.ai, Microsoft Azure, HiveOS Architecture

---

## فهرست

1. [مقدمه: Orchestration چیست؟](#intro)
2. [سه توپولوژی اصلی هماهنگی](#topologies)
   - [متمرکز (Centralized)](#centralized)
   - [غیرمتمرکز (Decentralized)](#decentralized)
   - [سلسله‌مراتبی (Hierarchical)](#hierarchical)
3. [پروتکل‌های ارتباطی](#protocols)
   - [MCP (Model Context Protocol)](#mcp)
   - [A2A (Agent-to-Agent)](#a2a)
   - [مقایسه MCP و A2A](#mcp-vs-a2a)
4. [لایه Orchestration در معماری](#orchestration-layer)
5. [پیاده‌سازی در HiveOS](#hiveos)
   - [Mothership](#mothership)
   - [Task Router](#task-router)
   - [Communication Bus](#comm-bus)
   - [Agent Registry](#agent-registry)
6. [الگوهای عملی Orchestration](#patterns)
   - [Supervisor Pattern](#supervisor)
   - [Event-Driven Choreography](#event-driven)
   - [Hybrid Orchestration](#hybrid)
   - [Pipeline/Sequential](#pipeline)
   - [Swarm Pattern](#swarm)
7. [فریمورک‌های مطرح](#frameworks)
8. [نکات کلیدی (Key Takeaways)](#takeaways)
9. [منابع](#references)

---

## ۱. مقدمه: Orchestration چیست؟ {#intro}

**Orchestration** در سیستم‌های چندعامله (Multi-Agent Systems یا MAS) به معنای **هماهنگی، برنامه‌ریزی و کنترل** تعاملات بین agentهای مستقل برای دستیابی به یک هدف مشترک است. بدون orchestration، حتی capabilityترین agentها نیز با مشکلات زیر مواجه می‌شوند:

- **تداخل وظایف (Task Conflict):** چند agent روی یک کار تکراری وقت می‌گذارند
- **ناسازگاری منطقی (Logical Inconsistency):** خروجی agentها با یکدیگر هماهنگ نیست
- **انحراف از هدف (Objective Drift):** agentها در مسیرهای نامرتبط گم می‌شوند
- **اتلاف منابع (Resource Waste):** محاسبات موازی بی‌نتیجه

> **تعریف:** Orchestration لایه‌ای از control plane است که agentها را به یک جمعیت هدف‌مند و منسجم (coherent collective) تبدیل می‌کند. این لایه اهداف سطح بالا را به subtaskهای قابل اجرا تجزیه می‌کند، ترتیب اجرا را تعیین می‌کند، و تضمین می‌کند هر خروجی با policy، context و استانداردهای کیفی همخوانی دارد.

### تکامل سیستم‌های Agentic

```text
┌──────────────────────────────────────────────────────────────────┐
│                   تکامل سیستم‌های Agentic                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Single Agent        ──→    Loosely Coupled MAS    ──→    Orchestrated MAS
│  ┌─────────────┐            ┌─────────────────┐          ┌─────────────────┐
│  │  monolithic  │            │  A1 ←→ A2 ←→ A3 │          │  Orchestrator   │
│  │  narrow task │            │  independent     │          │  ┌───────────┐  │
│  │  no coord.   │            │  minimal coord.  │          │  │ Planning  │  │
│  └─────────────┘            └─────────────────┘          │  │ Execution │  │
│                                                            │  │ Control   │  │
│  مثال:                                                    │  │ Quality   │  │
│  چت‌بات پشتیبانی  →  چند agent تحقیقاتی  →  سیستم تحت‌نویسی │  └───────────┘  │
│                     با همکاری آزاد        با orchestration   └─────────────────┘
│                                                                   │
│  ویژگی: task-specific    ویژگی: collaboration     ویژگی: governance
│           بدون overhead         overhead کم      + accountability
└──────────────────────────────────────────────────────────────────┘
```

---

## ۲. سه توپولوژی اصلی هماهنگی {#topologies}

سه الگوی اصلی برای orchestration agentها وجود دارد. انتخاب توپولوژی مناسب به عواملی مانند مقیاس سیستم، نیاز به **flexibility**, **accountability** و **fault tolerance** بستگی دارد.

### ۲.۱ توپولوژی متمرکز (Centralized Orchestration) {#centralized}

در این مدل، یک **Orchestrator مرکزی** تمام تصمیمات را می‌گیرد: کدام agent چه کاری انجام دهد، به چه ترتیبی، و با چه ورودی‌هایی.

```text
┌─────────────────────────────────────────────────────────────┐
│                    توپولوژی متمرکز (Centralized)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                     ┌──────────────┐                         │
│                     │ ORCHESTRATOR │                         │
│                     │  (Central)   │                         │
│                     └──────┬───────┘                         │
│                            │                                  │
│        ┌───────────────────┼───────────────────┐              │
│        │                   │                   │              │
│        ▼                   ▼                   ▼              │
│  ┌──────────┐       ┌──────────┐        ┌──────────┐         │
│  │ Agent A  │       │ Agent B  │        │ Agent C  │         │
│  │ (Worker) │       │ (Worker) │        │ (Worker) │         │
│  └──────────┘       └──────────┘        └──────────┘         │
│        │                   │                   │              │
│        └───────────────────┼───────────────────┘              │
│                            │                                  │
│                     ┌──────▼───────┐                         │
│                     │   Result     │                         │
│                     │ Consolidator │                         │
│                     └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

**مزایا:**
- **کنترل کامل (Full Control):** orchestrator همه چیز را می‌بیند و کنترل می‌کند
- **تصمیم‌گیری ساده:** بدون نیاز به negotiation بین agentها
- **قابلیت ردیابی (Traceability):** هر تصمیم و اقدام قابل ردیابی است
- **سادگی در Debugging:** یک نقطه واحد برای بررسی

**معایب:**
- **Single Point of Failure:** اگر orchestrator از کار بیفتد، کل سیستم متوقف می‌شود
- **گلوگاه عملکردی (Bottleneck):** orchestrator محدودیت پهنای باند ارتباطی دارد
- **مقیاس‌پذیری محدود:** با افزایش agentها، orchestrator به choke point تبدیل می‌شود
- **انعطاف‌پذیری کم:** agentها نمی‌توانند مستقل تصمیم بگیرند

**موارد استفاده:**
- workflowهای ترتیبی مانند month-end close
- سیستم‌های حساس که نیاز به governance قوی دارند
- سناریوهای با agentهای محدود (کمتر از ۱۰-۱۵ agent)

---

### ۲.۲ توپولوژی غیرمتمرکز (Decentralized / Peer-to-Peer) {#decentralized}

در این مدل، **هیچ orchestrator مرکزی** وجود ندارد. agentها مستقیماً با یکدیگر صحبت می‌کنند، وظایف را مذاکره (negotiate) می‌کنند و به طور مستقل تصمیم می‌گیرند.

```text
┌──────────────────────────────────────────────────────────────┐
│                 توپولوژی غیرمتمرکز (Decentralized)            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│                      ┌──────────┐                             │
│                 ┌───→│ Agent B  │←───┐                        │
│                 │    └──────────┘    │                        │
│                 │         ↑         │                         │
│                 │         │         │                         │
│           ┌─────┴─────┐   │   ┌─────┴─────┐                  │
│           │  Agent A   │←──┼──→│  Agent C   │                 │
│           │ (Negotiate)│   │   │ (Negotiate)│                 │
│           └────────────┘   │   └─────┬─────┘                 │
│                 │          │         │                        │
│                 │    ┌─────┴─────┐   │                        │
│                 └───→│  Agent D  │←──┘                        │
│                      └──────────┘                             │
│                                                               │
│    Message Bus (e.g., Kafka / NATS / Redis Pub/Sub)           │
│    هر agent می‌تواند publish/subscribe کند                    │
└──────────────────────────────────────────────────────────────┘
```

**مزایا:**
- **مقیاس‌پذیری بالا:** با افزایش agentها عملکرد افت نمی‌کند
- **Fault Tolerance:** خرابی یک agent بقیه سیستم را مختل نمی‌کند
- **انعطاف‌پذیری:** agentها می‌توانند به صورت پویا همکاری کنند
- **عدم گلوگاه:** بدون نقطه تمرکز ترافیک

**معایب:**
- **پیچیدگی ارتباطی:** مدیریت state بین agentها سخت است
- **عدم Accountability:** ردیابی اینکه چه کسی چه تصمیمی گرفته پیچیده است
- **مشکل Consistency:** هماهنگی state بین agentها چالش‌برانگیز است
- **Debugging دشوار:** ردیابی علت خطا در شبکه agentها سخت است

**موارد استفاده:**
- سیستم‌های real-time مانند تشخیص ناهنجاری
- سناریوهای مقیاس بزرگ با ده‌ها یا صدها agent
- محیط‌هایی که fault tolerance اولویت اول است

---

### ۲.۳ توپولوژی سلسله‌مراتبی (Hierarchical Orchestration) {#hierarchical}

این مدل **ترکیبی از دو مدل قبل** است. orchestration در چند لایه انجام می‌شود: هر لایه orchestrator مخصوص خود را دارد که زیرمجموعه‌ای از agentها را کنترل می‌کند.

```text
┌──────────────────────────────────────────────────────────────────┐
│                توپولوژی سلسله‌مراتبی (Hierarchical)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│                    ┌─────────────────┐                            │
│                    │  Master         │                            │
│                    │  Orchestrator   │                            │
│                    │  (Supervisor)   │                            │
│                    └────────┬────────┘                            │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ Sub-Orch A  │    │ Sub-Orch B  │    │ Sub-Orch C  │          │
│  │ (Domain A)  │    │ (Domain B)  │    │ (Domain C)  │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                   │                  │
│    ┌────┼────┐        ┌────┼────┐        ┌────┼────┐            │
│    │    │    │        │    │    │        │    │    │            │
│    ▼    ▼    ▼        ▼    ▼    ▼        ▼    ▼    ▼            │
│  ┌──┐ ┌──┐ ┌──┐   ┌──┐ ┌──┐ ┌──┐    ┌──┐ ┌──┐ ┌──┐           │
│  │A1│ │A2│ │A3│   │B1│ │B2│ │B3│    │C1│ │C2│ │C3│           │
│  └──┘ └──┘ └──┘   └──┘ └──┘ └──┘    └──┘ └──┘ └──┘           │
│                                                                   │
│  لایه ۱: Master Orchestrator ← اهداف سطح بالا                    │
│  لایه ۲: Sub-Orchestrator    ← هماهنگی درون domain               │
│  لایه ۳: Worker Agents       ← اجرای وظایف تخصصی                 │
└──────────────────────────────────────────────────────────────────┘
```

**مزایا:**
- **تعادل بین کنترل و انعطاف:** هر لایه autonomy خود را دارد
- **جداسازی دامنه‌ها (Domain Isolation):** هر sub-orchestrator مختص یک حوزه است
- **مقیاس‌پذیری خوب:** هر لایه می‌تواند مستقل مقیاس شود
- **Fault Isolation:** خرابی محدود به یک شاخه می‌ماند

**معایب:**
- **سربار معماری (Architectural Overhead):** لایه‌های بیشتر = پیچیدگی بیشتر
- **تأخیر ارتباطی (Latency):** پیام باید از چند لایه عبور کند
- **پیچیدگی در طراحی:** نیاز به تعریف دقیق interface بین لایه‌ها

**موارد استفاده:**
- سازمان‌های بزرگ با چندین دپارتمان / domain
- HiveOS با معماری Domain Plugin System
- سیستم‌های سازمانی (Enterprise) با governance چندسطحی

---

### مقایسه سه توپولوژی

| ویژگی | Centralized | Decentralized | Hierarchical |
|--------|-------------|---------------|--------------|
| **کنترل (Control)** | بالا | کم | متوسط |
| **مقیاس‌پذیری** | Low | High | High |
| **Fault Tolerance** | Low | High | Medium-High |
| **پیچیدگی** | کم | بالا | متوسط |
| **Traceability** | بالا | کم | بالا |
| **Debugging** | آسان | دشوار | متوسط |
| **Latency** | کم | متغیر | متوسط |
| **مناسب برای** | workflowهای حساس | real-time, مقیاس بزرگ | سازمانی, multi-domain |

---

## ۳. پروتکل‌های ارتباطی {#protocols}

ارتباط در MAS به دو سطح تقسیم می‌شود: ارتباط agent با **ابزار و داده** و ارتباط agent با **سایر agentها**. دو پروتکل استاندارد برای این دو سطح ظهور کرده‌اند.

### ۳.۱ MCP (Model Context Protocol) {#mcp}

**MCP** پروتکلی است که توسط **Anthropic** معرفی شد و نحوه ارتباط agentها با ابزارهای خارجی (tools) و منابع داده (data sources) را استاندارد می‌کند.

```text
┌──────────────────────────────────────────────────────────────┐
│              MCP — Model Context Protocol                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐          MCP           ┌──────────────────┐   │
│  │  Agent   │◄──────────────────────►│  External Tools   │   │
│  │ (Client) │     Resources, Tools,   │  - Database       │   │
│  │          │     Prompts, Sessions   │  - APIs           │   │
│  └──────────┘                        │  - File System    │   │
│       │                              │  - Search Engine  │   │
│       │ MCP Session                   │  - Web Browsers  │   │
│       │ (Stateless or Stateful)       └──────────────────┘   │
│       ▼                                                       │
│  ┌──────────┐                                                 │
│  │Orchestra-│  ← Enforces policy, schema, access control      │
│  │ tion Log │  ← Logs all MCP calls for audit                 │
│  └──────────┘                                                 │
└──────────────────────────────────────────────────────────────┘
```

**ویژگی‌های کلیدی MCP:**

| ویژگی | توضیح |
|--------|-------|
| **Client-Server** | Agent = Client / Tool = Server |
| **Resources** | داده‌های متنی و فایل‌هایی که agent می‌خواند |
| **Tools** | توابع قابل اجرا که agent فراخوانی می‌کند |
| **Prompts** | قالب‌های prompt قابل استفاده مجدد |
| **Session Management** | پشتیبانی از exchanges stateless و stateful |
| **Schema Validation** | enforce فرمت داده‌ها |
| **Access Control** | محدودیت دسترسی بر اساس policy |

> **نقش MCP در Orchestration:** MCP پل عملیاتی بین برنامه‌های سطح بالای orchestration و اجرای سطح پایین ابزارهاست. agent یا orchestrator از MCP برای فراخوانی ابزارهای خارجی با رعایت policy استفاده می‌کند و نتایج به orchestration state بازمی‌گردد.

**مثال فراخوانی MCP در workflow:**

```text
1. Orchestrator: "نیاز به استخراج داده از دیتابیس"
2. Orchestrator → MCP Client: "query: SELECT * FROM invoices WHERE status='pending'"
3. MCP Client → Database Tool: اجرای Query
4. Database Tool → MCP Client: داده‌های دریافتی
5. MCP Client → Orchestrator: داده + metadata + schema validation result
6. Orchestrator: داده را به Agent بعدی ارسال می‌کند
```

---

### ۳.۲ A2A (Agent-to-Agent Protocol) {#a2a}

**A2A** پروتکلی است که توسط **Google** معرفی شد و نحوه ارتباط مستقیم بین agentها را استاندارد می‌کند. این پروتکل امکان **negotiation**, **delegation** و **coordination** بین agentها را فراهم می‌کند.

```text
┌──────────────────────────────────────────────────────────────┐
│           A2A — Agent-to-Agent Protocol                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐              A2A               ┌──────────┐   │
│  │ Agent A  │◄──────────────────────────────►│ Agent B  │   │
│  │ (Worker) │     - Task Delegation          │ (Service)│   │
│  │          │     - Result Sharing           │          │   │
│  └────┬─────┘     - Negotiation              └────┬─────┘   │
│       │           - Status Updates                │         │
│       │                                           │         │
│       │                                           │         │
│  ┌────▼─────┐                          ┌──────────▼─────┐  │
│  │ Agent C  │◄──── A2A ───────────────►│  Orchestrator  │  │
│  │ (Support)│                          │  (Supervisor)  │  │
│  └──────────┘                          └────────────────┘  │
│                                                               │
│  A2A Message Format:                                          │
│  ┌──────────────────────────────────────────────┐            │
│  │ { "type": "task_delegation",                 │            │
│  │   "from": "agent_a",                         │            │
│  │   "to": "agent_b",                           │            │
│  │   "task": "validate_invoice",                │            │
│  │   "payload": { ... },                        │            │
│  │   "trace_id": "tx_abc123" }                  │            │
│  └──────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

**ویژگی‌های کلیدی A2A:**

| ویژگی | توضیح |
|--------|-------|
| **Peer-to-Peer** | ارتباط مستقیم بین agentها (با یا بدون واسطه orchestrator) |
| **Structured Payloads** | پیام‌های استاندارد با metadata |
| **Cryptographic Signing** | تضمین integrity و authenticity پیام‌ها |
| **Role-Based Routing** | مسیریابی بر اساس نقش agent |
| **Task Delegation** | ارسال subtask به agent دیگر |
| **Result Sharing** | به اشتراک‌گذاری نتایج میانی |
| **Traceability** | تمام exchanges قابل ردیابی هستند |

---

### ۳.۳ مقایسه MCP و A2A {#mcp-vs-a2a}

```text
┌─────────────────────────────────────────────────────────────────┐
│              MCP  vs  A2A — نقش‌های مکمل                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   MULTI-AGENT SYSTEM                      │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │          A2A PROTOCOL                          │    │   │
│  │  │     Agent ↔ Agent Communication                │    │   │
│  │  │     "چطور agentها با هم حرف می‌زنند"             │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                     │                                     │
│  │                     ▼                                     │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │          MCP PROTOCOL                          │    │   │
│  │  │     Agent ↔ Tool Communication                 │    │   │
│  │  │     "چطور agentها با ابزارها حرف می‌زنند"        │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                     │                                     │
│  │                     ▼                                     │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │          EXTERNAL WORLD                        │    │   │
│  │  │     Databases · APIs · Files · Web · Search     │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  MCP = چه ابزارهایی در دسترس است و چطور فراخوانی می‌شوند         │
│  A2A = چه agentهایی وجود دارند و چطور همکاری می‌کنند            │
└─────────────────────────────────────────────────────────────────┘
```

| جنبه | MCP | A2A |
|------|-----|-----|
| **هدف** | دسترسی agent به ابزار/داده | ارتباط agent با agent |
| **معمار** | Anthropic | Google |
| **الگو** | Client-Server | Peer-to-Peer |
| **مخاطب** | Agent ↔ Tool | Agent ↔ Agent |
| **امنیت** | Schema validation, Access control | Cryptographic signing, RBAC |
| **State** | Session-based (stateless/stateful) | Message-based |
| **نقش در orchestration** | اجرای دستورات ابزاری | هماهنگی بین agentها |

> این دو پروتکل **رقیب نیستند** — مکمل یکدیگرند. MCP تعیین می‌کند agentها چطور به ابزارها دسترسی داشته باشند و A2A تعیین می‌کند agentها چطور با هم ارتباط برقرار کنند.

---

## ۴. لایه Orchestration در معماری {#orchestration-layer}

بر اساس مقاله arXiv 2601.13671، لایه orchestration از چهار زیرسیستم اصلی تشکیل شده است:

```text
┌───────────────────────────────────────────────────────────────┐
│              لایه Orchestration — معماری کامل                   │
├───────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  A. Planning & Policy Management                         │  │
│  │  ┌──────────────┐  ┌────────────────┐                   │  │
│  │  │ Planning     │  │ Policy Unit    │                    │  │
│  │  │ Unit         │  │ (Governance    │                    │  │
│  │  │ (Goal →      │  │  Constraints)  │                    │  │
│  │  │  Subtasks)   │  └────────────────┘                    │  │
│  │  └──────────────┘                                        │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  B. Execution & Control Management                       │  │
│  │  ┌──────────────┐  ┌────────────────┐                   │  │
│  │  │ Execution    │  │ Control Unit   │                    │  │
│  │  │ Unit         │  │ (Concurrency,  │                    │  │
│  │  │ (Task Run)   │  │  Sync, Recovery)│                   │  │
│  │  └──────────────┘  └────────────────┘                    │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  C. State & Knowledge Management                         │  │
│  │  ┌──────────────┐  ┌────────────────┐                   │  │
│  │  │ State Unit   │  │ Knowledge Unit  │                   │  │
│  │  │ (Checkpoints,│  │ (Context,      │                   │  │
│  │  │  Logs, States)│  │  Domain Info)  │                   │  │
│  │  └──────────────┘  └────────────────┘                    │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  D. Quality & Operations Management                      │  │
│  │  ┌──────────────┐  ┌────────────────┐                   │  │
│  │  │ Validation   │  │ Monitoring     │                    │  │
│  │  │ (Schema,     │  │ (Metrics,      │                    │  │
│  │  │  Compliance)  │  │  Anomaly, Drift)│                   │  │
│  │  └──────────────┘  └────────────────┘                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Protocol Layer (زیرساخت ارتباطی):                              │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │   MCP Client     │  │   A2A Protocol   │                    │
│  │ (Tool Access)    │  │ (Agent Comms)    │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────────────────────────────────────────┘
```

### توضیح زیرسیستم‌ها:

| زیرسیستم | وظیفه اصلی | مثال عملی |
|-----------|-----------|-----------|
| **Planning** | تجزیه اهداف به subtaskهای قابل اجرا | "بستن ماهانه" → تطبیق بانک، ثبت سند، محاسبه مالیات |
| **Policy** | تعریف محدودیت‌های حاکمیتی | "فقط کاربران سطح ۳ می‌توانند سند قطعی ثبت کنند" |
| **Execution** | اجرای smooth وظایف توسط worker agentها | اجرای هم‌زمان ۳ agent تطبیق |
| **Control** | مدیریت concurrency, dependency, recovery | تشخیص agent خراب → ری‌استارت یا جایگزینی |
| **State** | checkpoint, workflow progress, agent state | "Agent A تمام شد، مرحله بعدی شروع شود" |
| **Knowledge** | context و دانش دامنه | قوانین IFRS, استانداردهای حسابداری |
| **Quality** | اعتبارسنجی خروجی‌ها | بررسی تطابق سند حسابداری با اصول پذیرفته شده |
| **Monitoring** | metrics, anomaly detection, drift | "Agent A ۳ بار خطا داده → اعلان به اپراتور" |

---

## ۵. پیاده‌سازی در HiveOS {#hiveos}

HiveOS به عنوان یک **Multi-Agent Operating System** از یک معماری **سلسله‌مراتبی (Hierarchical)** با یک orchestrator مرکزی به نام **Mothership** استفاده می‌کند.

```text
┌─────────────────────────────────────────────────────────────────┐
│                   HIVEOS — معماری Orchestration                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MOTHERSHIP                             │   │
│  │  ┌──────────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │ Flow Engine  │  │ Registry │  │ Knowledge         │   │   │
│  │  │ (DSL Parser  │  │ Manager  │  │ Distributor       │   │   │
│  │  │  + Executor) │  │          │  │ (Skill Sync)      │   │   │
│  │  └──────┬───────┘  └────┬─────┘  └────────┬─────────┘   │   │
│  │         │               │                  │              │   │
│  │  ┌──────▼───────────────▼──────────────────▼──────────┐  │   │
│  │  │           Task Router (مسیریاب هوشمند)              │  │   │
│  │  │  capability-aware · least-loaded · affinity-based   │  │   │
│  │  └───────────────────────┬────────────────────────────┘  │   │
│  │                          │                                │   │
│  │  ┌───────────────────────▼────────────────────────────┐  │   │
│  │  │        Communication Bus (Message Queue)            │  │   │
│  │  │  A2A · Task Assignment · Heartbeat · Sync Events     │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│        ┌───────────────────┼───────────────────┐                │
│        │                   │                   │                │
│        ▼                   ▼                   ▼                │
│  ┌──────────┐       ┌──────────┐        ┌──────────┐          │
│  │ Node A   │       │ Node B   │        │ Node C   │           │
│  │ (Sat.)   │       │ (Sat.)   │        │ (Sat.)   │           │
│  │ Hermes   │       │ Hermes   │        │ Hermes   │           │
│  │ Instance │       │ Instance │        │ Instance │           │
│  └──────────┘       └──────────┘        └──────────┘          │
│       │                  │                   │                  │
│  ┌────┴────┐        ┌────┴────┐        ┌────┴────┐            │
│  │ Domain  │        │ Domain  │        │ Domain  │             │
│  │ Agents  │        │ Agents  │        │ Agents  │             │
│  └─────────┘        └─────────┘        └─────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### ۵.۱ Mothership {#mothership}

**Mothership** قلب orchestration در HiveOS است. یک HTTP Server مرکزی که تمام ارتباطات بین satellite nodeها را مدیریت می‌کند.

**وظایف اصلی:**

| مؤلفه | وظیفه | پیاده‌سازی |
|--------|--------|------------|
| **Flow Engine** | خواندن Flow DSL YAML → ایجاد agentها → زنجیر کردن خروجی‌ها → مدیریت خطا | `mothership/server.py` |
| **Registry Manager** | ردیابی هر node: آدرس, قابلیت‌ها, وضعیت, flowهای اختصاص داده شده | `mothership/agent_registry.py` |
| **Knowledge Distributor** | sync مهارت‌ها, دانش‌نامه‌ها و تنظیمات به satelliteها | از طریق Communication Bus |
| **Task Router** | مسیریابی وظایف به مناسب‌ترین node | `mothership/task_router.py` |
| **Communication Bus** | message queue برای agent↔agent و node↔node | `mothership/communication_bus.py` |

> **نکته معماری:** هر agent در HiveOS یک **Hermes session** است — HiveOS خودش agent framework نمی‌سازد، بلکه لایه orchestration را روی Hermes می‌سازد.

### ۵.۲ Task Router {#task-router}

**Task Router** مغز مسیریابی هوشمند HiveOS است. وقتی یک flow اجرا می‌شود، Task Router تصمیم می‌گیرد کدام satellite agent کدام task را انجام دهد.

**استراتژی‌های مسیریابی:**

```text
RouteStrategy Enum:
├── CAPABILITY_FIRST  → ارسال task به nodeای که دقیقاً capability مورد نیاز را دارد
├── LEAST_LOADED      → ارسال به node با کمترین بار کاری فعلی
├── ROUND_ROBIN       → توزیع یکنواخت بین nodeهای capable
├── AFFINITY          → ارسال به nodeای که سابقه انجام task مشابه را دارد
└── BEST_FIT          → ترکیب capability + load + health
```

**معیارهای مسیریابی:**

1. **Capability Matching:** آیا node مهارت‌ها و دانش لازم برای این task را دارد؟
2. **Current Load:** node چقدر مشغول است؟ (تعداد taskهای فعال)
3. **Health Status:** node سالم است؟ (heartbeat اخیر)
4. **Affinity/Anti-Affinity Rules:** node قبلاً این نوع task را انجام داده؟ (→ performance بهتر)
5. **Geographic/Domain Proximity:** node در چه domain یا منطقه‌ای قرار دارد؟

```text
مثال: مسیریابی یک Task
┌─────────────────────────────────────────────┐
│ Task: "تطبیق صورتحساب بانکی با دفکل"         │
│ Capabilities needed: [reconciliation, erp]   │
├─────────────────────────────────────────────┤
│                                              │
│ Candidate Nodes:                             │
│ ┌─────────┬──────────┬────────┬──────┐      │
│ │ Node    │ Capable  │ Load   │Health│      │
│ ├─────────┼──────────┼────────┼──────┤      │
│ │ Node A  │ ✅       │ 3/10   │ ✅   │      │
│ │ Node B  │ ✅       │ 8/10   │ ✅   │ ← Best Fit
│ │ Node C  │ ❌       │ 1/10   │ ✅   │      │
│ │ Node D  │ ✅       │ 5/10   │ ❌   │      │
│ └─────────┴──────────┴────────┴──────┘      │
│                                              │
│ Result: Node B (capable + least loaded)      │
└─────────────────────────────────────────────┘
```

### ۵.۳ Communication Bus {#comm-bus}

**Communication Bus** ستون فقرات ارتباطی HiveOS است که راه‌های مختلف ارتباطی را پشتیبانی می‌کند:

```text
┌─────────────────────────────────────────────────────────────┐
│              Communication Bus — Message Types                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CONTROL PLANE:                                              │
│  ├── HEARTBEAT         ← nodeها هر N ثانیه سلامت خود را اعلام می‌کنند
│  ├── NODE_REGISTER     ← node جدید به سیستم می‌پیوندد
│  ├── NODE_UNREGISTER   ← node از سیستم خارج می‌شود
│  └── CONTROL_COMMAND   ← دستورات مدیریتی (restart, update, ...)
│                                                              │
│  DATA PLANE:                                                 │
│  ├── TASK_ASSIGNMENT   ← تخصیص task به node
│  ├── TASK_RESULT       ← ارسال نتیجه task
│  ├── A2A_MESSAGE       ← ارتباط مستقیم agent↔agent
│  └── KNOWLEDGE_SYNC    ← به‌روزرسانی دانش و skills
│                                                              │
│  BACKENDS (قابل تعویض):                                      │
│  ├── In-Memory         ← تک‌فرآیندی (توسعه و تست)
│  ├── File-Based        ← چندفرآیندی روی یک ماشین
│  ├── HTTP/REST         ← توزیع شده (آینده)
│  └── NATS/RabbitMQ     ← تولید (آینده — مقیاس بالا)
└─────────────────────────────────────────────────────────────┘
```

### ۵.۴ Agent Registry {#agent-registry}

**Agent Registry** دایرکتوری مرکزی تمام nodeها و agentهای فعال در HiveOS است:

```text
AgentRegistry
├── agent_id: unique identifier
├── address: node address (host:port)
├── capabilities: [list of skills, tools, knowledge domains]
├── status: ONLINE | OFFLINE | BUSY | ERROR
├── current_load: number of active tasks
├── assigned_flows: [active flow IDs]
├── last_heartbeat: timestamp
└── metadata: { version, domain, tags, ... }
```

---

## ۶. الگوهای عملی Orchestration {#patterns}

### ۶.۱ Supervisor Pattern {#supervisor}

یک orchestrator مرکزی (supervisor) agentهای تخصصی را مدیریت می‌کند. پرکاربردترین الگو در HiveOS.

```text
Supervisor Orchestrator
  ├── Step 1: Reconciliation Agent ───→ Result
  ├── Step 2: JE Auto-Post Agent ────→ Result (gated on Step 1)
  ├── Step 3: IC Matching Agent ─────→ Result (gated on Step 2)
  └── Step 4: Consolidation Agent ───→ Final Report
```

**موارد استفاده:**
- Month-end close (بستن ماهانه مالی)
- Tax filing (ارسال اظهارنامه مالیاتی)
- هر workflow ترتیبی با وابستگی‌های مشخص

### ۶.۲ Event-Driven Choreography {#event-driven}

agentها روی رویدادها subscribe می‌کنند و بدون orchestrator مرکزی واکنش نشان می‌دهند.

```text
[Transaction Event] ─→ Event Bus (Kafka/NATS)
  ├── Anomaly Detection Agent (subscribes)
  ├── Compliance Monitor Agent (subscribes)
  └── IC Matching Agent (subscribes)
       └── Detects anomaly → publishes AnomalyEvent
            └── Variance Explainer Agent reacts
                 └── Escalates if needed
```

**موارد استفاده:**
- تشخیص ناهنجاری (Anomaly Detection)
- هشدارهای real-time
- سناریوهای reactive

### ۶.۳ Hybrid Orchestration {#hybrid}

ترکیبی از Supervisor Pattern (برای workflowهای ترتیبی) و Event-Driven Choreography (برای جریان‌های real-time).

```text
HiveOS Hybrid Orchestration:
┌────────────────────────────────────────────────────────────┐
│  Supervisor Orchestrator       Event-Driven Choreography    │
│  ┌─────────────────────┐     ┌────────────────────────┐   │
│  │ Month-End Close     │     │ Anomaly Detection      │   │
│  │ → Sequential steps  │     │ → Event-driven         │   │
│  │ → Gated execution  │     │ → Reactive agents      │   │
│  │ → Human approval   │     │ → Real-time alerts     │   │
│  └─────────────────────┘     └────────────────────────┘   │
│                                                            │
│  Shared: Agent Registry · Communication Bus · Audit Trail  │
└────────────────────────────────────────────────────────────┘
```

### ۶.۴ Pipeline / Sequential Pattern {#pipeline}

agentها به صورت زنجیره‌ای اجرا می‌شوند — خروجی هر agent ورودی agent بعدی است.

```text
Agent A (Raw Data Ingest)
    │
    ▼
Agent B (Junior Accountant — Classify)
    │
    ▼
Agent C (Senior Accountant — Process)
    │
    ▼
Agent D (Financial Controller — Review & Approve)
    │
    ▼
Agent E (Auto-Post to ERP)
```

**ویژگی‌ها:**
- هر مرحله به مرحله قبل وابسته است
- امکان gate و approval در میانه مسیر
- خطا در یک مرحله کل pipeline را متوقف می‌کند

### ۶.۵ Swarm Pattern {#swarm}

چندین agent مشابه به صورت موازی روی یک مسئله کار می‌کنند و نتایج با رأی‌گیری یا میانگین‌گیری ترکیب می‌شود.

```text
┌──────────────────────────────────────────────┐
│                Orchestrator                    │
│  "بررسی این قرارداد از ۳ زاویه مختلف"          │
└────────────┬──────────┬──────────┬───────────┘
             │          │          │
             ▼          ▼          ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │ Agent A  │ │ Agent B  │ │ Agent C  │
     │(Legal)   │ │(Finance) │ │(Risk)    │
     └─────┬────┘ └─────┬────┘ └─────┬────┘
           │            │            │
           └────────────┼────────────┘
                        ▼
              ┌─────────────────┐
              │ Consolidator    │
              │ (Ensemble Vote) │
              └─────────────────┘
```

---

## ۷. فریمورک‌های مطرح Orchestration {#frameworks}

بر اساس تحقیق Galileo.ai و HiveOS:

| فریمورک | توسعه‌دهنده | نقطه قوت | بهترین برای |
|---------|------------|----------|-------------|
| **LangGraph** | LangChain | workflowهای graph-based با state management | فرآیندهای چندمرحله‌ای پیچیده |
| **AutoGen** | Microsoft | قابلیت اطمینان Enterprise + conversational patterns | استقرارهای بزرگ سازمانی |
| **CrewAI** | CrewAI Inc | تیم‌های role-based + نمونه‌سازی سریع | توسعه و آزمایش سریع |
| **OpenAI Agents SDK** | OpenAI | orchestration سبک با handoff | الگوهای ساده هماهنگی |
| **Semantic Kernel** | Microsoft | یکپارچگی Enterprise با .NET/Python | اکوسیستم Microsoft |
| **LlamaIndex Workflows** | LlamaIndex | معماری event-driven برای RAG | برنامه‌های knowledge-intensive |
| **HiveOS Mothership** | HiveOS | معماری سلسله‌مراتبی + DSL + Domain-aware | سیستم‌های domain-native مقیاس‌پذیر |

---

## ۸. نکات کلیدی (Key Takeaways) {#takeaways}

> **📌 خلاصه — آنچه باید درباره MAS Orchestration بدانید:**

| # | نکته کلیدی | توضیح |
|---|------------|-------|
| 1 | **بدون orchestration، chaos حاکم می‌شود** | agentهای مستقل بدون هماهنگی دچار تداخل وظایف و ناسازگاری می‌شوند |
| 2 | **سه توپولوژی اصلی وجود دارد** | Centralized (کنترل کامل), Decentralized (انعطاف بالا), Hierarchical (ترکیب بهترین‌ها) |
| 3 | **MCP و A2A مکمل هستند، نه رقیب** | MCP = agent ↔ tool / A2A = agent ↔ agent — هر دو برای MAS ضروری |
| 4 | **لایه Orchestration ۴ زیرسیستم دارد** | Planning, Execution, State/Knowledge, Quality/Operations |
| 5 | **HiveOS از معماری Hierarchical استفاده می‌کند** | Mothership (مرکزی) + Satellite Nodes (توزیع شده) + Domain Plugin System |
| 6 | **Task Router کلید مقیاس‌پذیری است** | مسیریابی capability-aware + load balancing = استفاده بهینه از منابع |
| 7 | **Hybrid Orchestration بهترین انتخاب عملی است** | Supervisor برای workflowهای ترتیبی + Event-Driven برای جریان‌های real-time |
| 8 | **Governance را فراموش نکنید** | سه سطح: Autonomous / Single Approval / Dual Approval |
| 9 | **Audit Trail ضروری است** | هر agent action باید با trace_id, timestamp, تصمیم‌گیرنده ثبت شود |
| 10 | **انتخاب توپولوژی به نیاز شما بستگی دارد** | مقیاس, accountability, fault tolerance, latency — همه را权衡 کنید |

---

## ۹. منابع {#references}

### مقالات علمی
1. **The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption** — arXiv 2601.13671 (2026)
2. **AIOS: LLM Agent Operating System** — arXiv 2403.16971 (2024)
3. **Agent Operating Systems (Agent-OS): A Blueprint Architecture** — Preprints 202509.0077 (2025)
4. **Multi-Agent Coordination across Diverse Applications: A Survey** — arXiv 2502.14743 (2025)

### پروتکل‌ها
5. **Model Context Protocol (MCP)** — Anthropic — https://modelcontextprotocol.io
6. **Agent-to-Agent (A2A) Protocol** — Google — https://github.com/google/A2A

### فریمورک‌ها
7. **LangGraph** — LangChain — https://www.langchain.com/langgraph
8. **AutoGen** — Microsoft — https://microsoft.github.io/autogen
9. **CrewAI** — https://www.crewai.com
10. **Semantic Kernel** — Microsoft — https://learn.microsoft.com/en-us/semantic-kernel

### HiveOS
11. **HiveOS Architecture** — `docs/02-Architecture/01-high-level-arch.md`
12. **Flow DSL Specification** — `docs/02-Architecture/02-flow-dsl.md`
13. **Domain Plugin System** — `docs/02-Architecture/03-domain-plugin-system.md`
14. **Multi-Agent Accounting Architecture** — `docs/06-Technical/HiveOS-Accounting-Multi-Agent-Architecture-Report.md`
15. **Source Code** — `src/hiveos/mothership/` — Agent Registry, Task Router, Communication Bus

---

> **نویسنده:** Hermes Agent (HiveOS Research)
> **تاریخ:** 2026-07-16
> **وضعیت:** ✅ تکمیل

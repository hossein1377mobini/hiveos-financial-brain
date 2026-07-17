# ارتباط و هماهنگی در سیستم‌های چندعامله (Communication & Coordination in MAS)

> **مسیر:** `docs/06-Research/agents/02-Multi-Agent-Systems/02-communication-and-coordination.md`
> **آخرین به‌روزرسانی:** 2026-07-16
> **منابع:** arXiv 2501.13671, Google A2A Spec, MCP Specification, HiveOS Message Bus

---

## فهرست (Table of Contents)

1. [مقدمه: چرا ارتباط بین Agentها حیاتی است؟](#intro)
2. [پارادایم‌های ارتباطی (Communication Paradigms)](#paradigms)
   - [پیام‌رسانی مستقیم (Direct Messaging)](#direct)
   - [تخته سیاه / حافظه اشتراکی (Blackboard / Shared Memory)](#blackboard)
   - [رویدادمحور (Event-Driven)](#event-driven)
   - [انتشار-اشتراک (Pub/Sub)](#pubsub)
3. [پروتکل‌های ارتباطی (Communication Protocols)](#protocols)
   - [MCP — Model Context Protocol](#mcp)
   - [A2A — Agent-to-Agent](#a2a)
   - [Google A2A — نگاهی عمیق](#google-a2a)
   - [مقایسه MCP و A2A](#mcp-vs-a2a)
4. [الگوهای هماهنگی (Coordination Patterns)](#coordination)
   - [Orchestrator متمرکز (Centralized)](#centralized)
   - [غیرمتمرکز / همتابه‌همتا (Decentralized / P2P)](#decentralized)
   - [سلسله‌مراتبی (Hierarchical)](#hierarchical)
   - [ناظر (Supervisor)](#supervisor)
5. [فرمت‌های پیام (Message Formats)](#formats)
   - [JSON-RPC](#json-rpc)
   - [gRPC / Protocol Buffers](#grpc)
   - [پروتکل‌های سفارشی (Custom Protocols)](#custom)
6. [حل تعارض بین Agentها (Conflict Resolution)](#conflicts)
7. [مدیریت خطا و استراتژی‌های Retry (Error Handling & Retry)](#errors)
8. [جدول مقایسه الگوهای ارتباطی (Comparison Table)](#comparison)
9. [پیاده‌سازی در HiveOS — Communication Bus](#hiveos)
10. [نکات کلیدی (Key Takeaways)](#takeaways)
11. [منابع (References)](#references)

---

## ۱. مقدمه: چرا ارتباط بین Agentها حیاتی است؟ {#intro}

در یک **سیستم چندعامله (Multi-Agent System / MAS)** ، agentها به صورت مجزا (isolated) کار نمی‌کنند. آنها برای دستیابی به اهداف مشترک — چه انجام یک تسک پیچیده، چه حل یک مسئله توزیع‌شده — نیاز به **ارتباط (communication)** و **هماهنگی (coordination)** دارند.

بدون یک لایه ارتباطی کارآمد، MAS با مشکلات زیر مواجه می‌شود:

- **تضاد وظایف (Task Conflict):** دو agent روی یک کار تکراری وقت می‌گذارند چون از هم خبر ندارند
- **ناسازگاری داده (Data Inconsistency):** agentها از نسخه‌های متفاوت یک حقیقت استفاده می‌کنند
- **انحراف از هدف (Goal Drift):** agentها بدون هماهنگی مسیرهای متفاوتی می‌روند
- **اتلاف منابع (Resource Waste):** محاسبات موازی اضافی و بی‌نتیجه

> **تشبیه برای مخاطب ایرانی:** یک MAS بدون ارتباط مؤثر مانند **یک تیم مجازی است که اعضای آن در گروه‌های مختلف واتساپ، تلگرام و بله پیام می‌دهند، هرکس از یک تقویم استفاده می‌کند، و هیچ جلسه هماهنگی هفتگی ندارند.** نتیجه: دوباره‌کاری، ناهماهنگی و اتلاف وقت.

ارتباط در MAS سه وظیفه اصلی دارد:

1. **اشتراک اطلاعات (Information Sharing):** agentها دانش، داده و context را مبادله می‌کنند
2. **هماهنگی وظایف (Task Coordination):** agentها توالی و وابستگی کارها را مدیریت می‌کنند
3. **مذاکره و توافق (Negotiation & Agreement):** agentها در مورد تقسیم کار و حل تعارض به توافق می‌رسند

```text
┌─────────────────────────────────────────────────────────────────┐
│                    لایه‌های ارتباطی در MAS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Application Layer (منطق کسب‌وکار agentها)               │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Message Layer (فرمت پیام: JSON-RPC, gRPC, custom)      │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Protocol Layer (پروتکل: MCP, A2A, HTTP, WebSocket)     │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Transport Layer (حمل: TCP, QUIC, Unix Socket, Shared)  │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Physical / Network Layer (شبکه: LAN, Internet, IPC)    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ✦ هر لایه وظیفه مشخصی دارد و می‌تواند مستقل تغییر کند          │
│  ✦ HiveOS از In-Memory و File backend تا HTTP و NATS را پشتیبانی│
│    می‌کند (لایه Transport قابل تعویض)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## ۲. پارادایم‌های ارتباطی (Communication Paradigms) {#paradigms}

چهار پارادایم اصلی برای ارتباط بین agentها وجود دارد. انتخاب پارادایم مناسب به معماری سیستم، مقیاس، نیاز به real-time بودن و تحمل خطا بستگی دارد.

### ۲.۱ پیام‌رسانی مستقیم (Direct Messaging) {#direct}

ساده‌ترین شکل ارتباط: agentها مستقیماً برای یکدیگر پیام می‌فرستند. هر agent آدرس یا شناسه agent مقصد را می‌داند و از طریق یک کانال نقطه‌به‌نقطه (point-to-point) با آن ارتباط برقرار می‌کند.

```text
┌──────────────────────────────────────────────────────┐
│               Direct Messaging                        │
│                                                        │
│  ┌──────────┐      ┌──────────┐                       │
│  │ Agent A  │──────→│ Agent B  │  "لطفاً این تسک را    │
│  │ (Sender) │←──────│ (Receiver)│   انجام بده"         │
│  └──────────┘      └──────────┘  "نتیجه این است"      │
│       │                                                   │
│       │    ┌──────────┐                                   │
│       └───→│ Agent C  │  پیام مستقیم دیگر                │
│            └──────────┘                                   │
└──────────────────────────────────────────────────────┘
```

**مزایا:**
- سادگی و سرعت بالا (بدون واسط)
- تأخیر کم (low latency)
- مناسب برای ارتباطات دوتایی (dyadic)

**معایب:**
- مقیاس‌پذیری ضعیف (با n agent، O(n²) کانال نیاز است)
- agentها باید از existence و آدرس یکدیگر مطلع باشند (tight coupling)
- عدم persistency — اگر agent مقصد در دسترس نباشد، پیام گم می‌شود

**مثال در HiveOS:**
```python
# HiveOS Communication Bus — پیام مستقیم از طریق correlation_id
bus.publish(
    msg_type=MessageType.AGENT_MESSAGE,
    payload={"content": "لطفاً داده‌های فروش را تحلیل کن"},
    recipient="analytics-agent-01",  # مستقیم به یک agent خاص
    correlation_id="req-001",
)
```

### ۲.۲ تخته سیاه / حافظه اشتراکی (Blackboard / Shared Memory) {#blackboard}

در این پارادایم، agentها به طور مستقیم با هم حرف نمی‌زنند. در عوض، یک **فضای حافظه اشتراکی (shared memory space)** وجود دارد که همه agentها می‌توانند روی آن **بنویسند (write)** و **بخوانند (read)** . این فضا که «تخته سیاه» (blackboard) نام دارد، نقش حافظه میانی (intermediary) را بازی می‌کند.

```text
┌──────────────────────────────────────────────────────────┐
│              Blackboard / Shared Memory                   │
│                                                            │
│  ┌──────────┐                                             │
│  │ Agent A  │─── writes result ──→  ┌─────────────────┐  │
│  └──────────┘                       │   BLACKBOARD     │  │
│                                     │  (منطقه مشترک)   │  │
│  ┌──────────┐                       │                  │  │
│  │ Agent B  │─── writes query ──→  │  • task_queue    │  │
│  └──────────┘                       │  • results_store │  │
│                                     │  • shared_knowl. │  │
│  ┌──────────┐                       │  • locks/semaph. │  │
│  │ Agent C  │←── reads result ─────│                  │  │
│  └──────────┘                       └─────────────────┘  │
│                                                            │
│  ✦ agentها همدیگر را نمی‌شناسند — فقط blackboard را    │
│  ✦ مناسب برای همکاری ناهمگام (asynchronous collaboration)│
└──────────────────────────────────────────────────────────┘
```

**مزایا:**
- **Loose Coupling:** agentها از existence هم بی‌خبرند
- **Persistent:** داده حتی اگر sender آفلاین شود باقی می‌ماند
- **مناسب برای agentهای ناهمگون (heterogeneous):** هر agent به زبان خود می‌نویسد و می‌خواند

**معایب:**
- **گلوگاه (Bottleneck):** blackboard می‌تواند choke point شود
- **مسائل همزمانی (Concurrency):** نیاز به lock و synchronization
- **شکست تکی (Single Point of Failure):** اگر blackboard از کار بیفتد، همه agentها قطع می‌شوند

### ۲.۳ رویدادمحور (Event-Driven Communication) {#event-driven}

در مدل **رویدادمحور (event-driven)** ، agentها به جای ارسال مستقیم پیام به یکدیگر، **رویدادها (events)** را منتشر می‌کنند. هر agent می‌تواند به رویدادهای خاصی **واکنش نشان دهد (react)** . این مدل به طور طبیعی ناهمگام (asynchronous) است.

```text
┌──────────────────────────────────────────────────────────┐
│              Event-Driven Communication                   │
│                                                            │
│  ┌──────────┐                                            │
│  │ Agent A  │─── رویداد: "task.completed" ───→  ┌─────┐ │
│  └──────────┘                                    │Event│ │
│                                                  │Bus  │ │
│  ┌──────────┐                                    └──┬──┘ │
│  │ Agent B  │←── واکنش: دریافت رویداد و شروع ────────┘    │
│  └──────────┘     تسک بعدی                                 │
│                                                            │
│  ┌──────────┐                                    ┌──────┐ │
│  │ Agent C  │←── واکنش: ذخیره رویداد در تاریخچه──│Event  │ │
│  └──────────┘                                    │Log   │ │
│                                                  └──────┘ │
│  ✦ رویدادها immutable و timestamp دار هستند               │
│  ✦ هر agent مستقل تصمیم می‌گیرد به چه رویدادی واکنش نشان  │
│    دهد (reactive architecture)                            │
└──────────────────────────────────────────────────────────┘
```

**مزایا:**
- **جداسازی قوی (Strong Decoupling):** تولیدکننده و مصرف‌کننده رویداد هم را نمی‌شناسند
- **مقیاس‌پذیری عالی:** می‌توان صدها consumer به یک رویداد اضافه کرد
- **تاریخچه کامل (Audit Trail):** همه رویدادها قابل ذخیره و بازپخش هستند

**معایب:**
- **اشکال‌زدایی دشوار (Hard Debugging):** ردیابی جریان رویدادها در سامانه پیچیده است
- **عدم تضمین ترتیب (Ordering):** ترتیب پردازش رویدادها تضمین‌شده نیست
- **پیچیدگی معماری:** نیاز به event store، event schema registry

### ۲.۴ انتشار-اشتراک (Publish / Subscribe — Pub/Sub) {#pubsub}

**Pub/Sub** تکامل‌یافته مدل event-driven است. در اینجا **کانال‌های موضوعی (topic channels)** وجود دارند. agentها می‌توانند در یک تاپیک خاص **مشترک شوند (subscribe)** یا در آن **منتشر کنند (publish)** . بروکر مرکزی (broker) مسئول تحویل پیام‌ها به مشترکان مناسب است.

```text
┌──────────────────────────────────────────────────────────────┐
│                Publish / Subscribe (Pub/Sub)                  │
│                                                               │
│                 ┌──────────────────┐                          │
│                 │    PUB/SUB       │                          │
│                 │    BROKER        │                          │
│                 │  (RabbitMQ,      │                          │
│                 │   NATS, Redis)   │                          │
│                 └──┬────┬────┬────┘                          │
│                    │    │    │                                │
│         ┌──────────┘    │    └──────────┐                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐   ┌──────────┐    ┌──────────┐                │
│  │ Agent A  │   │ Agent B  │    │ Agent C  │                │
│  │(Publisher│   │(Sub to   │    │(Pub+Sub) │                │
│  │ topic:   │   │ topic:   │    │ topic:   │                │
│  │ "tasks") │   │ "tasks") │    │"results")│                │
│  └──────────┘   └──────────┘    └──────────┘                │
│                                                               │
│  ✦ Publisherها از Subscriberها بی‌خبرند و برعکس             │
│  ✦ تاپیک‌ها قابل سازماندهی سلسله‌مراتبی: "tasks.financial" │
│  ✦ HiveOS از این مدل با MessageType برای مسیریابی استفاده   │
│    می‌کند                                                    │
└──────────────────────────────────────────────────────────────┘
```

**مزایا:**
- **مقیاس‌پذیری عالی (Excellent Scalability):** مناسب برای سیستم‌های بزرگ
- **Loose Coupling کامل:** Publisher و Subscriber همدیگر را نمی‌شناسند
- **انعطاف‌پذیری در افزودن agentهای جدید:** کافی است subscriber جدید به تاپیک اضافه شود

**معایب:**
- **تأخیر اضافی (Broker Overhead):** broker یک hop اضافی ایجاد می‌کند
- **پیچیدگی عملیاتی:** broker باید مدیریت، مانیتور و مقیاس شود
- **تضمین تحویل (Delivery Guarantees):** بسته به پیاده‌سازی، at-most-once یا at-least-once

**مثال در HiveOS — Communication Bus:**
```python
# HiveOS از Pub/Sub با MessageType به عنوان topic استفاده می‌کند
# اشتراک در انواع پیام‌های تسک
bus.subscribe(
    message_types=[MessageType.TASK_ASSIGN, MessageType.TASK_START],
    callback=handle_task_event,
    filter_fn=lambda m: m.recipient == "worker-node-01",
)
```

---

## ۳. پروتکل‌های ارتباطی (Communication Protocols) {#protocols}

پروتکل‌های ارتباطی **زبانی (language)** را تعریف می‌کنند که agentها با آن صحبت می‌کنند. دو پروتکل اصلی که در صنعت MAS معروف شده‌اند، **MCP** (توسط Anthropic) و **A2A** (توسط Google) هستند.

### ۳.۱ MCP — Model Context Protocol {#mcp}

| ویژگی | توضیح |
|--------|-------|
| **توسعه‌دهنده** | Anthropic (open standard) |
| **هدف اصلی** | اتصال مدل‌های زبانی (LLM) به **ابزارها و داده‌های خارجی (tools & data sources)** |
| **معماری** | Client-Server (مدل → MCP Client → MCP Server → منبع داده) |
| **پروتکل پایه** | JSON-RPC 2.0 روی HTTP/SSE یا stdio |
| **مورد استفاده در MAS** | یک agent می‌تواند از طریق MCP به ابزارهای تخصصی یا دانش خارجی دسترسی پیدا کند |

MCP در اصل برای **تک agent** طراحی شده — یک LLM که نیاز به دسترسی به ابزارهای خارجی دارد. اما در معماری MAS، MCP به عنوان **پروتکل لایه ابزار (tool layer protocol)** استفاده می‌شود: agentها از MCP برای دسترسی به پایگاه دانش، APIها، و منابع داده استفاده می‌کنند.

```text
┌─────────────────────────────────────────────────────┐
│           MCP در معماری MAS (HiveOS)                │
│                                                       │
│  ┌──────────┐     MCP Client     ┌────────────┐     │
│  │ Agent A  │───────────────────→│ MCP Server  │     │
│  │(LLM-based)│←────────────────────│ (Database)  │     │
│  └──────────┘    Tools/Resources  └────────────┘     │
│                                                       │
│  ┌──────────┐     MCP Client     ┌────────────┐     │
│  │ Agent B  │───────────────────→│ MCP Server  │     │
│  │(LLM-based)│←────────────────────│ (File Sys)  │     │
│  └──────────┘    Tools/Resources  └────────────┘     │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │ Mothership (Orchestrator) از طریق            │    │
│  │ Communication Bus به agentها متصل است         │    │
│  │ MCP برای دسترسی به منابع خارجی استفاده می‌شود│    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**سه مفهوم اصلی MCP:**
1. **Tools (ابزارها):** توابع قابل فراخوانی توسط مدل — مثل `search_database(query)`
2. **Resources (منابع):** داده‌های خواندنی — مثل `file:///reports/sales-2024.csv`
3. **Prompts (پرامپت‌ها):** قالب‌های از پیش تعریف‌شده برای تعامل

### ۳.۲ A2A — Agent-to-Agent Protocol {#a2a}

| ویژگی | توضیح |
|--------|-------|
| **توسعه‌دهنده** | جامعه منبع‌باز (open community standard) |
| **هدف اصلی** | ارتباط مستقیم **بین agentها (agent-to-agent)** |
| **معماری** | Peer-to-Peer (هر agent سرور و کلاینت خودش است) |
| **پروتکل پایه** | HTTP/JSON با WebSocket برای real-time |
| **مورد استفاده در MAS** | agentها مستقیماً با هم مذاکره می‌کنند، task ارسال می‌کنند و نتیجه می‌گیرند |

A2A مخصوص **خود سیستم‌های چندعاملی** طراحی شده است. در A2A، هر agent یک **کارت قابلیت (capability card)** منتشر می‌کند که مشخص می‌کند چه کارهایی می‌تواند انجام دهد. agentها با دیدن کارت‌های یکدیگر تصمیم می‌گیرند که با چه کسی همکاری کنند.

```text
┌────────────────────────────────────────────────────┐
│              A2A Agent-to-Agent                    │
│                                                      │
│  ┌──────────────┐          ┌──────────────┐        │
│  │  Agent A     │          │  Agent B     │        │
│  │              │          │              │        │
│  │ Capabilities:│          │ Capabilities:│        │
│  │ • text-sum   │←────────→│ • code-gen   │        │
│  │ • translate  │  A2A     │ • debug      │        │
│  │ • research   │  Peer    │ • review     │        │
│  └──────────────┘          └──────────────┘        │
│                                                      │
│  ┌─────────────────────────────────────────┐       │
│  │ A2A Message Format:                     │       │
│  │ {                                       │       │
│  │   "from": "agent-a",                    │       │
│  │   "to": "agent-b",                      │       │
│  │   "task_id": "t-001",                   │       │
│  │   "action": "request_collaboration",    │       │
│  │   "payload": { ... },                   │       │
│  │   "protocol": "a2a",                    │       │
│  │   "version": "1.0"                      │       │
│  │ }                                       │       │
│  └─────────────────────────────────────────┘       │
└────────────────────────────────────────────────────┘
```

### ۳.۳ Google A2A — نگاهی عمیق (Deep Dive) {#google-a2a}

پروتکل **Google Agent-to-Agent (A2A)** که در آوریل 2025 توسط Google منتشر شد، یک استاندارد منبع‌باز برای ارتباط مستقیم بین agentهای مستقل است. این پروتکل به طور خاص برای **سناریوهای سازمانی (enterprise scenarios)** با agentهای ناهمگون (توسعه‌یافته توسط تیم‌های مختلف) طراحی شده است.

**مفاهیم کلیدی Google A2A:**

| مفهوم | توضیح به فارسی | توضیح انگلیسی |
|-------|----------------|---------------|
| **Agent Card** | کارت قابلیت — یک سند JSON که مشخص می‌کند agent چه کارهایی می‌تواند انجام دهد، چه فرمت‌هایی پشتیبانی می‌کند، و چه endpointهایی دارد | Machine-readable capability descriptor |
| **Skill** | مهارت — یک قابلیت مشخص مانند "تحلیل صورت‌های مالی" یا "تولید کد SQL" | A discrete capability exposed by an agent |
| **Task** | وظیفه — یک درخواست کامل که از ارسال تا تکمیل را شامل می‌شود | A complete unit of work between agents |
| **Message** | پیام — یک تکه از مکالمه در context یک Task | A single turn within a conversation |
| **Artifact** | مصنوع — خروجی ملموس مانند فایل، تصویر، JSON | Tangible output (files, data, media) |
| **Push Notification** | اعلان لحظه‌ای — برای اطلاع از پیشرفت Task بدون polling | Real-time notification of task status |

**جریان کاری (Workflow) در Google A2A:**

```text
┌─────────────────────────────────────────────────────────────┐
│               Google A2A — جریان ارتباط                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Agent A (مشتری)                    Agent B (سرور)           │
│  ──────────────────                  ────────────────        │
│       │                                    │                  │
│       │  ۱. دریافت Agent Card (capabilities)│                 │
│       │←─────────────────────────────────────│                │
│       │                                    │                  │
│       │  ۲. ارسال Task با جزئیات            │                 │
│       │─────────────────────────────────────→│                │
│       │                                    │                  │
│       │  ۳. دریافت Task ID + وضعیت "pending"│                 │
│       │←─────────────────────────────────────│                │
│       │                                    │                  │
│       │  ۴. [اختیاری] Push Notification    │                 │
│       │      — پیشرفت تسک                   │                 │
│       │←─────────────────────────────────────│                │
│       │                                    │                  │
│       │  ۵. درخواست نتیجه (GET) یا دریافت   │                │
│       │     خودکار (push)                   │                │
│       │←─────────────────────────────────────│                │
│       │                                    │                  │
│       │  ۶. دریافت Artifact + وضعیت         │                 │
│       │     "completed" / "failed"          │                │
│       │←─────────────────────────────────────│                │
│       │                                    │                  │
└─────────────────────────────────────────────────────────────┘
```

**Agent Card — مثال:**
```json
{
  "name": "financial-analyst-agent",
  "description": "تحلیل صورت‌های مالی و تولید گزارش",
  "url": "https://agents.hiveos.io/financial",
  "capabilities": {
    "skills": [
      {
        "id": "analyze-balance-sheet",
        "name": "تحلیل ترازنامه",
        "input_types": ["application/json", "text/csv"],
        "output_types": ["application/json", "text/markdown"]
      },
      {
        "id": "calculate-ratios",
        "name": "محاسبه نسبت‌های مالی",
        "input_types": ["application/json"],
        "output_types": ["application/json"]
      }
    ]
  },
  "security": {
    "authentication": "oauth2",
    "required_audience": "https://agents.hiveos.io"
  }
}
```

### ۳.۴ مقایسه MCP و A2A {#mcp-vs-a2a}

| جنبه | MCP (Model Context Protocol) | A2A (Agent-to-Agent) |
|------|------------------------------|----------------------|
| **هدف (Purpose)** | اتصال LLM به ابزار/داده | ارتباط بین agentها |
| **معماری** | Client-Server | Peer-to-Peer |
| **جهت ارتباط** | یک‌طرفه (مدل → ابزار) | دوطرفه (agent → agent) |
| **کاربرد در MAS** | دسترسی به ابزارهای تخصصی | همکاری و مذاکره بین agentها |
| **نقش در HiveOS** | agentها از MCP برای دسترسی به domain tools استفاده می‌کنند | Mothership از A2A-like patterns برای هماهنگی استفاده می‌کند |
| **فرمت پیام** | JSON-RPC 2.0 | JSON over HTTP/WebSocket |
| **وضعیت** | استاندارد در حال رشد (Anthropic) | پیش‌نویس (Google, 2025) |

> **نکته مهم:** MCP و A2A **رقابتی نیستند** — مکمل هم هستند. یک agent می‌تواند از MCP برای دسترسی به ابزارها و از A2A برای ارتباط با agentهای دیگر استفاده کند.

---

## ۴. الگوهای هماهنگی (Coordination Patterns) {#coordination}

در این بخش چهار الگوی اصلی هماهنگی در MAS را بررسی می‌کنیم.

### ۴.۱ Orchestrator متمرکز (Centralized Orchestration) {#centralized}

یک **Orchestrator مرکزی (Central Orchestrator)** تصمیم می‌گیرد کدام agent چه کاری انجام دهد، به چه ترتیبی، و با چه ورودی‌هایی. همه ارتباطات از طریق orchestrator عبور می‌کند.

```text
┌──────────────────────────────────────────────────────────┐
│             Centralized Orchestration                     │
│                                                            │
│                      ┌──────────────┐                     │
│                      │ ORCHESTRATOR │                     │
│                      │  (Mothership)│                     │
│                      └──────┬───────┘                     │
│                             │                              │
│             ┌───────────────┼───────────────┐              │
│             │               │               │              │
│             ▼               ▼               ▼              │
│      ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│      │  Agent   │    │  Agent   │    │  Agent   │         │
│      │Research  │    │  Write   │    │  Review  │         │
│      └──────────┘    └──────────┘    └──────────┘         │
│         │               │               │                  │
│         └───────────────┼───────────────┘                  │
│                         ▼                                  │
│                  ┌──────────────┐                          │
│                  │  Results     │                          │
│                  │  Aggregator  │                          │
│                  └──────────────┘                          │
│                                                            │
│  ✦ HiveOS Mothership در این نقش عمل می‌کند                 │
│  ✦ تمام تسک‌ها از طریق Communication Bus مدیریت می‌شوند   │
└──────────────────────────────────────────────────────────┘
```

**مزایا:**
- کنترل و دید کامل (full visibility)
- governance قوی (هر تصمیم قابل ردیابی است)
- سادگی در پیاده‌سازی

**معایب:**
- Single Point of Failure
- bottleneck در مقیاس بالا
- انعطاف‌پذیری کم

### ۴.۲ غیرمتمرکز / همتابه‌همتا (Decentralized / Peer-to-Peer) {#decentralized}

هیچ نقطه مرکزی وجود ندارد. agentها مستقیماً با هم صحبت می‌کنند، وظایف را مذاکره می‌کنند و به consensus می‌رسند.

```text
┌──────────────────────────────────────────────────────────┐
│              Decentralized / Peer-to-Peer                 │
│                                                            │
│                 ┌──────────┐                              │
│            ┌───→│ Agent B  │←───┐                         │
│            │    └──────────┘    │                         │
│            │         ↑         │                          │
│            │         │         │                          │
│      ┌─────┴─────┐   │   ┌─────┴─────┐                   │
│      │ Agent A   │←──┼──→│ Agent C   │                   │
│      │(Orchestrate│   │   │(Compute)  │                   │
│      │ the flow)  │   │   └───────────┘                   │
│      └────────────┘   │                                   │
│            │          │                                   │
│            │    ┌─────┴─────┐                             │
│            └───→│ Agent D   │                             │
│                 │(Validate) │                             │
│                 └───────────┘                             │
│                                                            │
│  ✦ هر agent تصمیم می‌گیرد با کی و چگونه همکاری کند        │
│  ✦ با Communication Bus، همه agentها به bus وصلند         │
└──────────────────────────────────────────────────────────┘
```

### ۴.۳ سلسله‌مراتبی (Hierarchical Coordination) {#hierarchical}

ترکیبی از centralized و decentralized — orchestration در چند لایه انجام می‌شود. هر لایه یک orchestrator دارد که زیرمجموعه‌ای را کنترل می‌کند.

```text
┌──────────────────────────────────────────────────────────────┐
│                Hierarchical Coordination                      │
│                                                                │
│                    ┌─────────────────┐                        │
│                    │  Master         │                        │
│                    │  Orchestrator   │                        │
│                    │  (Mothership)   │                        │
│                    └────────┬────────┘                        │
│                             │                                 │
│         ┌───────────────────┼───────────────────┐             │
│         │                   │                   │             │
│         ▼                   ▼                   ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │Sub-Orch A   │    │Sub-Orch B   │    │Sub-Orch C   │       │
│  │(Research    │    │(Coding      │    │(Validation)  │       │
│  │ Domain)     │    │ Domain)     │    │             │       │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│         │                  │                   │               │
│    ┌────┼────┐       ┌────┼────┐        ┌────┼────┐         │
│    │    │    │       │    │    │        │    │    │         │
│    ▼    ▼    ▼       ▼    ▼    ▼        ▼    ▼    ▼         │
│  A1   A2   A3      B1   B2   B3       C1   C2   C3          │
│  (متخصصین تحقیق)    (متخصصین کدنویسی)    (متخصصین تست)        │
└──────────────────────────────────────────────────────────────┘
```

### ۴.۴ الگوی ناظر (Supervisor Pattern) {#supervisor}

در این الگو که در HiveOS هم استفاده شده، یک **Supervisor Agent** کار agentهای زیردست را نظارت می‌کند. supervisor تسک‌ها را توزیع می‌کند، پیشرفت را مانیتور می‌کند، و در صورت خطا مداخله می‌کند.

```text
┌────────────────────────────────────────────────────────────┐
│                   Supervisor Pattern                        │
│                                                              │
│  ┌──────────────┐                                           │
│  │  Supervisor  │── ۱. تقسیم تسک اصلی به زیرتسک ───────┐   │
│  │   Agent      │                                       │   │
│  │  (Mothership)│  ۲. تخصیص زیرتسک به workerها          │   │
│  └──────┬───────┘                                       │   │
│         │           ۳. نظارت بر پیشرفت و کیفیت           │   │
│         │           ۴. جمع‌آوری نتایج                   │   │
│         │           ۵. مدیریت خطا و retry               │   │
│         │                                               │   │
│  ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐   │   │
│  │ Worker A   │   │ Worker B   │   │ Worker C   │   │   │
│  │ (تحقیق)    │   │ (نوشتن)    │   │ (بازبینی)  │   │   │
│  └────────────┘   └────────────┘   └────────────┘   │   │
│                                                      │   │
│  ✦ Supervisor نتیجه هر worker را بررسی می‌کند       │   │
│  ✦ اگر worker B خراب شد، supervisor تسک را به D می‌دهد│   │
└──────────────────────────────────────────────────────────┘
```

**مثال Supervisor در HiveOS:**
```python
# HiveOS Resilience Engine — Supervisor Logic
# از resilience.py در Mothership
class Supervisor:
    def __init__(self, bus: CommunicationBus, registry: AgentRegistry):
        self.bus = bus
        self.registry = registry

    def assign_with_supervision(self, task: Task):
        """تخصیص تسک با نظارت — supervisor شکست را مدیریت می‌کند"""
        worker = self.registry.find_capable_worker(task.capability)
        if not worker:
            return self.escalate_to_human(task)

        # ارسال تسک و تنظیم watchdog
        msg = self.bus.assign_task(worker.node_id, task.id, ...)
        success = self._wait_with_timeout(task.id, timeout=30)

        if not success:
            # Fallback: agent خراب — تسک را به worker دیگر بده
            self.registry.mark_degraded(worker.node_id)
            return self.assign_with_supervision(task)  # Retry
```

---

## ۵. فرمت‌های پیام (Message Formats) {#formats}

فرمت پیام تعیین می‌کند که داده چگونه **ساختار (structure)** و **کدگذاری (encode)** شود.

### ۵.۱ JSON-RPC {#json-rpc}

یک پروتکل **سبک (lightweight)** و **متن‌باز (text-based)** برای فراخوانی از راه دور (remote procedure call). در MAS، JSON-RPC رایج‌ترین فرمت برای MCP و بسیاری از معماری‌های agent است.

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "agent.capabilities.list",
  "params": {
    "agent_id": "analytics-agent-01"
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "capabilities": [
      "data_analysis",
      "chart_generation",
      "report_summarization"
    ],
    "status": "available",
    "load": 0.35
  }
}
```

**مزایا:** ساده، خوانا برای انسان، پشتیبانی گسترده  
**معایب:** حجیم (verbose)، بدون تایپ قوی (no type safety)، slow برای حجم بالا

### ۵.۲ gRPC / Protocol Buffers {#grpc}

یک فریمورک **کارآمد (efficient)** و **دودویی (binary)** برای RPC که توسط Google توسعه یافته. از **Protocol Buffers (protobuf)** برای serialization استفاده می‌کند.

```protobuf
syntax = "proto3";

package hiveos.mas;

message AgentMessage {
  string message_id = 1;
  string sender = 2;
  string recipient = 3;
  MessageType type = 4;
  bytes payload = 5;         // Any structured data
  int32 priority = 6;
  int64 timestamp = 7;       // Unix epoch ms
  int32 ttl_seconds = 8;
  int32 retry_count = 9;
}

enum MessageType {
  HEARTBEAT = 0;
  TASK_ASSIGN = 1;
  TASK_RESULT = 2;
  AGENT_MESSAGE = 3;
}

service CommunicationBus {
  rpc SendMessage(AgentMessage) returns (Ack);
  rpc StreamMessages(Subscription) returns (stream AgentMessage);
}
```

**مزایا:** بسیار سریع، تایپ ایمن (type safe)، پشتیبانی از streaming، فشرده  
**معایب:** پیچیده‌تر، نیاز به code generation، اشکال‌زدایی دشوارتر (binary)

### ۵.۳ پروتکل‌های سفارشی (Custom Protocols) {#custom}

بسیاری از سیستم‌های MAS از **پروتکل‌های مختص خود (domain-specific protocols)** استفاده می‌کنند. HiveOS یک مثال خوب است — از **Message dataclass** با فیلدهای سفارشی به جای JSON-RPC خام استفاده می‌کند.

```python
# HiveOS Message — یک پروتکل سفارشی اما استاندارد
@dataclass
class Message:
    type: MessageType          # نوع پیام (Enum)
    sender: str                # فرستنده
    recipient: Optional[str]   # گیرنده (None = broadcast)
    payload: Dict[str, Any]    # بدنه اصلی
    message_id: str            # شناسه یکتا
    correlation_id: Optional[str]  # برای request-response
    priority: MessagePriority  # اولویت (LOW, NORMAL, HIGH, CRITICAL)
    ttl: int                   # زمان انقضا (ثانیه)
    retry_count: int           # تعداد تلاش مجدد
    headers: Dict[str, str]    # metadata اضافی
```

**جدول مقایسه فرمت‌های پیام:**

| ویژگی | JSON-RPC | gRPC/Protobuf | Custom (HiveOS Message) |
|-------|----------|---------------|------------------------|
| **سرعت (Speed)** | متوسط | ⚡ بسیار سریع | سریع (in-memory dict) |
| **حجم پیام** | بزرگ (text) | کوچک (binary) | متوسط |
| **Type Safety** | ❌ خیر | ✅ بله | ✅ با Dataclass |
| **Human Readable** | ✅ بله | ❌ خیر | ✅ بله |
| **Streaming** | ❌ (محدود) | ✅ بله | ✅ (از طریق callback) |
| **پیچیدگی** | کم | متوسط | کم |
| **مناسب برای** | ابزارهای خارجی | ارتباطات پرسرعت داخلی | bus درونی سیستم |

---

## ۶. حل تعارض بین Agentها (Conflict Resolution) {#conflicts}

در MAS، تعارض (conflict) اجتناب‌ناپذیر است. **تعارض** زمانی رخ می‌دهد که دو یا چند agent:
- به یک **منبع مشترک (shared resource)** نیاز دارند
- **اهداف متناقض (conflicting goals)** دارند
- **نظرات متفاوت (divergent opinions)** در مورد یک مسئله دارند

### ۶.۱ انواع تعارض (Types of Conflict)

| نوع تعارض | توضیح | مثال |
|-----------|-------|------|
| **منبع (Resource)** | دو agent به یک منبع محدود (GPU, API, lock) نیاز دارند | دو agent می‌خواهند همزمان از یک مدل LLM استفاده کنند |
| **هدف (Goal)** | اهداف agentها با هم ناسازگار است | agent فروش می‌خواهد تخفیف بدهد، agent مالی می‌خواهد حاشیه سود حفظ شود |
| **دانش (Knowledge)** | agentها از حقایق متفاوتی استفاده می‌کنند | agent A می‌گوید مشتری VIP است، agent B می‌گوید معمولی است |
| **تسک (Task)** | دو agent روی یک تسک تکراری کار می‌کنند | دو agent همزمان صورت مالی را تحلیل می‌کنند |

### ۶.۲ استراتژی‌های حل تعارض (Resolution Strategies)

| استراتژی | توضیح | مناسب برای |
|----------|-------|-----------|
| **Locking (قفل)** | منبع اشتراکی قفل می‌شود — فقط یک agent در لحظه دسترسی دارد | تعارض منبع |
| **Priority-Based** | agent با اولویت بالاتر برنده می‌شود | تعارض تسک |
| **Voting / Consensus** | agentها رأی می‌دهند و اکثریت تصمیم می‌گیرد | تعارض نظر/دانش |
| **Arbitration** | یک agent داور (arbiter) تصمیم نهایی را می‌گیرد | تعارض هدف |
| **Negotiation** | agentها با مذاکره به توافق می‌رسند | تعارض منبع/هدف |
| **Escalation** | تعارض به سطح بالاتر (انسان) ارجاع می‌شود | تعارض حل‌نشدنی |

**مثال Arbitration در HiveOS:**
```python
# HiveOS Task Router — حل تعارض با اولویت
class TaskRouter:
    def resolve_conflict(self, task_id: str, claimants: List[str]):
        """
        دو agent هر دو می‌گویند "من این تسک را انجام می‌دهم".
        router بر اساس capability score و current load تصمیم می‌گیرد.
        """
        best_agent = max(
            claimants,
            key=lambda aid: (
                self.registry.get_capability_score(aid, task_id),
                -self.registry.get_current_load(aid)  # بار کمتر = بهتر
            )
        )
        return best_agent
```

---

## ۷. مدیریت خطا و استراتژی‌های Retry (Error Handling & Retry) {#errors}

ارتباط در MAS ذاتاً **غیرقابل اطمینان (unreliable)** است — agentها ممکن است کرش کنند، شبکه قطع شود، یا پیام گم شود. یک سیستم MAS بالغ باید سناریوهای خطا را به صورت ساختیافته مدیریت کند.

### ۷.۱ انواع خطا در ارتباط MAS (Failure Types)

| نوع خطا | علت | شدت |
|---------|------|-----|
| **Agent Crash** | agent از کار می‌افتد (خطای نرم‌افزاری، OOM) | 🔴 بالا |
| **Network Partition** | قطعی شبکه، agent قابل دسترس نیست | 🔴 بالا |
| **Message Timeout** | پیام ارسال شد اما پاسخی نرسید | 🟡 متوسط |
| **Message Loss** | پیام در مسیر گم شد | 🟡 متوسط |
| **Stale Data** | agent با داده‌های قدیمی کار می‌کند | 🟡 متوسط |
| **Rate Limit** | agent بیش از حد مجاز درخواست فرستاد | 🟢 کم |

### ۷.۲ الگوهای Retry (Retry Strategies)

```text
┌──────────────────────────────────────────────────────────────┐
│                استراتژی‌های Retry در MAS                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ۱. Retry ساده (Simple Retry):                                │
│     ┌─────┐   fail   ┌─────┐   fail   ┌─────┐   success     │
│     │Send  │────────→│Send  │────────→│Send  │────────────→  │
│     └─────┘          └─────┘          └─────┘               │
│     ✦ max_retries=3, wait=1s                                 │
│                                                               │
│  ۲. Exponential Backoff:                                      │
│     ┌─────┐   fail   ┌─────┐   fail   ┌─────┐               │
│     │Send  │────────→│Wait  │────────→│Send  │────...──→     │
│     └─────┘   1s     │1s→2s│   2s     │2s→4s│               │
│                       └─────┘          └─────┘               │
│     ✦ wait = base * (2 ** attempt) + jitter                  │
│                                                               │
│  ۳. Circuit Breaker:                                          │
│     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│     │   CLOSED     │───→│    OPEN      │───→│  HALF-OPEN   │ │
│     │  (normal)    │    │  (blocked)   │    │  (probing)   │ │
│     └──────────────┘    └──────────────┘    └──────┬───────┘ │
│            ↑                                        │        │
│            └────────────────────────────────────────┘        │
│     ✦ بعد از N خطا، درخواست‌ها متوقف می‌شوند                 │
│     ✦ بعد از timeout، یک درخواست آزمایشی فرستاده می‌شود      │
│                                                               │
│  ۴. Dead Letter Queue (DLQ):                                  │
│     ┌─────────┐    ┌────────────┐    ┌─────────────┐        │
│     │ بعد از  │───→│   DLQ      │───→│  انسان /     │        │
│     │ max_retry│    │  (صف مرگ)  │    │  escalation │        │
│     └─────────┘    └────────────┘    └─────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

### ۷.۳ پیاده‌سازی Retry در HiveOS

HiveOS از طریق `Message.retry_count` و `Message.ttl` استراتژی retry را پیاده‌سازی می‌کند:

```python
# HiveOS Communication Bus — Retry Logic
class CommunicationBus:
    def publish_with_retry(
        self,
        msg_type: MessageType,
        payload: Dict[str, Any],
        recipient: str,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """پابلیش با retry خودکار و exponential backoff"""

        for attempt in range(max_retries):
            response = self.request(
                msg_type=msg_type,
                payload=payload,
                recipient=recipient,
                timeout=timeout,
            )

            if response is not None:
                return response

            # Exponential backoff with jitter
            wait = (2 ** attempt) + random.uniform(0, 1)
            console.print(f"[yellow]⚠ Retry {attempt+1}/{max_retries} "
                          f"after {wait:.1f}s[/yellow]")
            time.sleep(wait)

        # All retries exhausted — route to DLQ / escalate
        self._escalate_to_mothership(msg_type, payload, recipient)
        return None
```

**Circuit Breaker در HiveOS (از resilience.py):**
```python
# HiveOS Resilience Engine — Circuit Breaker
class CircuitBreaker:
    """Circuit breaker برای جلوگیری از بمباران agentهای خراب."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_count: Dict[str, int] = defaultdict(int)
        self.circuit_open_until: Dict[str, float] = {}
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def can_send(self, agent_id: str) -> bool:
        """آیا می‌توان به این agent پیام فرستاد؟"""
        if agent_id in self.circuit_open_until:
            if time.time() < self.circuit_open_until[agent_id]:
                return False  # Circuit is OPEN
            else:
                # Circuit HALF-OPEN — یک درخواست آزمایشی مجاز است
                del self.circuit_open_until[agent_id]
                self.failure_count[agent_id] = 0
                return True
        return True

    def record_failure(self, agent_id: str):
        """ثبت خطا — اگر از حد گذشت، circuit را باز کن"""
        self.failure_count[agent_id] += 1
        if self.failure_count[agent_id] >= self.failure_threshold:
            self.circuit_open_until[agent_id] = time.time() + self.recovery_timeout
```

---

## ۸. جدول مقایسه الگوهای ارتباطی (Comparison Table) {#comparison}

| ویژگی | Direct Messaging | Blackboard | Event-Driven | Pub/Sub |
|-------|-----------------|------------|--------------|---------|
| **Coupling** | Tight | Loose | Very Loose | Very Loose |
| **مقیاس‌پذیری** | ❌ ضعیف (O(n²)) | 🟡 متوسط | ✅ عالی | ✅ عالی |
| **Fault Tolerance** | ❌ ضعیف | 🟡 (SFoP) | ✅ خوب | ✅ خوب |
| **تأخیر (Latency)** | ✅ کم | 🟡 متوسط | 🟡 متوسط | 🟡 متوسط |
| **Persistency** | ❌ ندارد | ✅ دارد | ✅ دارد (با event store) | ✅ دارد (با queue) |
| **پیچیدگی** | ✅ کم | 🟡 متوسط | 🔴 بالا | 🔴 بالا |
| **Debugging** | ✅ آسان | 🟡 متوسط | ❌ دشوار | ❌ دشوار |
| **Ordering** | ✅ تضمین‌شده | ❌不确定 | ❌不确定 | ❌不确定 |
| **Audit Trail** | ❌ محدود | ✅ کامل | ✅ کامل | ✅ کامل |
| **هزینه عملیاتی** | کم | کم | متوسط | متوسط-بالا |
| **موارد استفاده** | ارتباطات دوتایی، فرمان‌های کنترلی | همکاری تیمی، اشتراک دانش | رویدادهای کسب‌وکار، CDC | توزیع بار، اعلان‌ها |
| **HiveOS Backend** | Direct AGENT_MESSAGE | — | — | MessageType subscription |

**راهنمای انتخاب (Selection Guide):**

```
سوال: چه پارادایمی انتخاب کنم؟
│
├─ اگر فقط دو agent دارم که مستقیما حرف می‌زنند → Direct Messaging
│
├─ اگر agentها نیاز به اشتراک دانش دارند → Blackboard / Shared Memory
│
├─ اگر agentها باید به تغییرات واکنش نشان دهند → Event-Driven
│
└─ اگر مقیاس بزرگ است و agentها مستقل هستند → Pub/Sub
      │
      └─ در HiveOS: از Communication Bus با subscribe استفاده کن
```

---

## ۹. پیاده‌سازی در HiveOS — Communication Bus و Mothership {#hiveos}

HiveOS از یک **Communication Bus لایه‌بندی‌شده (layered bus)** استفاده می‌کند که از ترکیب پارادایم‌های مختلف بهره می‌برد:

### ۹.۱ معماری Bus در HiveOS

```text
┌──────────────────────────────────────────────────────────────┐
│            HiveOS — معماری لایه‌های ارتباطی                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  Mothership (Orchestrator)                          │     │
│  │  ┌───────────────────────────────────────────────┐  │     │
│  │  │  CommunicationBus (Core)                      │  │     │
│  │  │  • publish() / subscribe() / request()        │  │     │
│  │  │  • reply() / broadcast()                      │  │     │
│  │  └──────────────────────┬────────────────────────┘  │     │
│  └─────────────────────────┼───────────────────────────┘     │
│                            │                                  │
│            ┌───────────────┼───────────────┐                  │
│            │               │               │                  │
│     ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐          │
│     │ InMemoryBus │ │ FileBus    │ │ HTTP / NATS │ (Future) │
│     │ (تست / محلی) │ │ (چند پروسه) │ │ (توزیع‌شده)   │          │
│     └─────────────┘ └────────────┘ └─────────────┘          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  پشتیبانی از همه پارادایم‌ها:                        │     │
│  │  • Direct: AGENT_MESSAGE با recipient مشخص          │     │
│  │  • Pub/Sub: subscribe() با MessageType فیلتر        │     │
│  │  • Event-Driven: از MessageType به عنوان event type │     │
│  │  • Request-Response: request() با correlation_id    │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### ۹.۲ MessageTypeهای ارتباطی در HiveOS

HiveOS Communication Bus از `MessageType` Enum برای طبقه‌بندی پیام‌ها استفاده می‌کند:

| دسته | MessageType | توضیح |
|------|-------------|-------|
| **Control Plane** | `HEARTBEAT`, `NODE_REGISTER`, `HEALTH_CHECK` | مدیریت گره‌ها |
| **Task** | `TASK_ASSIGN`, `TASK_START`, `TASK_COMPLETE`, `TASK_FAILED`, `TASK_REROUTE` | orchestration تسک |
| **Agent Comm** | `AGENT_MESSAGE`, `AGENT_BROADCAST`, `AGENT_REPLY` | ارتباط مستقیم agentها |
| **Knowledge Sync** | `SYNC_PUSH`, `SYNC_PULL`, `SKILL_UPDATE`, `KNOWLEDGE_UPDATE` | همگام‌سازی دانش |
| **Control** | `SHUTDOWN`, `RELOAD_CONFIG`, `PAUSE_FLOW`, `RESUME_FLOW` | فرمان‌های کنترلی |

### ۹.۳ جریان ارتباطی کامل در HiveOS

```text
┌─────────────────────────────────────────────────────────────────┐
│    جریان ارتباطی: از درخواست کاربر تا پاسخ نهایی                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  کاربر                    Mothership              Worker Agent  │
│  ─────                    ──────────              ──────────── │
│    │                          │                        │        │
│    │  ۱. ارسال درخواست       │                        │        │
│    │────────────────────────→│                        │        │
│    │                          │                        │        │
│    │                    ۲. تحلیل و تجزیه درخواست       │        │
│    │                       (orchestrator)             │        │
│    │                          │                        │        │
│    │                    ۳. publish(TASK_ASSIGN)       │        │
│    │                          │────────────────────────→│        │
│    │                          │                        │        │
│    │                          │  ۴. Agent کار را شروع  │        │
│    │                          │     می‌کند             │        │
│    │                          │                        │        │
│    │                    ۵. publish(TASK_PROGRESS)     │        │
│    │                          │←────────────────────────│        │
│    │                          │                        │        │
│    │                          │  ۶. مذاکره با agent    │        │
│    │                          │     دیگر (A2A-like)    │        │
│    │                          │     از طریق bus        │        │
│    │                          │◄──────────────────────►│        │
│    │                          │                        │        │
│    │                    ۷. publish(TASK_COMPLETE)     │        │
│    │                          │←────────────────────────│        │
│    │                          │                        │        │
│    │  ۸. تحویل نتیجه نهایی    │                        │        │
│    │←─────────────────────────│                        │        │
│    │                          │                        │        │
│    │  ✦ همه ارتباطات از طریق Communication Bus عبور   │        │
│    │     می‌کند — agentها مستقیماً با هم حرف نمی‌زنند │        │
│    │  ✦ این loose coupling اجازه مقیاس‌پذیری و fault  │        │
│    │     tolerance را می‌دهد                            │        │
└─────────────────────────────────────────────────────────────────┘
```

### ۹.۴ کد کامل — یک سناریو ارتباطی

```python
"""HiveOS — سناریوی ارتباط و هماهنگی بین agentها"""

from hiveos.mothership.communication_bus import (
    CommunicationBus, MessageType, MessagePriority
)
from hiveos.mothership.agent_registry import AgentRegistry
from hiveos.mothership.task_router import TaskRouter
from hiveos.mothership.resilience import CircuitBreaker

# ── راه‌اندازی ──────────────────────────────────
bus = CommunicationBus(node_id="mothership")
registry = AgentRegistry()
router = TaskRouter(bus=bus, registry=registry)
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

# ── ثبت agentها در bus ─────────────────────────
def research_callback(msg):
    """Agent تحقیقاتی — به تسک‌های تحقیق پاسخ می‌دهد"""
    if msg.type == MessageType.TASK_ASSIGN:
        topic = msg.payload.get("topic")
        result = do_research(topic)
        bus.task_complete("research-agent-01", msg.payload["task_id"], result)

def writer_callback(msg):
    """Agent نویسنده — محتوا را می‌نویسد"""
    if msg.type == MessageType.TASK_ASSIGN:
        draft = write_content(msg.payload["research_data"])
        bus.task_complete("writer-agent-01", msg.payload["task_id"], draft)

bus.subscribe([MessageType.TASK_ASSIGN], research_callback)
bus.subscribe([MessageType.TASK_ASSIGN], writer_callback)

# ── ارسال تسک با retry و circuit breaker ────────
def dispatch_task_with_safety(task_id: str, capability: str, payload: dict):
    """ارسال تسک با مدیریت خطا"""

    worker = router.find_optimal_worker(capability)

    if not cb.can_send(worker.node_id):
        print(f"⚠ Circuit open for {worker.node_id}, trying fallback...")
        worker = router.find_fallback_worker(capability)

    response = bus.publish_with_retry(
        msg_type=MessageType.TASK_ASSIGN,
        payload={"task_id": task_id, **payload},
        recipient=worker.node_id,
        max_retries=3,
    )

    if response is None:
        cb.record_failure(worker.node_id)
        # Escalate to Mothership supervisor
        bus.publish(
            MessageType.TASK_REROUTE,
            {"task_id": task_id, "reason": "all_retries_exhausted"},
            recipient="mothership",
            priority=MessagePriority.HIGH,
        )
    else:
        print(f"✅ Task {task_id} completed by {worker.node_id}")
```

---

## ۱۰. نکات کلیدی (Key Takeaways) {#takeaways}

1. **ارتباط (Communication)** و **هماهنگی (Coordination)** دو ستون اصلی MAS هستند — بدون آنها agentها فقط موجودیت‌های منزوی‌اند

2. **چهار پارادایم ارتباطی** اصلی وجود دارد: Direct Messaging (ساده و سریع)، Blackboard (مناسب برای اشتراک دانش)، Event-Driven (مناسب برای واکنش به تغییرات)، Pub/Sub (مناسب برای مقیاس بزرگ)

3. **MCP** برای اتصال agent به ابزارهاست، **A2A** (به ویژه Google A2A) برای ارتباط مستقیم بین agentها — این دو مکمل هم هستند

4. **انتخاب الگوی هماهنگی** به نیاز سیستم بستگی دارد: Centralized برای کنترل قوی، Decentralized برای مقیاس و انعطاف، Hierarchical برای سازمان‌های بزرگ، Supervisor برای سیستم‌های حساس

5. **حل تعارض** باید از ابتدا در معماری MAS پیش‌بینی شود — استراتژی‌هایی مانند Locking، Voting، Arbitration و Escalation

6. **مدیریت خطا** با استراتژی‌هایی مانند Retry با Exponential Backoff، Circuit Breaker، و Dead Letter Queue از الزامات یک MAS تولیدی است

7. **HiveOS** از طریق Communication Bus خود از همه این الگوها پشتیبانی می‌کند — با لایه‌بندی مناسب بین transport, protocol, و message

---

## ۱۱. منابع (References) {#references}

- **arXiv 2501.13671** — "A Taxonomy of Agent Communication Protocols for Multi-Agent Systems" (2025)
- **Google A2A Specification** — Agent-to-Agent Protocol, Google (2025)
- **MCP Specification** — Model Context Protocol, Anthropic (2024-2025)
- **HiveOS Source Code** — `src/hiveos/mothership/communication_bus.py`, `resilience.py`, `task_router.py`, `agent_registry.py`
- **Russell & Norvig** — "Artificial Intelligence: A Modern Approach" (Ch. 2: Intelligent Agents)
- **Wooldridge, M.** — "An Introduction to MultiAgent Systems" (2009, Wiley)

---

> **فایل‌های مرتبط:**
> - `01-orchestration-patterns.md` — الگوهای Orchestration در MAS
> - `03-task-decomposition.md` — تجزیه وظایف در سیستم‌های چندعامله
> - `03-Frameworks/01-agent-frameworks-overview.md` — مروری بر فریمورک‌های MAS

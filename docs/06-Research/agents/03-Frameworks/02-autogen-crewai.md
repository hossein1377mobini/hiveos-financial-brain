# نبرد غول‌ها: AutoGen در مقابل CrewAI — معماری، کد و تصمیم‌گیری برای تولید
## Battle of the Titans: AutoGen vs CrewAI — Architecture, Code & Production Decisions

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **نسخه:** v1.0  
> **مسیر:** `docs/06-Research/agents/03-Frameworks/02-autogen-crewai.md`  
> **پیش‌نیاز:** مطالعه `01-agent-frameworks-overview.md` برای نمای کلی چهارچهارچوب

---

## فهرست مطالب (Table of Contents)

1. [چرا AutoGen و CrewAI را عمیق مقایسه می‌کنیم؟](#why-compare)
2. [فلسفه معماری — دو دنیای متفاوت](#architecture-philosophy)
3. [AutoGen (مایکروسافت): غرق در مکالمه](#autogen-deep-dive)
   - [معماری Core v0.4 — رویدادمحور و ناهمگام](#autogen-arch)
   - [AssistantAgent — هسته مکالمه](#autogen-assistant)
   - [UserProxyAgent — پل انسان و ماشین](#autogen-userproxy)
   - [GroupChat — سمفونی چندعاملی](#autogen-groupchat)
   - [اجرای کد — سندباکس Docker](#autogen-code-exec)
   - [نمودار معماری](#autogen-diagram)
4. [CrewAI: تیم رویاهای شما](#crewai-deep-dive)
   - [معماری نقش‌محور — تیم انسانی دیجیتال](#crewai-arch)
   - [Agent — نقش، هدف، پیشینه](#crewai-agent)
   - [Task — وظیفه با ورودی و خروجی شفاف](#crewai-task)
   - [Crew — هماهنگ‌کننده نهایی](#crewai-crew)
   - [Process — ترتیبی و سلسله‌مراتبی](#crewai-process)
   - [Flows — لایه ارکستراسیون جدید](#crewai-flows)
   - [Tools — جعبه ابزار عامل‌ها](#crewai-tools)
   - [نمودار معماری](#crewai-diagram)
5. [کد یکسان، دو فریمورک — تحقیق + تحلیل + نوشتن](#same-task-code)
   - [سناریو: تحلیل رقابتی بازار AI Agents](#code-scenario)
   - [پیاده‌سازی با AutoGen v0.4](#code-autogen)
   - [پیاده‌سازی با CrewAI](#code-crewai)
   - [مقایسه کد خط به خط](#code-comparison)
6. [ماتریس تصمیم — چه زمانی کدام را انتخاب کنیم؟](#decision-matrix)
7. [مقایسه آمادگی برای تولید (Production Readiness)](#production-readiness)
8. [موارد استفاده واقعی (Real-World Use Cases)](#real-world-cases)
9. [ارتباط با الگوهای HiveOS](#hiveos-connection)
10. [جمع‌بندی و توصیه نهایی](#conclusion)

---

## ۱. چرا AutoGen و CrewAI را عمیق مقایسه می‌کنیم؟ {#why-compare}

در فریمورک‌های AI Agent، **AutoGen (مایکروسافت)** و **CrewAI** دو تا از محبوب‌ترین گزینه‌ها با فلسفه‌های معماری کاملاً متفاوت هستند:

| ویژگی | AutoGen | CrewAI |
|-------|---------|--------|
| ⭐ GitHub Stars | ~35K+ | ~25K+ |
| 🏢 توسعه‌دهنده | Microsoft Research | CrewAI Inc. |
| 📅 اولین انتشار | ۲۰۲۳ | ۲۰۲۳ |
| 🎭 فلسفه | **مکالمه‌محور (Conversational)** | **نقش‌محور (Role-Based)** |
| 🏗️ معماری | رویدادمحور، ناهمگام، مبتنی بر پیام | تیمی، ترتیبی/سلسله‌مراتبی |
| 🐍 API | v0.4: async/await, event-driven | Synchronous + Flows (async) |

این دو فریمورک در نگاه اول کار مشابهی انجام می‌دهند — orchestration چندعاملی — اما فلسفه معماری آن‌ها آنقدر متفاوت است که انتخاب بین آن‌ها تأثیر عمیقی بر **قابلیت توسعه (extensibility)**، **هزینه عملیاتی (operational cost)** و **تجربه توسعه‌دهنده (developer experience)** پروژه شما خواهد داشت.

> **نکته کلیدی:** انتخاب بین AutoGen و CrewAI انتخاب بین «مکالمه» و «تیم» است. اولی می‌گوید «بگذارید عامل‌ها با هم حرف بزنند»، دومی می‌گوید «بگذارید هر کسی نقش خودش را بازی کند».

---

## ۲. فلسفه معماری — دو دنیای متفاوت {#architecture-philosophy}

### مکالمه‌محوری (Conversational-First) — AutoGen

فلسفه AutoGen ساده است: **عامل‌ها با هم حرف می‌زنند و workflow خودبه‌خود شکل می‌گیرد**. شما جعبه‌هایی به نام Agent تعریف می‌کنید، یک اتاق گفتگو به نام GroupChat به آن‌ها می‌دهید، و می‌گذارید مکالمه جریان پیدا کند. کنترل جریان (flow control) به صورت **پویا (dynamic)** توسط LLM تصمیم‌گیری می‌شود — یعنی LLM تعیین می‌کند که کدام عامل در هر مرحله صحبت کند.

این پارادایم شبیه **بازار آزاد (free market)** ایده‌هاست — اطلاعات آزادانه جریان دارد و ساختار به صورت خودجوش شکل می‌گیرد.

**نقاط قوت:**
- برای وظایف اکتشافی (exploratory) و خلاقانه عالی است
- عامل‌ها می‌توانند سوال بپرسند، ابهام‌زدایی کنند، برگردند
- شبیه نحوه کار تیم‌های انسانی در جلسات طوفان فکری

**نقاط ضعف:**
- پیش‌بینی مسیر مکالمه غیرممکن است
- دیباگ کردن سخت است — چه کسی کی چه گفت؟
- هزینه LLM بالا به دلیل چرخش‌های بی‌هدف

### نقش‌محوری (Role-First) — CrewAI

فلسفه CrewAI: **وظایف پیچیده را عامل‌های تخصصی که هر کدام نقش مشخصی دارند بهتر حل می‌کنند**. شما یک تیم تعریف می‌کنید — Researcher، Analyst، Writer — و به هر کدام یک وظیفه خاص می‌دهید. جریان کار (workflow) به صورت **صریح (explicit)** تعریف می‌شود: Researcher کارش که تمام شد، Analyst شروع می‌کند.

این پارادایم شبیه **خط مونتاژ (assembly line)** کارخانه است — هر ایستگاه کار مشخصی انجام می‌دهد و محصول نهایی از خط خارج می‌شود.

**نقاط قوت:**
- پیش‌بینی‌پذیر — دقیقاً می‌دانید چه کسی چه کاری کی انجام می‌دهد
- دیباگ آسان — خروجی هر task مجزاست
- هزینه LLM کنترل‌شده — تعداد فراخوانی مشخص

**نقاط ضعف:**
- انعطاف کمتر برای وظایف اکتشافی
- عامل‌ها نمی‌توانند به راحتی از وظیفه خود منحرف شوند
- تعامل پویا محدود است

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│  AutoGen — Conversational (مکالمه‌محور)                                       │
│                                                                              │
│    ┌──────────┐    "I found 3 frameworks"     ┌──────────┐                  │
│    │Researcher│──────────────────────────────▶│ Analyst  │                  │
│    └──────────┘                                └──────────┘                  │
│         ▲                                          │                        │
│         │  "Can you elaborate on X?"               │  "Here's the analysis" │
│         │                                          ▼                        │
│    ┌──────────┐                                ┌──────────┐                  │
│    │  Writer  │◀──────────────────────────────│   Critic │                  │
│    └──────────┘   "Needs more data on Y"      └──────────┘                  │
│                                                                              │
│    جریان: پویا — LLM تصمیم می‌گیرد کی حرف بزند                                │
│    همه چیز از طریق مبادله پیام (Message Passing)                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  CrewAI — Role-Based (نقش‌محور)                                               │
│                                                                              │
│    ┌──────────┐    task1: Research    ┌──────────┐    task2: Analyze         │
│    │Researcher│──────────────────────▶│ Analyst  │──────────────────────────▶│
│    │Role: PhD │    context: []        │Role: Sr  │    context: [task1]       │
│    │Tools: [S]│                       │Tools: [D]│                           │
│    └──────────┘                       └──────────┘                           │
│                                                                              │
│    ┌──────────┐    task3: Write Final Report     ┌──────────┐                │
│    │  Writer  │◀─────────────────────────────────│  Critic  │                │
│    │Role: Tech│    context: [task1, task2]       │Role: Ed. │                │
│    └──────────┘                                   └──────────┘                │
│                                                                              │
│    جریان: صریح — شما تعیین می‌کنید کی چه کاری انجام دهد                       │
│    خروجی هر task وابستگی صریح به task قبلی دارد                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## ۳. AutoGen (مایکروسافت): غرق در مکالمه {#autogen-deep-dive}

### ۳.۱ معماری Core v0.4 — رویدادمحور و ناهمگام {#autogen-arch}

AutoGen در نسخه **v0.4** یک بازنویسی کامل (from-the-ground-up rewrite) را تجربه کرد. معماری جدید:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AutoGen v0.4 — معماری لایه‌ای (Layered Architecture)                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AgentChat API (لایه بالایی — Task-Driven)                          │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐    │   │
│  │  │Assistant   │ │UserProxy   │ │GroupChat   │ │SelectorGroup│    │   │
│  │  │Agent       │ │Agent       │ │Team        │ │Chat         │    │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Core API (لایه پایه — Event-Driven Actor Framework)                │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐    │   │
│  │  │RoutedAgent │ │Message     │ │Topic       │ │AgentRuntime  │    │   │
│  │  │(بازیگر)    │ │(پیام)      │ │(موضوع)     │ │(زمان اجرا)   │    │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Extensions (افزونه‌ها)                                              │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────────┐  │   │
│  │  │OpenAI / Azure    │ │Docker Code Exec │ │WebSurfer / FileSurfer│  │   │
│  │  │Model Clients     │ │(سندباکس)        │ │(عامل‌های مرورگر)     │  │   │
│  │  └─────────────────┘ └─────────────────┘ └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Core API** یک **چارچوب بازیگری رویدادمحور (Event-Driven Actor Framework)** است:
- **RoutedAgent:** هر عامل یک بازیگر (actor) است که پیام‌های异步 دریافت می‌کند
- **Message:** همه چیز پیام است — درخواست، پاسخ، ابزار، خطا
- **Topic:** کانال‌های ارتباطی برای انتشار/اشتراک پیام
- **AgentRuntime:** موتور اجرای ناهمگام که پیام‌ها را مسیریابی می‌کند

**AgentChat API** لایه بالایی است که توسعه‌دهندگان معمولاً با آن کار می‌کنند:
- AssistantAgent، UserProxyAgent، GroupChat، GroupChatManager
- API مبتنی بر `async/await` و `CancellationToken`
- پشتیبانی از `streaming` توکن‌به‌توکن

```python
# نمونه API مدرن AutoGen v0.4
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent1 = AssistantAgent(
        name="Researcher",
        model_client=model_client,
        system_message="شما یک محقق هستید."
    )
    
    agent2 = AssistantAgent(
        name="Writer",
        model_client=model_client,
        system_message="شما یک نویسنده فنی هستید."
    )
    
    termination = TextMentionTermination("FINAL")
    
    team = RoundRobinGroupChat(
        [agent1, agent2],
        termination_condition=termination
    )
    
    result = await team.run(task="تحقیق درباره AI Agents در 2026")
    print(result.messages[-1].content)

asyncio.run(main())
```

### ۳.۲ AssistantAgent — هسته مکالمه {#autogen-assistant}

**AssistantAgent** عامل اصلی AutoGen است — یک عامل مبتنی بر LLM که می‌تواند:

- به پیام‌ها پاسخ دهد
- از ابزارها (tools) استفاده کند
- کد تولید کند
- مدل‌ها را تغییر دهد (model switching)

```python
assistant = AssistantAgent(
    name="Assistant",
    model_client=OpenAIChatCompletionClient(
        model="gpt-4o",
        temperature=0.7,
        seed=42
    ),
    system_message="""شما یک دستیار هوشمند هستید.
قوانین:
1. ابتدا فکر کنید، سپس پاسخ دهید
2. اگر نیاز به اجرای کد دارید، کد را در بلاک ```python تولید کنید
3. اگر مطمئن نیستید، سوال بپرسید""",
    reflect_on_tool_use=True,  # بازتاب روی نتیجه ابزار
    tools=[search_tool, calculator_tool]
)
```

**نکته مهم:** در نسخه v0.4، همه چیز `async` است. `on_messages()` جای `generate_reply()` را گرفته است. `CancellationToken` امکان لغز اجرا را می‌دهد.

### ۳.۳ UserProxyAgent — پل انسان و ماشین {#autogen-userproxy}

**UserProxyAgent** نماینده انسان در سیستم است. می‌تواند:

- کد را اجرا کند (محلی یا در Docker)
- ورودی انسانی را شبیه‌سازی کند
- فایل‌ها را ذخیره کند

```python
from autogen import UserProxyAgent
from autogen.coding import LocalCommandLineCodeExecutor

executor = UserProxyAgent(
    name="Executor",
    code_execution_config={
        "executor": LocalCommandLineCodeExecutor(
            work_dir="coding",
            timeout=60
        ),
        "use_docker": True,  # یا "python:3-slim"
        "last_n_messages": 3  # فقط ۳ پیام آخر را بررسی کن
    },
    human_input_mode="NEVER",  # یا "ALWAYS" یا "TERMINATE"
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "FINAL ANSWER" in x.get("content", "")
)
```

**حالت‌های human_input_mode:**
| حالت | توضیح |
|------|-------|
| `"ALWAYS"` | قبل از هر پاسخ از انسان سوال می‌کند |
| `"TERMINATE"` | فقط هنگام پایان از انسان سوال می‌کند |
| `"NEVER"` | کاملاً خودکار، هرگز از انسان نمی‌پرسد |

### ۳.۴ GroupChat — سمفونی چندعاملی {#autogen-groupchat}

**GroupChat** قلب سیستم چندعاملی AutoGen است — یک اتاق گفتگو که عامل‌ها در آن پیام رد و بدل می‌کنند.

انواع GroupChat در AutoGen v0.4:

| نوع | توضیح | کاربرد |
|-----|-------|--------|
| `RoundRobinGroupChat` | هر عامل به ترتیب صحبت می‌کند | ساده‌ترین، پیش‌بینی‌پذیرترین |
| `SelectorGroupChat` | LLM انتخاب می‌کند چه کسی صحبت کند | مکالمه پویا، پیچیده |
| `SwarmGroupChat` | الگوی Swarm از OpenAI | هماهنگی غیرمتمرکز |

```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

# شرط پایان: ۲۰ پیام یا دیدن "FINISH"
termination = (
    TextMentionTermination("FINISH") |
    MaxMessageTermination(20)
)

team = SelectorGroupChat(
    agents=[researcher, analyst, writer, critic],
    model_client=selector_client,  # LLM برای انتخاب speaker
    termination_condition=termination,
    selector_prompt="""با توجه به گفتگوی زیر، بهترین عامل برای ادامه کیست؟
عامل‌ها: {roles}
تاریخچه: {history}
بهترین انتخاب:""",
    max_turns=30,
    allow_repetition=False
)

result = await team.run(task="یک مقاله تحلیلی بنویس")
```

**مکانیسم انتخاب Speaker در SelectorGroupChat:**

```
پیام کاربر (user message)
       │
       ▼
┌──────────────────────┐
│ گروه چت (GroupChat)  │
│                      │
│  ۱. دریافت پیام       │
│  ۲. LLM بررسی می‌کند  │
│  ۳. speaker بعدی را  │
│     انتخاب می‌کند     │
│  ۴. پیام را ارسال     │
│     می‌کند            │
└──────────────────────┘
       │
       ▼
عامل انتخاب‌شده ──▶ پاسخ ──▶ گروه چت ──▶ (تکرار)
```

### ۳.۵ اجرای کد — سندباکس Docker {#autogen-code-exec}

یکی از نقاط قوت بی‌نظیر AutoGen، **اجرای امن کد (Secure Code Execution)** است:

```python
from autogen.coding import DockerCommandLineCodeExecutor
from autogen import UserProxyAgent

# Docker sandbox
docker_executor = DockerCommandLineCodeExecutor(
    image="python:3.11-slim",
    container_name="autogen-sandbox",
    timeout=120,
    work_dir="coding",
    auto_remove=True  # خودکار حذف بعد از اتمام
)

agent = UserProxyAgent(
    name="CodeRunner",
    code_execution_config={"executor": docker_executor}
)
```

**سطوح اجرای کد:**

| روش | امنیت | سرعت | موارد استفاده |
|-----|-------|------|--------------|
| `LocalCommandLineCodeExecutor` | ❌ پایین | ✅ بالا | توسعه محلی، اعتماد کامل |
| `DockerCommandLineCodeExecutor` | ✅ بالا | ⚠️ متوسط | محیط تولید، کد ناشناس |
| `ACADynamicSessionsCodeExecutor` | ✅ بالا | ✅ بالا | Azure، مقیاس بزرگ |

### ۳.۶ نمودار معماری کامل AutoGen {#autogen-diagram}

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│  AutoGen v0.4 — معماری کامل                                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  AGENTCHAT API (برای توسعه‌دهندگان)                                │      │
│  │                                                                     │      │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │      │
│  │  │ Assistant    │    │ UserProxy    │    │ ToolAgent    │          │      │
│  │  │ Agent        │    │ Agent        │    │ (Built-in)   │          │      │
│  │  │              │    │              │    │              │          │      │
│  │  │ • LLM-driven │    │ • Code Exec  │    │ • WebSurfer  │          │      │
│  │  │ • Tool Use   │    │ • Human Inp  │    │ • FileSurfer │          │      │
│  │  │ • Reflection │    │ • File I/O   │    │ • PDFSurfer  │          │      │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │      │
│  │         └────────┬──────────┘───────────────────┘                  │      │
│  │                  ▼                                                 │      │
│  │         ┌──────────────────┐                                      │      │
│  │         │  Team Chat       │                                      │      │
│  │         │  (GroupChat)     │                                      │      │
│  │         │  • RoundRobin    │                                      │      │
│  │         │  • Selector      │     ┌─────────────────────────┐      │      │
│  │         │  • Swarm         │────▶│ Termination Conditions  │      │      │
│  │         └──────────────────┘     │ • Text Mention          │      │      │
│  │                                  │ • Max Messages          │      │      │
│  │                                  │ • Token Limit           │      │      │
│  │                                  │ • Custom Function       │      │      │
│  │                                  └─────────────────────────┘      │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  CORE API (بنیان رویدادمحور)                                       │      │
│  │                                                                     │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │      │
│  │  │ RoutedAgent  │  │   Message    │  │    Topic     │              │      │
│  │  │ (Actor)      │  │   (Payload)  │  │  (Channel)   │              │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │      │
│  │  │AgentRuntime  │  │Cancellation  │  │Logging/Trace │              │      │
│  │  │(Scheduler)   │  │Token         │  │(OpenTelemetry)│              │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  EXTENSIONS (افزونه‌های رسمی)                                       │      │
│  │                                                                     │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │      │
│  │  │ Model Clients│  │  Executors   │  │  Agent Types │              │      │
│  │  │ • OpenAI     │  │ • Local      │  │ • CodeWriter │              │      │
│  │  │ • Azure      │  │ • Docker     │  │ • WebSurfer  │              │      │
│  │  │ • Ollama     │  │ • ACA Dync   │  │ • FileSurfer │              │      │
│  │  │ • Gemini     │  │              │  │ • RAG Agent  │              │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │      │
│  └────────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## ۴. CrewAI: تیم رویاهای شما {#crewai-deep-dive}

### ۴.۱ معماری نقش‌محور — تیم انسانی دیجیتال {#crewai-arch}

CrewAI از این ایده پیروی می‌کند که **عامل‌ها باید مثل انسان‌های حرفه‌ای رفتار کنند**. شما به هر عامل یک **نقش (role)**، یک **هدف (goal)** و یک **پیشینه (backstory)** می‌دهید — درست مثل اعضای یک تیم استارتاپی.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CrewAI — معماری نقش‌محور                                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FLOWS (لایه ارکستراسیون — اختیاری)                                 │   │
│  │  ┌──────────┐          ┌──────────┐          ┌──────────┐         │   │
│  │  │ @start   │─────────▶│ @listen  │─────────▶│ @listen  │         │   │
│  │  │ Flow     │          │ Crew 1   │          │ Crew 2   │         │   │
│  │  └──────────┘          └──────────┘          └──────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CREW (هماهنگی تیم)                                                 │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐      │   │
│  │  │  Agents (نقش‌ها)      │  Tasks (وظایف)                     │      │   │
│  │  │  ┌──────────────────┐ │  ┌────────────────────────────┐   │      │   │
│  │  │  │ Agent: Researcher│ │  │ Task 1: Research          │   │      │   │
│  │  │  │ Role: AI Expert  │ │  │ description: "جستجوی..."   │   │      │   │
│  │  │  │ Goal: Find info   │ │  │ agent: Researcher         │   │      │   │
│  │  │  │ Tools: [Search]   │ │  │ expected_output: "..."    │   │      │   │
│  │  │  └──────────────────┘ │  └────────────────────────────┘   │      │   │
│  │  │  ┌──────────────────┐ │  ┌────────────────────────────┐   │      │   │
│  │  │  │ Agent: Analyst   │ │  │ Task 2: Analyze            │   │      │   │
│  │  │  │ Role: Data Sci   │ │  │ context: [task1]           │   │      │   │
│  │  │  │ Tools: [Python]   │ │  │ agent: Analyst            │   │      │   │
│  │  │  └──────────────────┘ │  └────────────────────────────┘   │      │   │
│  │  │  ┌──────────────────┐ │  ┌────────────────────────────┐   │      │   │
│  │  │  │ Agent: Writer    │ │  │ Task 3: Write Report       │   │      │   │
│  │  │  │ Role: Tech Wri   │ │  │ context: [task1, task2]    │   │      │   │
│  │  │  │ Tools: []        │ │  │ agent: Writer              │   │      │   │
│  │  │  └──────────────────┘ │  └────────────────────────────┘   │      │   │
│  │  └──────────────────────────────────────────────────────────┘      │   │
│  │                                                                     │   │
│  │  Process: Sequential │ Hierarchical │ Consensual                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CORE INFRASTRUCTURE                                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ LLM Provider │  │   Memory     │  │    Tools     │             │   │
│  │  │ • OpenAI     │  │ • Short-term │  │ • Custom     │             │   │
│  │  │ • Anthropic  │  │ • Long-term  │  │ • CrewAI Tls │             │   │
│  │  │ • Ollama     │  │ • Entity     │  │ • LangChain  │             │   │
│  │  │ • Azure      │  │ • User       │  │              │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ۴.۲ Agent — نقش، هدف، پیشینه {#crewai-agent}

عامل در CrewAI یک **شخصیت (persona)** کامل است:

```python
from crewai import Agent

researcher = Agent(
    role="Senior AI Research Scientist",
    goal="کشف آخرین پیشرفت‌های فریمورک‌های AI Agent در سال ۲۰۲۶",
    backstory="""شما یک محقق ارشد با ۱۵ سال سابقه در حوزه NLP و Agent Systems هستید.
    در دانشگاه MIT تحصیل کرده‌اید و مقالات متعددی در NeurIPS و ICML منتشر کرده‌اید.
    به دنبال کشف مرزهای جدید در AI هستید.""",
    tools=[search_tool, arxiv_tool, browser_tool],
    verbose=True,
    allow_delegation=True,  # اجازه واگذاری کار به دیگران
    max_iter=10,  # حداکثر تکرار برای انجام وظیفه
    max_rpm=10,  # Rate limit
    memory=True,  # حافظه کوتاه‌مدت
    cache=True,   # کش کردن فراخوانی‌های LLM
    llm="gpt-4o",  # مدل اختصاصی
    function_calling_llm="gpt-4o-mini",  # مدل ارزان‌تر برای ابزارها
)
```

**پارامترهای کلیدی:**
| پارامتر | توضیح | مقدار پیش‌فرض |
|---------|-------|--------------|
| `role` | نقش عامل — تعیین‌کننده رفتار | اجباری |
| `goal` | هدف کلی — هر task از این مشتق می‌شود | اجباری |
| `backstory` | پیشینه — context اضافی برای LLM | اجباری |
| `allow_delegation` | آیا می‌تواند کار را به دیگران واگذار کند | `False` |
| `max_iter` | حداکثر تکرار برای انجام وظیفه | `15` |
| `memory` | حافظه کوتاه‌مدت | `True` |
| `llm` | مدل LLM | `"gpt-4"` |

### ۴.۳ Task — وظیفه با ورودی و خروجی شفاف {#crewai-task}

**Task** کوچکترین واحد کار در CrewAI است:

```python
from crewai import Task

research_task = Task(
    description="""یک تحقیق جامع درباره وضعیت فعلی فریمورک‌های AI Agent انجام بده.
    
    مواردی که باید پوشش داده شود:
    1. فریمورک‌های محبوب (AutoGen, CrewAI, LangGraph, OpenAI SDK)
    2. روندهای جدید در ۲۰۲۶ (Agent-to-Agent protocols, MCP, A2A)
    3. مقایسه آمادگی برای تولید (Production Readiness)
    
    از ابزار جستجو برای پیدا کردن آخرین اطلاعات استفاده کن.""",
    expected_output="یک گزارش تحلیلی ۵۰۰ کلمه‌ای با حداقل ۵ منبع",
    agent=researcher,
    output_file="research_output.md",  # ذخیره خودکار در فایل
    context=[],  # وابستگی به task قبلی
    async_execution=False,  # اجرای ناهمگام
    callback=lambda output: print(f"✅ Task done: {len(output)} chars"),  # callback
    human_input=False  # نیاز به تأیید انسانی
)
```

**زنجیره Task با context:**

```
Task 1 (Research)
  │
  │ output: research_output.md
  │
  ▼
Task 2 (Analyze) ← context=[Task1]
  │
  │ output: analysis.json
  │
  ▼
Task 3 (Write) ← context=[Task1, Task2]
  │
  ▼
Final Output
```

### ۴.۴ Crew — هماهنگ‌کننده نهایی {#crewai-crew}

**Crew** کلاس orchestration اصلی است که همه چیز را به هم متصل می‌کند:

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # Process.hierarchical
    verbose=True,
    memory=True,  # حافظه بین taskها
    cache=True,
    max_rpm=20,
    share_crew=True,  # اشتراک دانش بین عامل‌ها
    output_log_file="crew_log.txt",
    manager_agent=manager_agent,  # فقط برای hierarchical
    planning=True,  # برنامه‌ریزی خودکار قبل از اجرا
    planning_llm="gpt-4o"
)

# اجرا
result = crew.kickoff()

# یا با ورودی
result = crew.kickoff(inputs={"topic": "AI Agents 2026"})
```

### ۴.۵ Process — ترتیبی و سلسله‌مراتبی {#crewai-process}

CrewAI دو فرآیند اصلی دارد:

#### Sequential Process (پیش‌فرض)

ساده‌ترین حالت: taskها به ترتیب اجرا می‌شوند.

```
[T1: Research] ──▶ [T2: Analyze] ──▶ [T3: Write] ──▶ Output
```

**مزایا:** ساده، پیش‌بینی‌پذیر، خطایابی آسان  
**معایب:** بدون بازخورد (feedback)، بدون تکرار

#### Hierarchical Process

یک **مدیر (Manager Agent)** کارها را بین عامل‌ها توزیع می‌کند:

```
┌──────────────────────────────────────────┐
│  Manager Agent (LLM-driven)               │
│  "با توجه به وظیفه فعلی، چه کسی باید کار│
│   کند؟"                                  │
└────┬─────────────────────────────────┬───┘
     │  "تحقیق کن!"                    │  "تحلیل کن!"
     ▼                                 ▼
┌──────────┐                    ┌──────────┐
│Researcher│                    │ Analyst  │
└──────────┘                    └──────────┘
     │                                 │
     └──────────────┬──────────────────┘
                    ▼
           ┌──────────────────┐
           │ Manager تصمیم     │
           │ می‌گیرد کار تمام │
           │ شده یا نیاز به   │
           │ تکرار دارد       │
           └──────────────────┘
```

```python
manager = Agent(
    role="Project Manager",
    goal="هماهنگی تیم برای تولید بهترین خروجی",
    backstory="مدیری با تجربه در تیم‌های AI",
    allow_delegation=True,
    llm="gpt-4o"
)

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[complex_task],  # یک task کلی
    process=Process.hierarchical,
    manager_agent=manager
)
```

### ۴.۶ Flows — لایه ارکستراسیون جدید {#crewai-flows}

**CrewAI Flows** (اضافه شده در نسخه‌های جدید) یک لایه ارکستراسیون است که به شما امکان می‌دهد چندین Crew را به هم متصل کنید:

```python
from crewai.flow import Flow, start, listen, router
from pydantic import BaseModel

class AnalysisState(BaseModel):
    topic: str = ""
    research: str = ""
    score: float = 0.0

class MarketAnalysisFlow(Flow[AnalysisState]):
    
    @start()
    def initialize(self):
        print("شروع تحلیل بازار")
        self.state.topic = "AI Agents Market 2026"
    
    @listen(initialize)
    def research_crew(self):
        """یک Crew کامل برای تحقیق"""
        research_crew = Crew(
            agents=[researcher],
            tasks=[Task(description=f"Research {self.state.topic}", ...)],
        )
        self.state.research = research_crew.kickoff()
    
    @router(research_crew)
    def quality_check(self):
        """مسیریابی بر اساس کیفیت تحقیق"""
        if self.state.score >= 0.7:
            return "high_quality"
        else:
            return "needs_revision"
    
    @listen("high_quality")
    def write_report(self):
        """گزارش نهایی"""
        ...
    
    @listen("needs_revision")
    def revise_research(self):
        """بازبینی تحقیق"""
        ...

flow = MarketAnalysisFlow()
flow.kickoff()
```

### ۴.۷ Tools — جعبه ابزار عامل‌ها {#crewai-tools}

CrewAI از ابزارها از طریق `@tool` دکوراتور پشتیبانی می‌کند:

```python
from crewai.tools import tool
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    FileReadTool,
    YoutubeVideoSearchTool,
    DOCXSearchTool,
    # ... ده‌ها ابزار از پیش ساخته
)

@tool("Search Web")
def search_web(query: str) -> str:
    """جستجوی اینترنتی برای پیدا کردن اطلاعات"""
    # implementation
    return results

@tool("Calculate Metrics")
def calculate_metrics(data: str) -> dict:
    """تحلیل داده‌های عددی"""
    # implementation
    return {"mean": 42, "std": 5}

# ابزارهای از پیش ساخته CrewAI
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
read_tool = FileReadTool(file_path="data.txt")
```

### ۴.۸ نمودار معماری کامل CrewAI {#crewai-diagram}

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│  CrewAI — معماری کامل                                                        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  APPLICATION LAYER (برنامه)                                        │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │      │
│  │  │    Agent     │  │    Task      │  │    Crew      │             │      │
│  │  │              │  │              │  │              │             │      │
│  │  │ • role       │  │ • desc       │  │ • agents[]   │             │      │
│  │  │ • goal       │  │ • agent      │  │ • tasks[]    │             │      │
│  │  │ • backstory  │  │ • context[]  │  │ • process    │             │      │
│  │  │ • tools[]    │  │ • output     │  │ • memory     │             │      │
│  │  │ • llm        │  │ • callback   │  │ • cache      │             │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │      │
│  │                                                                     │      │
│  │  ┌────────────────────────────────────────────────────────────┐    │      │
│  │  │  FLOWS (اختیاری)                                           │    │      │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │    │      │
│  │  │  │ @start   │ │ @listen  │ │ @router  │ │ @persist     │ │    │      │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │    │      │
│  │  └────────────────────────────────────────────────────────────┘    │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  ORCHESTRATION LAYER (ارکستراسیون)                                 │      │
│  │                                                                     │      │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐       │      │
│  │  │   Sequential   │  │ Hierarchical │  │   Consensual     │       │      │
│  │  │   Process      │  │   Process    │  │ (Future)         │       │      │
│  │  └────────────────┘  └──────────────┘  └──────────────────┘       │      │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐       │      │
│  │  │    Memory      │  │    Cache     │  │  Human Input     │       │      │
│  │  │ • Short-term   │  │ • LLM Cache  │  │ • Callbacks      │       │      │
│  │  │ • Long-term    │  │ • Tool Cache │  │ • Approval       │       │      │
│  │  │ • Entity       │  │              │  │                  │       │      │
│  │  └────────────────┘  └──────────────┘  └──────────────────┘       │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │  INFRASTRUCTURE LAYER (زیرساخت)                                    │      │
│  │                                                                     │      │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐       │      │
│  │  │   LLM Adapter  │  │  Tool System │  │  Logging/Verbose │       │      │
│  │  │ • OpenAI       │  │ • @tool dec. │  │ • Console        │       │      │
│  │  │ • Anthropic    │  │ • CrewAI Tls │  │ • File           │       │      │
│  │  │ • Ollama/Groq  │  │ • LangChain  │  │ • Callbacks      │       │      │
│  │  │ • Azure/Gemini │  │              │  │                  │       │      │
│  │  └────────────────┘  └──────────────┘  └──────────────────┘       │      │
│  └────────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## ۵. کد یکسان، دو فریمورک — تحقیق + تحلیل + نوشتن {#same-task-code}

### ۵.۱ سناریو: تحلیل رقابتی بازار AI Agents {#code-scenario}

یک سیستم سه عاملی می‌سازیم که:

1. **تحقیق:** آخرین فریمورک‌های AI Agent را جستجو می‌کند
2. **تحلیل:** داده‌ها را تحلیل می‌کند و مقایسه می‌کند
3. **نوشتن:** یک گزارش نهایی تولید می‌کند

### ۵.۲ پیاده‌سازی با AutoGen v0.4 {#code-autogen}

```python
"""
AutoGen v0.4 — تحلیل رقابتی بازار AI Agents
Three-agent system: Researcher → Analyst → Writer
با معماری مکالمه‌محور و GroupChat
"""
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken

# --- ابزارها (Tools) ---
async def search_web(query: str) -> str:
    """جستجوی اینترنتی برای تحقیقات بازار"""
    # در عمل: فراخوانی API جستجو
    return f"نتایج جستجو برای: {query}\n1. AutoGen 35K stars\n2. CrewAI 25K stars\n3. LangGraph 20K stars"

async def calculate_growth(data: str) -> str:
    """تحلیل نرخ رشد"""
    return "نرخ رشد: ۴۵٪ سالانه در بازار AI Agents"

# --- تعریف عامل‌ها ---
model_client = OpenAIChatCompletionClient(model="gpt-4o")

researcher = AssistantAgent(
    name="Researcher",
    model_client=model_client,
    system_message="""شما یک محقق بازار AI هستید.
    
وظایف شما:
1. جستجوی اطلاعات به روز درباره فریمورک‌های AI Agent
2. جمع‌آوری آمار GitHub Stars، تاریخ انتشار، ویژگی‌ها
3. ارائه خروجی ساختاریافته با اعداد و ارقام دقیق

ابزارهای شما:
- search_web: برای جستجو
- calculate_growth: برای تحلیل رشد

پس از اتمام تحقیق، پیام خود را با "[RESEARCH_DONE]" پایان دهید.""",
    tools=[search_web, calculate_growth],
    reflect_on_tool_use=True
)

analyst = AssistantAgent(
    name="Analyst",
    model_client=model_client,
    system_message="""شما یک تحلیلگر داده هستید.

وظایف شما:
1. تحلیل داده‌های جمع‌آوری شده توسط Researcher
2. شناسایی روندها و الگوها
3. ایجاد جدول مقایسه با معیارهای مشخص
4. امتیازدهی به هر فریمورک (۱-۱۰)

پس از اتمام تحلیل، پیام خود را با "[ANALYSIS_DONE]" پایان دهید.""",
    tools=[calculate_growth],
    reflect_on_tool_use=True
)

writer = AssistantAgent(
    name="Writer",
    model_client=model_client,
    system_message="""شما یک نویسنده فنی مسلط به فارسی و انگلیسی هستید.

وظایف شما:
1. تبدیل تحلیل‌ها به یک گزارش روان و حرفه‌ای
2. استفاده از ترکیب فارسی و انگلیسی (اصطلاحات فنی به انگلیسی)
3. ایجاد خلاصه اجرایی (Executive Summary)
4. نتیجه‌گیری نهایی با توصیه‌های عملی

پس از نوشتن گزارش نهایی، پیام خود را با "FINAL_REPORT" پایان دهید.
این عبارت شرط پایان مکالمه است.""",
    reflect_on_tool_use=False
)

# --- شرط پایان ---
termination = TextMentionTermination("FINAL_REPORT")

# --- تیم گروه چت (RoundRobin برای پیش‌بینی‌پذیری بیشتر) ---
team = RoundRobinGroupChat(
    agents=[researcher, analyst, writer],
    termination_condition=termination,
    max_turns=10  # حداکثر ۱۰ دور
)

# --- اجرا ---
async def run_analysis():
    print("🚀 شروع تحلیل رقابتی بازار AI Agents با AutoGen")
    print("=" * 60)
    
    task = """
    یک تحلیل رقابتی از فریمورک‌های اصلی AI Agent انجام بده:
    - AutoGen, CrewAI, LangGraph, OpenAI Agents SDK
    - معیارها: GitHub Stars, تاریخ انتشار, Production Readiness, Learning Curve
    - خروجی نهایی: گزارش به صورت ترکیبی فارسی/انگلیسی با جداول مقایسه
    """
    
    result = await team.run(task=task)
    
    print("\n📋 گزارش نهایی:")
    print("-" * 40)
    for msg in result.messages:
        if msg.source == "Writer" and msg.content:
            print(msg.content)
    print("=" * 60)
    print(f"💰 مجموع توکن مصرفی: {sum(m.models_usage or 0 for m in result.messages if hasattr(m, 'models_usage'))}")

if __name__ == "__main__":
    asyncio.run(run_analysis())
```

### ۵.۳ پیاده‌سازی با CrewAI {#code-crewai}

```python
"""
CrewAI — تحلیل رقابتی بازار AI Agents
Three-agent system: Researcher → Analyst → Writer
با معماری نقش‌محور و Sequential Process
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# --- ابزارها (Tools) ---
@tool("Search Web")
def search_web(query: str) -> str:
    """جستجوی اینترنتی برای تحقیقات بازار"""
    return f"نتایج جستجو برای: {query}\n1. AutoGen 35K stars\n2. CrewAI 25K stars\n3. LangGraph 20K stars"

@tool("Calculate Growth")
def calculate_growth(data: str) -> str:
    """تحلیل نرخ رشد بازار"""
    return "نرخ رشد: ۴۵٪ سالانه در بازار AI Agents"

# --- تعریف عامل‌ها با نقش‌های مشخص ---
researcher = Agent(
    role="Senior Market Researcher",
    goal="جمع‌آوری دقیق‌ترین و به‌روزترین اطلاعات درباره فریمورک‌های AI Agent",
    backstory="""شما یک محقق بازار با ۱۰ سال سابقه در حوزه فناوری هستید.
    در شرکت‌های Gartner و Forrester کار کرده‌اید و به جمع‌آوری داده‌های دقیق معروفید.
    همیشه با چندین منبع صحت اطلاعات را تأیید می‌کنید.""",
    tools=[search_web, calculate_growth],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    llm="gpt-4o"
)

analyst = Agent(
    role="Data Analyst & Strategy Consultant",
    goal="تحلیل عمیق داده‌ها و استخراج insightهای قابل اجرا",
    backstory=""""شما یک تحلیلگر داده با مدرک PhD در علم داده از Stanford هستید.
    تخصص شما در تحلیل بازارهای فناوری و شناسایی الگوهای رشد است.
    خروجی شما همیشه شامل جداول مقایسه، نمودارهای تحلیلی و امتیازدهی عددی است.""",
    tools=[calculate_growth],
    verbose=True,
    allow_delegation=False,
    llm="gpt-4o"
)

writer = Agent(
    role="Technical Content Strategist",
    goal="تولید گزارش حرفه‌ای با سبک نگارش فارسی/انگلیسی",
    backstory="""شما یک استراتژیست محتوای فنی هستید که به دو زبان فارسی و انگلیسی مسلط است.
    مقالات شما در مجلات معتبری مانند MIT Technology Review منتشر شده است.
    تخصص شما در ساده‌سازی مفاهیم پیچیده فنی است.""",
    verbose=True,
    allow_delegation=False,
    llm="gpt-4o"
)

# --- تعریف وظایف با وابستگی صریح ---
research_task = Task(
    description="""یک تحقیق جامع درباره وضعیت فعلی فریمورک‌های AI Agent انجام بده.
    
    فریمورک‌های هدف: AutoGen, CrewAI, LangGraph, OpenAI Agents SDK
    
    اطلاعات مورد نیاز برای هر فریمورک:
    - تعداد ستاره‌های GitHub
    - شرکت توسعه‌دهنده
    - تاریخ انتشار اولین نسخه
    - معماری اصلی
    - آمادگی برای تولید (Production Readiness)
    
    از ابزار Search Web برای جستجو استفاده کن.""",
    expected_output="""یک گزارش ساختاریافته با جدول مقایسه شامل:
    - نام فریمورک | GitHub Stars | شرکت | معماری | Production Ready
    - حداقل ۵ منبع معتبر
    - آمار دقیق و به‌روز""",
    agent=researcher,
    output_file="autogen_crewai_research.md"
)

analysis_task = Task(
    description="""داده‌های جمع‌آوری شده توسط Researcher را تحلیل کن.
    
    موارد تحلیل:
    1. مقایسه GitHub Stars و روند رشد
    2. مقایسه معماری‌ها (مکالمه‌محور vs نقش‌محور vs گراف‌محور)
    3. امتیازدهی به هر فریمورک (۱-۱۰) در معیارهای:
       - سهولت استفاده
       - Production Readiness
       - انعطاف‌پذیری
       - هزینه
    
    خروجی باید شامل جدول امتیازات و تحلیل روندها باشد.""",
    expected_output="""یک گزارش تحلیلی شامل:
    - جدول امتیازات با ۴ معیار
    - تحلیل روندهای بازار
    - سه insight کلیدی
    - پیشنهاد برای بهترین فریمورک در سناریوهای مختلف""",
    agent=analyst,
    context=[research_task],  # وابستگی به task قبلی
    output_file="autogen_crewai_analysis.md"
)

writing_task = Task(
    description="""بر اساس تحقیق و تحلیل انجام شده، یک گزارش نهایی حرفه‌ای بنویس.
    
    ساختار گزارش:
    1. عنوان و تاریخ
    2. خلاصه اجرایی (Executive Summary) — ۳ پاراگراف
    3. جدول مقایسه اصلی
    4. تحلیل عمیق هر فریمورک (۳-۴ پاراگراف برای هر کدام)
    5. ماتریس تصمیم (چه زمانی از کدام استفاده کنیم)
    6. نتیجه‌گیری و توصیه‌ها
    
    سبک نگارش: ترکیبی از فارسی و انگلیسی
    - بدنه اصلی به فارسی
    - اصطلاحات فنی به انگلیسی در پرانتز
    - جداول به انگلیسی (برای خوانایی بین‌المللی)""",
    expected_output="""یک گزارش کامل حداقل ۱۰۰۰ کلمه‌ای شامل:
    - Executive Summary
    - Comparison Table
    - Deep Analysis (۴ فریمورک)
    - Decision Matrix
    - Final Recommendations""",
    agent=writer,
    context=[research_task, analysis_task],  # وابستگی به دو task قبلی
    output_file="autogen_crewai_final_report.md"
)

# --- تشکیل تیم ---
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # اجرای ترتیبی
    verbose=True,
    memory=True,
    planning=True,  # برنامه‌ریزی خودکار
    planning_llm="gpt-4o",
    output_log_file="crew_execution.log"
)

# --- اجرا ---
if __name__ == "__main__":
    print("🚀 شروع تحلیل رقابتی بازار AI Agents با CrewAI")
    print("=" * 60)
    
    result = crew.kickoff(inputs={
        "topic": "AI Agent Frameworks Comparison 2026"
    })
    
    print("\n📋 گزارش نهایی:")
    print("-" * 40)
    print(result.raw if hasattr(result, 'raw') else result)
    print("=" * 60)
    print(f"💰 جزئیات اجرا در فایل log ذخیره شد")
```

### ۵.۴ مقایسه کد خط به خط {#code-comparison}

| جنبه | AutoGen v0.4 | CrewAI |
|------|-------------|--------|
| **الگوی معماری** | مکالمه‌محور (Conversational) | نقش‌محور (Role-Based) |
| **API** | `async/await` — ناهمگام اجباری | Synchronous + Flows اختیاری |
| **تعریف عامل** | `AssistantAgent(name, system_message, model_client)` | `Agent(role, goal, backstory, llm)` |
| **ابزارها** | توابع `async` ساده + `tools=[]` | `@tool` دکوراتور + `tools=[]` |
| **زنجیره وظایف** | از طریق مکالمه در GroupChat | `Task(context=[...])` صریح |
| **مدیریت حالت** | تاریخچه مکالمه (Message History) | خروجی Taskها + Memory |
| **شرط پایان** | `TerminationCondition` صریح | اتمام همه Taskها |
| **کنترل جریان** | LLM تصمیم می‌گیرد (یا RoundRobin) | شما تصمیم می‌گیرید (Sequential) |
| **خطایابی** | دیباگ مکالمه سخت‌تر | خروجی هر Task مجزا |
| **هزینه پیش‌بینی** | غیرقابل پیش‌بینی (تعداد دور نامشخص) | قابل پیش‌بینی (تعداد Task مشخص) |
| **بازنویسی (Reflection)** | `reflect_on_tool_use=True` داخلی | از طریق Task اضافی یا حلقه |
| **ذخیره خروجی** | دستی | `output_file` خودکار |

**مشاهدات کلیدی:**

1. **CrewAI کد خواناتر و خودمستند (self-documenting) دارد** — `Agent(role="Researcher", goal="...")` گویاتر از `AssistantAgent(name="Researcher", system_message="...")` است
2. **AutoGen انعطاف بیشتری در جریان دارد** — عامل‌ها می‌توانند با هم تعامل داشته باشند، سوال بپرسند و برگردند
3. **CrewAI هزینه predictableتری دارد** — دقیقاً می‌دانید چند Task اجرا می‌شود
4. **AutoGen برای وظایف اکتشافی بهتر است** — جایی که نمی‌دانید دقیقاً چه مراحلی نیاز است
5. **CrewAI verbose.logging بهتری دارد** — خروجی کنسول بسیار آموزنده است

---

## ۶. ماتریس تصمیم — چه زمانی کدام را انتخاب کنیم؟ {#decision-matrix}

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│  ماتریس تصمیم AutoGen vs CrewAI                                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  آیا وظیفه شما نیاز به مکالمه پویا و اکتشاف دارد؟                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ ✅ بله → آیا نیاز به اجرای کد در سندباکس دارید؟                   │  │   │
│  │  │   ├── ✅ بله → **AutoGen** (بی‌رقب در code execution)            │  │   │
│  │  │   └── ❌ خیر → AutoGen (اگر هزینه مهم است CrewAI هم خوبه)         │  │   │
│  │  │                                                                  │  │   │
│  │  │ ❌ خیر → آیا تیم شما با نقش‌های مشخص کار می‌کند؟                   │  │   │
│  │  │   ├── ✅ بله → **CrewAI** (نقش‌محور طبیعی‌تر)                    │  │   │
│  │  │   └── ❌ خیر → AutoGen (برای جریان‌های نامشخص بهتر است)            │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  سوالات تکمیلی:                                                       │   │
│  │                                                                        │   │
│  │  آیا Production Readiness حیاتی است؟                                   │   │
│  │  ├── ✅ AutoGen (code execution, sandbox)                             │   │
│  │  └── ✅ CrewAI (stable, simple, good logging)                         │   │
│  │                                                                        │   │
│  │  آیا هزینه LLM مهم است؟                                               │   │
│  │  ├── ✅ CrewAI (پیش‌بینی‌پذیر، تعداد دور مشخص)                         │   │
│  │  └── ❌ AutoGen (ممکن است دورهای اضافی داشته باشد)                     │   │
│  │                                                                        │   │
│  │  آیا تیم شما تجربه async Python دارد؟                                 │   │
│  │  ├── ✅ AutoGen (اجباری async)                                        │   │
│  │  └── ❌ CrewAI (Synchronous ساده‌تر)                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### جدول تصمیم‌گیری

| سناریو | انتخاب پیشنهادی | دلیل |
|--------|----------------|------|
| **تحلیل کد و تولید کد** (Code Generation & Execution) | 🏆 **AutoGen** | Docker sandbox منحصربه‌فرد، اجرای امن کد |
| **تحقیق بازار و گزارش‌نویسی** (Research & Report) | 🏆 **CrewAI** | نقش‌های مشخص، خروجی task مجزا، logging عالی |
| **پشتیبانی مشتری چندمرحله‌ای** | ⚖️ هر دو مناسب | AutoGen برای مکالمه، CrewAI برای triage |
| **سیستم مکالمه‌ای اکتشافی** (Debate/Brainstorm) | 🏆 **AutoGen** | SelectorGroupChat پویا |
| **اتوماسیون فرآیند قطعی** (Pipeline) | 🏆 **CrewAI** | Sequential Process دقیق و قابل پیش‌بینی |
| **شروع سریع و MVP** | 🏆 **CrewAI** | ساده‌ترین API، مستندات خوب |
| **محصول در مقیاس Enterprise** | ⚖️ هر دو چالش دارند | هر دو نیاز به زیرساخت اضافی دارند |
| **Human-in-the-Loop** | 🏆 **AutoGen** | `human_input_mode` داخلی |
| **استفاده از ابزارهای LangChain** | 🏆 **CrewAI** | سازگاری بومی با LangChain tools |
| **پروژه تحقیقاتی (R&D)** | 🏆 **AutoGen** | انعطاف بیشتر برای آزمایش |
| **هزینه پایین و مقرون‌به‌صرفه** | 🏆 **CrewAI** | تعداد فراخوانی LLM کنترل‌شده |

---

## ۷. مقایسه آمادگی برای تولید (Production Readiness) {#production-readiness}

| معیار | AutoGen v0.4 | CrewAI |
|-------|-------------|--------|
| **ماندگاری (Persistence)** | ❌ داخلی ندارد (بايد خودتان پیاده کنید) | ⚠️ محدود (Memory داخلی، اما نه Database persistence) |
| **Streaming** | ✅ هم token هم message streaming | ❌ |
| **مشاهده‌پذیری (Observability)** | ✅ OpenTelemetry + Logging | ⚠️ Logging ساده کنسول |
| **Error Recovery** | ⚠️ CancellationToken + Retry | ⚠️ Retry ساده (تعداد محدود) |
| **Containerization/Sandbox** | ✅ Docker + ACA Dynamic Sessions | ❌ |
| **مدیریت حالت (State Management)** | ⚠️ تاریخچه مکالمه (محدود) | ⚠️ Memory داخلی (محدود برای production) |
| **نرخ (Rate Limiting)** | ❌ باید خودتان پیاده کنید | ✅ `max_rpm` داخلی |
| **مدیریت هزینه** | ❌ | ❌ |
| **Caching** | ⚠️ Client-side | ✅ داخلی (LLM + Tool cache) |
| **Security** | ✅ Sandbox code execution | ⚠️ امنیت در سطح API |
| **Auto-Scaling** | ❌ | ❌ |
| **مستندات** | ⚠️ متوسط (v0.4 docs در حال تکمیل) | ✅ خوب |
| **جمعیت کاربری** | ⭐ 35K+ Stars (جامعه بزرگ) | ⭐ 25K+ Stars (جامعه در حال رشد) |
| **ثبات API** | ⚠️ v0.4 API در حال تغییر | ✅ نسبتاً پایدار |
| **کلود/مدیریت‌شده** | ❌ (فقط کتابخانه) | ❌ (فقط کتابخانه) |

### تحلیل عمیق Production Readiness

#### AutoGen

**نقاط قوت:**
- **اجرای کد سندباکس** تنها فریمورکی است که Docker sandbox واقعی دارد
- **معماری v0.4** با OpenTelemetry برای production طراحی شده
- **CancellationToken** برای کنترل timeout و لغو اجرا
- **ACA Dynamic Sessions** برای اجرای کد در Azure (مقیاس Enterprise)

**نقاط ضعف:**
- **بدون persistence داخلی** — اگر سرور ری‌استارت شود، تاریخچه از بین می‌رود
- **API v0.4 جدید** و در حال تغییر — ممکن است مهاجرت‌های پرهزینه داشته باشید
- **مایکروسافت تمرکز را به Microsoft Agent Framework منتقل کرده** — AutoGen در حالت maintenance است
- **هزینه نامشخص** — تعداد دورهای مکالمه قابل پیش‌بینی نیست

#### CrewAI

**نقاط قوت:**
- **API ساده و پایدار** — تغییرات کم، مهاجرت آسان
- **Logging داخلی** — کنسول verbose بسیار مفید
- **Caching** — هم LLM cache و هم Tool cache
- **Rate Limiting** — `max_rpm` از production scenarioها پشتیبانی می‌کند

**نقاط ضعف:**
- **بدون persistence** — هیچ stateای ذخیره نمی‌شود
- **بدون streaming** — باید منتظر تمام خروجی بمانید
- **بدون sandbox** — کد را مستقیماً روی سیستم اجرا می‌کند (ریسک امنیتی)
- **بدون observability استاندارد** — OpenTelemetry پشتیبانی نمی‌شود

---

## ۸. موارد استفاده واقعی (Real-World Use Cases) {#real-world-cases}

### AutoGen در Production

#### 1. GitHub Copilot Extension — تحلیل و تولید کد

یک شرکت SaaS از AutoGen برای تحلیل خودکار issueها و تولید PR استفاده می‌کند. سه عامل:
- **IssueAnalyzer:** issue را می‌خواند و categorized می‌کند
- **CodeGenerator:** کد مورد نیاز را تولید می‌کند
- **CodeReviewer:** کد را بازبینی می‌کند

**چرا AutoGen:** نیاز به **اجرای کد در سندباکس** و **مکالمه بین عامل‌ها** برای رفع ابهامات.

#### 2. Chatbot پشتیبانی فنی با قابلیت اجرای دستورات

یک شرکت مخابراتی از AutoGen برای پشتیبانی مشتری استفاده می‌کند:
- عامل اصلی با مشتری صحبت می‌کند
- عامل اجرایی (UserProxyAgent) دستورات را روی سرورهای آزمایشی اجرا می‌کند
- عامل ناظر (Critic) خروجی را قبل از ارسال به مشتری بررسی می‌کند

**چرا AutoGen:** `UserProxyAgent` با `human_input_mode="NEVER"` و Docker sandbox.

#### 3. سیستم تحلیل رقابتی خودکار (مایکروسافت)

مایکروسافت خودش از AutoGen برای تحلیل رقبا استفاده می‌کند:
- عامل‌ها وب را می‌گردند، گزارش می‌گیرند، تحلیل می‌کنند و داشبورد می‌سازند
- GroupChat با RoundRobin برای گردش کار قطعی

**چرا AutoGen:** یکپارچگی با Azure OpenAI و ecosystem مایکروسافت.

### CrewAI در Production

#### 1. Content Marketing Pipeline

یک استارتاپ محتوا از CrewAI برای تولید خودکار محتوای وبلاگ استفاده می‌کند:
- **Researcher:** موضوع را تحقیق می‌کند
- **Strategist:** استراتژی محتوا را تعیین می‌کند
- **Writer:** مقاله را می‌نویسد
- **Editor:** ویرایش و بهینه‌سازی SEO می‌کند
- **Designer:** تصاویر و layout را پیشنهاد می‌دهد

**چرا CrewAI:** **نقش‌های مشخص** و **خروجی task مجزا** برای بازبینی انسانی.

#### 2. Automated Due Diligence (DD)

یک شرکت سرمایه‌گذاری از CrewAI برای بررسی شرکت‌های هدف استفاده می‌کند:
- **Financial Analyst:** صورت‌های مالی را تحلیل می‌کند
- **Market Researcher:** بازار و رقبا را بررسی می‌کند
- **Legal Reviewer:** قراردادها و مسائل قانونی را بررسی می‌کند
- **Risk Analyst:** ریسک‌ها را ارزیابی می‌کند
- **Manager:** همه را هماهنگ می‌کند (Hierarchical Process)

**چرا CrewAI:** **Hierarchical Process** با manager agent و **allow_delegation**.

#### 3. پلتفرم استخدام خودکار

یک پلتفرم HR از CrewAI برای بررسی رزومه استفاده می‌کند:
- **Screener:** رزومه‌ها را فیلتر می‌کند
- **Technical Interviewer:** سوالات فنی می‌سازد
- **Culture Fit Analyst:** تناسب فرهنگی را بررسی می‌کند
- **Report Generator:** گزارش نهایی را می‌سازد

**چرا CrewAI:** پردازش **موازی** (execution موازی taskها) و **خروجی ساختاریافته**.

---

## ۹. ارتباط با الگوهای HiveOS {#hiveos-connection}

### HiveOS به عنوان abstraction layer

HiveOS هر دو فریمورک را به عنوان **موتور اجرا (execution engine)** می‌بیند و خود را به عنوان لایه abstraction بالای آن‌ها تعریف می‌کند:

```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│  HiveOS + AutoGen / CrewAI                                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  HiveOS — لایه ارکستراسیون                                            │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │   │
│  │  │ Flow DSL   │ │  Domains   │ │  RBAC      │ │ StorageEngine    │  │   │
│  │  │ (YAML)     │ │ (دامنه‌ها) │ │ (دسترسی)   │ │ (حافظه)         │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Adapter Layer — تبدیل DSL به کد فریمورک                               │   │
│  │                                                                        │   │
│  │  ┌────────────────────┐      ┌────────────────────┐                   │   │
│  │  │  AutoGen Adapter   │      │  CrewAI Adapter    │                   │   │
│  │  │                    │      │                    │                   │   │
│  │  │ Flow DSL ──▶ AutoGen│      │ Flow DSL ──▶ CrewAI│                   │   │
│  │  │ GroupChat Code      │      │ Agent/Task Code   │                   │   │
│  │  └────────────────────┘      └────────────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Execution Engine (موتور اجرا)                                       │   │
│  │                                                                        │   │
│  │  ┌────────────────────┐      ┌────────────────────┐                   │   │
│  │  │  AutoGen Runtime   │      │  CrewAI Runtime     │                   │   │
│  │  │  (Async, Event)    │      │  (Sync + Flows)    │                   │   │
│  │  └────────────────────┘      └────────────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### الگوی پیشنهادی HiveOS برای انتخاب

| سناریوی HiveOS | فریمورک پیشنهادی | دلیل |
|----------------|-----------------|------|
| Flow نیاز به مکالمه پویا دارد | **AutoGen** | GroupChat + Selector |
| Flow نیاز به اجرای کد امن دارد | **AutoGen** | Docker sandbox |
| Flow شامل وظایف نقش‌محور است | **CrewAI** | Agent/Task مدل شفاف |
| کاربران نیاز به Persian-first دارند | **CrewAI** | `output_file` و گزارش readable |
| Flow ترکیبی از کد و تحلیل است | **هر دو + HiveOS** | Adapter انتخاب را推迟 می‌کند |

### چگونه HiveOS نقاط ضعف هر فریمورک را جبران می‌کند

| نقطه ضعف | فریمورک | راهکار HiveOS |
|-----------|---------|--------------|
| بدون persistence | هر دو | **StorageEngine** (SQLite) داخلی |
| بدون observability | هر دو | **Brain + Decision Tracer** |
| هزینه نامشخص | AutoGen | **Cost tracking** در Flow Engine |
| بدون caching | AutoGen | **Cache layer** در HiveOS |
| بدون RBAC | هر دو | **RBAC** داخلی HiveOS |
| DSL وابسته به زبان | هر دو | **Flow DSL** (YAML) مستقل از زبان |

---

## ۱۰. جمع‌بندی و توصیه نهایی {#conclusion}

### انتخاب بر اساس معماری

```
┌──────────────────────────────────────────────────────────────────┐
│  سوال: workflow شما چه شکلی است؟                                 │
│                                                                  │
│  مکالمه‌ای (Conversational)          قطعی (Deterministic)        │
│  ┌───────────────────────┐          ┌───────────────────────┐   │
│  │                       │          │                       │   │
│  │     AutoGen           │          │      CrewAI           │   │
│  │                       │          │                       │   │
│  │  • بحث و تبادل نظر    │          │  • خط مونتاژ          │   │
│  │  • اکتشافی            │          │  • نقش‌های مشخص       │   │
│  │  • کد محور            │          │  • تحلیل + گزارش     │   │
│  │  • هزینه بیشتر        │          │  • هزینه کمتر        │   │
│  │                       │          │                       │   │
│  └───────────────────────┘          └───────────────────────┘   │
│                                                                  │
│  انتخاب نهایی:                                                   │
│                                                                  │
│  ✅ اگر workflow شما شبیه جلسه طوفان فکری است → AutoGen          │
│  ✅ اگر workflow شما شبیل خط تولید است → CrewAI                  │
│  ✅ اگر به هر دو نیاز دارید → HiveOS + Adapter Pattern           │
└──────────────────────────────────────────────────────────────────┘
```

### توصیه‌های عملی

1. **برای شروع سریع (Rapid Prototyping):** CrewAI انتخاب بهتری است. در چند ساعت مولد می‌شوید و خروجی ملموس دارید.

2. **برای سیستم‌های کد-محور (Code-Centric Systems):** AutoGen با Docker sandbox تنها گزینه واقعی است. اگر عامل‌های شما کد تولید و اجرا می‌کنند، AutoGen انتخاب شماست.

3. **برای Production با منابع محدود:** CrewAI ساده‌تر و پایدارتر است. AutoGen v0.4 API هنوز در حال تثبیت است.

4. **برای پروژه‌های بلندمدت:** هر دو را با **Adapter Pattern** (الگوی HiveOS) جدا کنید. Flow DSL بنویسید و بتوانید بین فریمورک‌ها جابجا شوید.

5. **اگر تیم شما async Python بلد نیست:** CrewAI sync بسیار ساده‌تر است. AutoGen v0.4 اجباری async دارد.

6. **برای Human-in-the-Loop:** AutoGen با `human_input_mode` برتری محسوسی دارد.

7. **برای Observability:** هر دو ضعف دارند — HiveOS یا LangSmith را به عنوان لایه مشاهده‌پذیری اضافه کنید.

### خط پایانی (Bottom Line)

> **AutoGen** یک **چارچوب مکالمه‌ای (Conversational Framework)** است که در **اجرای کد و تعامل پویا** برتری دارد. برای تیم‌هایی که به دنبال انعطاف و قدرت هستند و آمادگی پذیرش هزینه بیشتر و API در حال تغییر را دارند.
>
> **CrewAI** یک **چارچوب تیمی (Team Framework)** است که در **سادگی، پیش‌بینی‌پذیری و نقش‌محوری** برتری دارد. برای تیم‌هایی که می‌خواهند سریع حرکت کنند و workflow مشخصی دارند.
>
> **HiveOS** از هر دو به عنوان موتور اجرا استفاده می‌کند و نقاط ضعف آن‌ها را با StorageEngine، RBAC، Brain Visualization و Flow DSL جبران می‌کند.

---

## پیوست: مسیرهای یادگیری (Learning Paths)

### AutoGen Learning Path

```
۱. یادگیری مفاهیم پایه (۱ روز)
   └── AgentChat API Tutorial
۲. ساخت اولین GroupChat (۲ روز)
   └── RoundRobin → SelectorGroupChat
۳. ابزارها و اجرای کد (۲ روز)
   └── Tools → Docker Sandbox
۴. الگوهای پیشرفته (۳ روز)
   └── Nested Chat → StateFlow → Swarm
۵. Production (۲ روز)
   └── OpenTelemetry → Persistence → Error Recovery
```

### CrewAI Learning Path

```
۱. یادگیری مفاهیم پایه (نیم روز)
   └── Agent, Task, Crew, Process
۲. ساخت اولین Crew (۱ روز)
   └── Sequential Process
۳. ابزارها (۱ روز)
   └── @tool → LangChain Tools → CrewAI Tools
۴. فرآیندهای پیشرفته (۲ روز)
   └── Hierarchical → Manager Agent → Delegation
۵. Flows و Production (۲ روز)
   └── Flows → Memory → Caching → Deployment
```

---

## منابع و مراجع (References)

- [AutoGen Documentation — Microsoft](https://microsoft.github.io/autogen/)
- [AutoGen GitHub](https://github.com/microsoft/autogen)
- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)
- [AutoGen v0.2 to v0.4 Migration Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/migration-guide.html)
- [CrewAI Flows Guide](https://docs.crewai.com/flows)
- [HiveOS Architecture](../02-Architecture/01-high-level-arch.md)
- [HiveOS Flow DSL](../02-Architecture/02-flow-dsl.md)
- [Microsoft Azure AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [AI Agent Framework Comparison — CallSphere](https://callsphere.ai/blog/ai-agent-framework-comparison-2026)

---

> **آخرین به‌روزرسانی:** ۲۰۲۶-۰۷-۱۶  
> **نویسنده:** تیم مستندات HiveOS  
> **مسیر فایل:** `docs/06-Research/agents/03-Frameworks/02-autogen-crewai.md`  
> **پیشنهاد مطالعه بعدی:** `03-openai-agents-sdk-deep-dive.md`

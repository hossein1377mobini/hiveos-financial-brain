# مقایسه فریمورک‌های AI Agent (LangGraph vs CrewAI vs AutoGen vs OpenAI Agents SDK)

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **منابع:** CallSphere 2026 Framework Comparison · Galileo AI Agent Frameworks Guide · Microsoft Azure AI Agent Design Patterns · HiveOS Architecture Docs  
> **نسخه:** v1.0

---

## فهرست مطالب (Table of Contents)

1. [چرا انتخاب فریمورک مهم است؟](#why-framework-choice-matters)
2. [معرفی چهار فریمورک اصلی](#framework-introductions)
3. [مقایسه معماری (Architecture Comparison)](#architecture-comparison)
4. [ماتریس مقایسه ویژگی‌ها (Feature Comparison Matrix)](#feature-comparison-matrix)
5. [مقایسه سهولت استفاده (Ease of Use)](#ease-of-use)
6. [مقایسه آمادگی برای تولید (Production Readiness)](#production-readiness)
7. [مقایسه عملکرد و هزینه (Performance & Cost)](#performance-and-cost)
8. [کدام فریمورک را انتخاب کنیم؟ (When to Choose Each)](#when-to-choose-each)
9. [الگوهای HiveOS در ارتباط با این فریمورک‌ها](#hiveos-patterns)
10. [نکات کلیدی (Key Takeaways)](#key-takeaways)

---

## ۱. چرا انتخاب فریمورک مهم است؟ {#why-framework-choice-matters}

ساخت **AI Agent** بدون فریمورک، مثل ساختن یک وب‌اپلیکیشن بدون فریمورک وب است — ممکن است، اما در نهایت مجبور می‌شوید همان الگوهایی را بازنویسی کنید که همه به آن نیاز دارند: **حلقه‌های اجرای ابزار (tool execution loops)**، **مدیریت حالت (state management)**، **مدیریت خطا (error handling)**، **مشاهده‌پذیری (observability)** و **هماهنگی چندعاملی (multi-agent coordination)**. فریمورک مناسب این کارهای تکراری (boilerplate) را حذف می‌کند و در عین حال **گاردریل‌هایی برای استقرار در محیط تولید (production deployment)** فراهم می‌آورد.

اما انتخاب فریمورک اشتباه، اصطکاک ایجاد می‌کند. فریمورکی که برای **عامل‌های مکالمه‌ای (conversational agents)** طراحی شده، وقتی به یک **workflow قطعی (deterministic workflow)** نیاز دارید با شما می‌جنگد. فریمورکی که برای **ابزارهای تک‌عاملی (single-agent tools)** ساخته شده، وقتی به **همکاری چندعاملی (multi-agent collaboration)** نیاز دارید شما را محدود می‌کند.

> **نکته کلیدی:** فریمورک درست مانند **مغز افزار** سیستم عامل‌های شماست — معماری آن تعیین می‌کند که چه الگوهایی ممکن، چه الگوهایی آسان، و چه الگوهایی غیرممکن هستند.

---

## ۲. معرفی چهار فریمورک اصلی {#framework-introductions}

### LangGraph (LangChain)

| ویژگی | توضیح |
|-------|-------|
| **توسعه‌دهنده** | LangChain Inc. |
| **معماری** | **Graph-Based State Machines** — ماشین حالت مبتنی بر گراف |
| **مخزن** | GitHub: 20K+ stars |
| **زبان اصلی** | Python (TypeScript نیز موجود) |
| **وضعیت** | Production-Ready ✅ |

**فلسفه معماری:** گردش کارها باید **صریح (explicit)**، **قابل مشاهده (visualizable)** و **قطعی (deterministic)** باشند. توسعه‌دهنده توپولوژی دقیق گراف را تعریف می‌کند؛ LLM درون آن ساختار تصمیم می‌گیرد.

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal

class AgentState(TypedDict):
    input: str
    classification: str
    response: str

def classify_request(state: AgentState) -> dict:
    # LLM call to classify
    return {"classification": "technical"}

def process_request(state: AgentState) -> dict:
    # Process based on classification
    return {"response": f"Processed: {state['input']}"}

def human_review(state: AgentState) -> dict:
    # Human-in-the-loop approval
    return state

def route_by_type(state: AgentState) -> Literal["process", "review"]:
    if state["classification"] == "sensitive":
        return "review"
    return "process"

# Build graph
graph = StateGraph(AgentState)
graph.add_node("classify", classify_request)
graph.add_node("process", process_request)
graph.add_node("review", human_review)
graph.add_conditional_edges("classify", route_by_type)
graph.add_edge("review", "process")
graph.add_edge("process", END)

# Compile with checkpointing
app = graph.compile(checkpointer=PostgresSaver(...))

# Run
result = app.invoke({"input": "Help! My order is late"})
```

---

### CrewAI

| ویژگی | توضیح |
|-------|-------|
| **توسعه‌دهنده** | CrewAI Inc. |
| **معماری** | **Role-Based Agent Teams** — تیم‌های عاملی مبتنی بر نقش |
| **مخزن** | GitHub: 25K+ stars |
| **زبان اصلی** | Python |
| **وضعیت** | Production-Ready (Growing Maturity) ✅ |

**فلسفه معماری:** وظایف پیچیده را **عامل‌های تخصصی (specialized agents)** که در قالب یک تیم کار می‌کنند بهتر حل می‌کنند — مانند یک تیم انسانی با نقش‌های مشخص.

```python
from crewai import Agent, Task, Crew, Process

# تعریف عامل‌ها مثل اعضای تیم
researcher = Agent(
    role="Researcher",
    goal="پیدا کردن آخرین تحقیقات درباره AI agents",
    backstory="محققی کنجکاو با ۱۰ سال سابقه در حوزه هوش مصنوعی",
    tools=[search_tool, arxiv_tool],
    verbose=True
)

analyst = Agent(
    role="Analyst",
    goal="تحلیل یافته‌ها و استخراج الگوها",
    backstory="تحلیل‌گر داده با تخصص در استخراج insight",
    tools=[data_analysis_tool],
    verbose=True
)

writer = Agent(
    role="Writer",
    goal="تولید گزارش نهایی به زبان فارسی",
    backstory="نویسنده فنی مسلط به فارسی و انگلیسی",
    verbose=True
)

# تعریف وظایف
task1 = Task(
    description="تحقیق درباره آخرین فریمورک‌های AI agent در سال ۲۰۲۶",
    agent=researcher,
    expected_output="لیست ۵ فریمورک برتر با جزئیات"
)

task2 = Task(
    description="تحلیل داده‌های جمع‌آوری شده توسط researcher",
    agent=analyst,
    context=[task1],
    expected_output="گزارش تحلیلی با جداول مقایسه"
)

task3 = Task(
    description="نوشتن مقاله نهایی به فارسی",
    agent=writer,
    context=[task1, task2],
    expected_output="مقاله کامل به زبان فارسی"
)

# تشکیل تیم
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[task1, task2, task3],
    process=Process.sequential,  # یا Process.hierarchical
    verbose=True
)

# اجرا
result = crew.kickoff()
```

---

### AutoGen (Microsoft)

| ویژگی | توضیح |
|-------|-------|
| **توسعه‌دهنده** | Microsoft Research |
| **معماری** | **Conversational Multi-Agent** — عامل‌های مکالمه‌ای چندگانه |
| **مخزن** | GitHub: 35K+ stars (بیشترین ستاره) |
| **زبان اصلی** | Python |
| **وضعیت** | Production-Ready (نسخه ۰.۴ / AG2 بازنویسی اساسی) ✅ |

**فلسفه معماری:** همکاری عامل‌ها از **مکالمه طبیعی (natural conversation)** نشأت می‌گیرد. بگذارید عامل‌ها با هم حرف بزنند و workflow خودبه‌خود شکل می‌گیرد.

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# تنظیمات LLM
config = {
    "config_list": [
        {"model": "gpt-4o", "api_key": "..."},
        {"model": "gpt-4o-mini", "api_key": "..."}
    ],
    "temperature": 0.7
}

# تعریف عامل‌ها
assistant = AssistantAgent(
    name="Assistant",
    system_message="شما یک دستیار هوشمند هستید.",
    llm_config=config
)

executor = UserProxyAgent(
    name="Executor",
    code_execution_config={
        "use_docker": True,
        "work_dir": "coding"
    },
    human_input_mode="NEVER"
)

critic = AssistantAgent(
    name="Critic",
    system_message="شما یک منتقد هستید. خروجی‌ها را بررسی کنید.",
    llm_config=config
)

# گروه چت
group_chat = GroupChat(
    agents=[assistant, executor, critic],
    messages=[],
    max_round=10,
    speaker_selection_method="auto"  # یا "round_robin" یا "random"
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=config
)

# شروع مکالمه
result = executor.initiate_chat(
    manager,
    message="یک تحلیل از داده‌های فروش انجام بده"
)
```

---

### OpenAI Agents SDK

| ویژگی | توضیح |
|-------|-------|
| **توسعه‌دهنده** | OpenAI |
| **معماری** | **Primitive-Based Composition** — ترکیب بر اساس primitives |
| **مخزن** | GitHub (جدیدترین فریمورک) |
| **زبان اصلی** | Python |
| **وضعیت** | Production-Ready (ساده اما محدود) ✅ |

**فلسفه معماری:** فریمورک را **مینیمال** نگه دارید. چهار primitive اصلی — **Agentها**، **Toolها**، **Handoffها** و **Guardrailها** — برای بیشتر موارد کافی هستند.

```python
from agents import Agent, Runner, function_tool, guardrail
from agents.guardrails import InputGuardrail

# تعریف ابزار
@function_tool
def get_order_status(order_id: str) -> dict:
    """بررسی وضعیت سفارش بر اساس شماره پیگیری"""
    # فراخوانی API واقعی
    return {
        "order_id": order_id,
        "status": "shipped",
        "estimated_delivery": "2026-07-18"
    }

@function_tool
def cancel_order(order_id: str) -> dict:
    """لغو سفارش"""
    return {"order_id": order_id, "status": "cancelled"}

# تعریف عامل‌های تخصصی
billing_agent = Agent(
    name="Billing Agent",
    instructions="شما متخصص امور مالی و صورتحساب هستید.",
    tools=[get_order_status]
)

tech_agent = Agent(
    name="Technical Support",
    instructions="شما متخصص پشتیبانی فنی هستید.",
    tools=[diagnostic_tool]
)

# گاردریل امنیتی
def safety_check(ctx, messages):
    for msg in messages:
        if "توهین" in msg.get("content", ""):
            return {"block": True, "reason": "محتوای نامناسب"}
    return {"block": False}

# عامل اصلی با handoff
main_agent = Agent(
    name="Support",
    instructions="شما یک دستیار پشتیبانی مشتری هستید. ابتدا مشکل را تشخیص بده، سپس به عامل مناسب ارجاع بده.",
    tools=[get_order_status, cancel_order],
    handoffs=[billing_agent, tech_agent],
    input_guardrails=[InputGuardrail(safety_check)]
)

# اجرا
result = Runner.run_sync(
    main_agent,
    messages=[{"role": "user", "content": "سفارش من دیر شده، راهنمایی کن"}]
)

print(result.final_output)
```

---

## ۳. مقایسه معماری (Architecture Comparison) {#architecture-comparison}

### نمای کلی معماری

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LangGraph                                       │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐                        │
│  │Input │──▶│Classify│──▶│Process│──▶│Review│──▶│End│              │
│  └──────┘   └──┬───┘   └──────┘   └──────┘                        │
│                │                                                   │
│                └─────(شرطی)─────▶ Human Review                      │
│  حالت (State) به صورت TypedDict در کل گراف جریان دارد              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     CrewAI                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                    │
│  │Researcher│────▶│ Analyst  │────▶│  Writer  │───▶ خروجی          │
│  └──────────┘     └──────────┘     └──────────┘                    │
│  هر عامل نقش (Role)، هدف (Goal) و پیشینه (Backstory) دارد         │
│  اجرا: ترتیبی (Sequential) یا سلسله‌مراتبی (Hierarchical)           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     AutoGen                                         │
│  ┌──────────┐                                                      │
│  │Assistant │◀────────────────────────────────────┐                │
│  └────┬─────┘                                      │                │
│       │مکالمه                                      │                │
│  ┌────▼─────┐     ┌──────────┐                      │                │
│  │ Executor │     │  Critic  │────(GroupChat)───────┘                │
│  └──────────┘     └──────────┘                                      │
│  همه چیز از طریق تبادل پیام (message passing) انجام می‌شود          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     OpenAI Agents SDK                               │
│  ┌──────────────┐                                                   │
│  │  Main Agent  │─────(Handoff)─────▶ Billing Agent                │
│  │  (Orch.)     │─────(Handoff)─────▶ Technical Agent              │
│  └──────┬───────┘                                                   │
│         │                                                           │
│    ابزارهای معمولی                                                  │
│  [Order Status] [Cancel] [Diagnose]                                 │
│  معماری ساده: Agent + Tools + Handoffs + Guardrails                │
└─────────────────────────────────────────────────────────────────────┘
```

### جدول مقایسه معماری

| معیار | LangGraph | CrewAI | AutoGen | OpenAI SDK |
|-------|-----------|--------|---------|------------|
| **الگوی معماری** | ماشین حالت گرافی (Graph State Machine) | تیم‌های نقش‌محور | مکالمه‌محور (Conversational) | ترکیب primitives |
| **نحوه تعریف جریان** | YAML یا Python (گره‌ها و یال‌ها) | عامل + وظیفه + فرآیند | پیام‌رسانی بین عامل‌ها | Agent + Tool + Handoff |
| **کنترل جریان** | دستی و صریح (گراف دقیق) | ترتیبی / سلسله‌مراتبی | پویا (مشخص شدن مرحله بعد توسط LLM) | دستی (از طریق handoff) |
| **مدیریت حالت (State)** | TypedDict صریح — جریان از طریق reducer | خروجی وظایف (ضمنی) | تاریخچه مکالمه | تاریخچه مکالمه |
| **شاخه‌بندی شرطی** | ✅ بومی (conditional edges) | ❌ محدود | ⚠️ از طریق منطق مکالمه | ⚠️ محدود (handoff ساده) |
| **حلقه (Loop)** | ✅ بومی (چرخه در گراف) | ❌ | ✅ از طریق مکالمه | ❌ |
| **اجرای موازی** | ✅ Fan-out/Fan-in بومی | فقط سلسله‌مراتبی | گروه چت | عامل به عنوان ابزار |

---

## ۴. ماتریس مقایسه ویژگی‌ها (Feature Comparison Matrix) {#feature-comparison-matrix}

| ویژگی | LangGraph | CrewAI | AutoGen | OpenAI SDK |
|-------|-----------|--------|---------|------------|
| **مدیریت حالت (State Management)** | ✅ Explicit TypedDict + Reducer | ⚠️ Implicit (task outputs) | ⚠️ تاریخچه مکالمه | ⚠️ تاریخچه مکالمه |
| **چندعاملی (Multi-Agent)** | ✅ از طریق گره‌های گراف | ✅ بومی (Crew) | ✅ بومی (GroupChat) | ⚠️ از طریق Handoff |
| **Human-in-the-Loop** | ✅ interrupt_before/after | ⚠️ Callback دستی | ✅ human_input_mode | ⚠️ Custom guardrails |
| **اجرای کد (Code Execution)** | ⚠️ یکپارچه‌سازی دستی | ❌ داخلی ندارد | ✅ Sandbox Docker | ❌ داخلی ندارد |
| **ماندگاری (Persistence)** | ✅ PostgreSQL / Redis / SQLite | ❌ داخلی ندارد | ❌ داخلی ندارد | ❌ داخلی ندارد |
| **Streaming** | ✅ Token + State streaming | ❌ | ✅ Token streaming | ✅ Token streaming |
| **مشاهده‌پذیری (Observability)** | ✅ LangSmith | ⚠️ Logging ساده | ✅ Cost tracking | ✅ Built-in tracing |
| **استقلال از مدل (Model Agnostic)** | ✅ هر مدل LangChain | ✅ هر LLM | ✅ فرمت OpenAI | ❌ فقط OpenAI* |
| **اجرای موازی** | ✅ Fan-out/Fan-in بومی | ⚠️ محدود | ⚠️ Group chat | ⚠️ Agent-as-tool |
| **گاردریل (Guardrails)** | ✅ سفارشی (از طریق گره) | ❌ داخلی ندارد | ❌ داخلی ندارد | ✅ بومی input/output |
| **خروجی ساختاریافته** | ✅ از طریق LangChain | ✅ از طریق task output | ⚠️ Parse دستی | ✅ بومی output_type |
| **ابزارهای از پیش ساخته** | ✅ صدها ابزار LangChain | ✅ CrewAI Tools | ⚠️ محدود | ❌ حداقل |
| **بازیابی از خطا (Error Recovery)** | ✅ Checkpoint + Retry | ⚠️ Retry ساده | ⚠️ محدود | ⚠️ Retry ساده |
| **مستندات** | ✅ عالی | ✅ خوب | ⚠️ متوسط | ✅ خوب |
| **تعداد ستاره GitHub** | ~20K+ | ~25K+ | ~35K+ | جدید |

---

## ۵. مقایسه سهولت استفاده (Ease of Use) {#ease-of-use}

### منحنی یادگیری (Learning Curve)

```
دشوار  ▲
       │
       │                    🟢 LangGraph
       │                 (گراف، state، reducer)
       │
       │              🔵 AutoGen (مکالمه‌ای،
       │              اما دیباگ پیچیده)
       │
       │           🟡 OpenAI SDK (ساده ولی
       │           محدود برای سناریوهای پیچیده)
       │
       │        🟢 CrewAI (ساده‌ترین — ساعتی مولد)
       │
       └───────────────────────────────────────────▶ آسان
```

**LangGraph** — شیب‌دارترین منحنی یادگیری. باید با **ماشین حالت (state machine)**، **TypedDict**، **Reducer**، **یال‌های شرطی (conditional edges)** و **الگوی compile/invoke** آشنا شوید. پاداش آن **حداکثر کنترل** است. معمولاً ۲-۳ روز طول می‌کشد تا مولد شوید.

**CrewAI** — ساده‌ترین فریمورک برای یادگیری. عامل‌ها را با توضیحات زبان طبیعی تعریف کنید، وظایف را ایجاد کنید و اجرا نمایید. اکثر توسعه‌دهندگان در **چند ساعت** مولد می‌شوند. بهای این سادگی: وقتی به رفتاری خارج از الگوهای CrewAI نیاز دارید، راه فراری وجود ندارد.

**AutoGen** — برای مکالمات دو عاملی ساده، یادگیری متوسطی دارد اما با **انتخاب speaker در GroupChat** و **مکالمات تو در تو (nested)** به سرعت پیچیده می‌شود. پارادایم مکالمه‌ای بصری (intuitive) است اما دیباگ کردن گفتگوهای چندعاملی چالش‌برانگیز است.

**OpenAI Agents SDK** — شروع آسان (ساده‌تر از LangGraph) اما برای سیستم‌های پیچیده نیاز به معماری دقیق دارد. مکانیزم handoff ساده است اما انعطاف LangGraph را در مسیریابی پیچیده ندارد.

---

## ۶. مقایسه آمادگی برای تولید (Production Readiness) {#production-readiness}

### LangGraph: Production-Grade ✅

LangGraph **آماده‌ترین فریمورک برای محیط تولید** است:
- ✅ **ماندگاری بومی (Native Persistence):** PostgreSQL, Redis, SQLite
- ✅ **Streaming داخلی:** هم token هم state
- ✅ **مشاهده‌پذیری:** LangSmith — رهگیری کامل اجرا
- ✅ **Checkpointing:** بازیابی از crash، restart workflowهای طولانی
- ✅ **LangGraph Cloud:** استقرار مدیریت‌شده با auto-scaling
- ✅ **بازیابی خطا:** exponential backoff با jitter

```python
# نمونه Persistence در LangGraph
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(
    "postgresql://user:pass@host/db"
)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)

# اجرا با قابلیت بازیابی
result = app.invoke(
    {"input": "Process order 12345"},
    config={"configurable": {"thread_id": "order-12345"}}
)

# بازیابی از نقطه شکست
state = app.get_state({"configurable": {"thread_id": "order-12345"}})
app.update_state({"configurable": {"thread_id": "order-12345"}}, {...})
```

### CrewAI: Growing Maturity ⚠️

CrewAI سریع بهبود یافته اما همچنان کمبودهایی دارد:
- ❌ **عدم persistence داخلی** — مناسب برای batch processing
- ❌ **عدم streaming**
- ❌ **مشاهده‌پذیری محدود**
- ✅ **CrewAI Enterprise** برخی قابلیت‌های تولید را اضافه می‌کند
- ✅ مناسب برای **پردازش دسته‌ای (batch)** و **تولید گزارش**

### AutoGen: Research to Production Gap ⚠️

AutoGen ریشه در **تحقیقات آکادمیک** دارد:
- ✅ اجرای کد قوی (Docker sandbox)
- ❌ عدم persistence داخلی
- ⚠️ انتخاب speaker در GroupChat گاهی غیرقابل پیش‌بینی
- ✅ **نسخه ۰.۴ (AG2)** بازنویسی اساسی به سمت آمادگی تولید
- ⚠️ نیاز به تنظیمات اضافی برای production

### OpenAI Agents SDK: Simple but Limited ⚠️

SDK برای آنچه انجام می‌دهد قابل اعتماد است — زیرساخت OpenAI کار سنگین را انجام می‌دهد:
- ❌ عدم persistence
- ❌ عدم orchestration پیشرفته
- ❌ عدم ابزارهای استقرار
- ✅ **Guardrails** با کیفیت تولید
- ✅ **Tracing** قوی
- ⚠️ برای سیستم‌های ساده عالی، برای پیچیده نیاز به تکمیل دستی

---

## ۷. مقایسه عملکرد و هزینه (Performance & Cost) {#performance-and-cost}

```python
# برآورد تعداد فراخوانی LLM به ازای هر تعامل کاربر (typical support agent)

# LangGraph: 1-3 فراخوانی LLM (مسیریابی قطعی، حداقل فراخوانی)
# هزینه: $0.01-0.03 به ازای هر تعامل

# CrewAI: 3-5 فراخوانی LLM (هر عامل حداقل یک بار فراخوانی می‌شود)
# هزینه: $0.03-0.08 به ازای هر تعامل

# AutoGen: 4-10 فراخوانی LLM (مکالمات رفت و برگشتی)
# هزینه: $0.04-0.15 به ازای هر تعامل

# OpenAI SDK: 1-3 فراخوانی LLM + 2 فراخوانی کوچک برای guardrail
# هزینه: $0.02-0.05 به ازای هر تعامل
```

| فریمورک | تعداد فراخوانی LLM | هزینه تخمینی | علت |
|---------|-------------------|-------------|------|
| **LangGraph** | ۱-۳ | $0.01-0.03 | مسیریابی قطعی، کمترین فراخوانی |
| **CrewAI** | ۳-۵ | $0.03-0.08 | هر عامل حداقل یک فراخوانی |
| **AutoGen** | ۴-۱۰ | $0.04-0.15 | مکالمات رفت و برگشتی |
| **OpenAI SDK** | ۱-۳ + guardrail | $0.02-0.05 | مشابه LangGraph + گاردریل |

> **نکته:** LangGraph و OpenAI SDK **مقرون‌به‌صرفه‌ترین** هستند چون فراخوانی‌های غیرضروری LLM را به حداقل می‌رسانند. CrewAI به دلیل رویکرد نقش‌محور، هر عامل حداقل یک فراخوانی دارد. AutoGen به دلیل مدل مکالمه‌ای می‌تواند به تبادلات طولانی منجر شود.

---

## ۸. کدام فریمورک را انتخاب کنیم؟ (When to Choose Each) {#when-to-choose-each}

### LangGraph را انتخاب کنید وقتی:
- ✅ نیاز به **workflowهای قطعی و پیچیده** با شاخه‌بندی و حلقه دارید
- ✅ **قابلیت اطمینان تولید** برای شما حیاتی است (persistence، observability)
- ✅ تیم شما می‌تواند زمان یادگیری پارادایم گراف را سرمایه‌گذاری کند
- ✅ به **workflowهای طولانی** نیاز دارید که از restart فرآیند جان سالم به در ببرند
- ✅ به **Human-in-the-Loop** قوی نیاز دارید (interrupt، approval gate)

### CrewAI را انتخاب کنید وقتی:
- ✅ وظیفه شما به طور طبیعی به **نقش‌ها** تقسیم می‌شود (تحقیق، تحلیل، نوشتن)
- ✅ می‌خواهید **سریع‌ترین زمان نمونه‌سازی (time-to-prototype)** را داشته باشید
- ✅ workflow شما **پردازش دسته‌ای (batch)** است، نه تعامل real-time کاربر
- ✅ تیم شما **سادگی را بر انعطاف** ترجیح می‌دهد
- ✅ نیاز به **تیم‌های عاملی با نقش‌های مشخص** دارید

### AutoGen را انتخاب کنید وقتی:
- ✅ **تولید و اجرای کد** هسته اصلی کار شماست
- ✅ نیاز دارید عامل‌ها به صورت **تکراری (iteratively)** کد بنویسند، خطا بگیرند و بهبود دهند
- ✅ workflow شما **اکتشافی (exploratory)** است — مراحل از قبل مشخص نیستند
- ✅ در حال ساخت **عامل‌های تحلیل داده** یا **مهندسی نرم‌افزار** هستید
- ✅ در اکوسیستم Microsoft و Azure فعالیت می‌کنید

### OpenAI Agents SDK را انتخاب کنید وقتی:
- ✅ قبلاً به **اکوسیستم OpenAI** متعهد شده‌اید
- ✅ به یک فریمورک **سبک (lightweight)** با **گاردریل داخلی** نیاز دارید
- ✅ نیازهای چندعاملی شما ساده است (الگوی triage و handoff)
- ✅ می‌خواهید **حداقل overhead فریمورک** و **حداکثر قابلیت مدل** را داشته باشید
- ✅ در حال ساختن **MVP یا نمونه اولیه** هستید

### درخت تصمیم (Decision Tree)

```
آیا workflow شما قطعی و قابل پیش‌بینی است؟
├── ✅ بله
│   ├── آیا persistence و production readiness حیاتی است؟
│   │   ├── ✅ بله → LangGraph
│   │   └── ❌ خیر → OpenAI Agents SDK (اگر ساده است)
│   │
├── ❌ خیر (اکتشافی/مکالمه‌ای)
│   ├── آیا تولید کد هسته کار شماست؟
│   │   ├── ✅ بله → AutoGen
│   │   └── ❌ خیر
│   │       ├── آیا نقش‌های مشخصی دارید؟
│   │       │   ├── ✅ بله → CrewAI
│   │       │   └── ❌ خیر → AutoGen یا OpenAI SDK
│   │
└── ترکیبی از هر دو
    └── LangGraph برای orchestration اصلی + CrewAI/AutoGen برای زیروظایف
```

---

## ۹. الگوهای HiveOS در ارتباط با این فریمورک‌ها {#hiveos-patterns}

### HiveOS در یک نگاه

**HiveOS** یک **سیستم عامل چندعاملی (Multi-Agent Operating System)** است که خود را به عنوان لایه orchestration بالای عامل‌ها تعریف می‌کند — نه یک فریمورک عامل جدید. معماری HiveOS از ترکیب بهترین الگوهای فریمورک‌های فوق بهره می‌برد:

```
┌──────────────────────────────────────────────────────────────┐
│                         🧠 BRAIN                            │
│              3D Neural Visualization — Glass Box            │
├──────────────────────────────────────────────────────────────┤
│                         🎮 PLAYGROUND                       │
│          Visual Flow Builder — Drag, Drop, Configure        │
├──────────────────────────────────────────────────────────────┤
│                         🔧 ENGINE                           │
│  CLI • Flow Engine • Mothership • RBAC • Audit • Workspace  │
├──────────────────────────────────────────────────────────────┤
│                         🧩 DOMAINS                          │
│           Accounting (D1) • Medical • Legal • ...           │
└──────────────────────────────────────────────────────────────┘
```

### HiveOS از چه الگوهایی از هر فریمورک الهام گرفته است؟

#### ۱. تأثیر LangGraph — گراف محور (Graph-Based)

HiveOS از **گراف وابستگی (Dependency Graph)** برای تعریف جریان کار (Flow) استفاده می‌کند — درست مثل LangGraph:

```yaml
# Flow DSL در HiveOS — الهام گرفته از LangGraph
name: "پایان‌نامه حسابداری ماهانه"
agents:
  - id: data_collector
    skills: [accounting-data-extraction]
    output: raw_data.json

  - id: reconciler
    depends_on: [data_collector]
    skills: [accounting-reconciliation]
    input_from:
      agent: data_collector
      files: [raw_data.json]
    output: reconciled.json

  - id: auditor
    depends_on: [reconciler]
    skills: [accounting-audit]
    action:
      require_approval: true  # Human-in-the-loop مثل LangGraph
```

**شباهت‌ها:**
- هر دو از **گراف صریح (explicit graph)** استفاده می‌کنند
- هر دو **مسیریابی بر اساس وابستگی** را پشتیبانی می‌کنند
- هر دو **Human-in-the-Loop** دارند
- هر دو **State Management** قوی دارند

**تفاوت‌ها:**
- LangGraph گراف را درコード Python تعریف می‌کند؛ HiveOS از **YAML Flow DSL** استفاده می‌کند
- HiveOS **دامنه‌محور (Domain-Based)** است — عامل‌ها دانش دامنه را از domain plugin می‌گیرند
- HiveOS روی **قابلیت حمل (portability)** تمرکز دارد — flows قابل اشتراک‌گذاری و نصب هستند

#### ۲. تأثیر CrewAI — نقش‌محور (Role-Based)

HiveOS از ایده **نقش‌های تخصصی (specialized roles)** CrewAI استفاده می‌کند، اما از طریق **دامنه‌ها (Domains)**:

```
CrewAI:                     HiveOS:
Agent(role="Accountant")    domain: accounting
Agent(role="Auditor")       domain: auditing  
Agent(role="Analyst")       domain: analytics
```

در HiveOS، هر domain یک مجموعه از **blueprintهای عامل** و **flowهای از پیش ساخته** است — شبیه به agent templates در CrewAI اما با قابلیت نصب و اشتراک‌گذاری از طریق **Domain Registry**.

#### ۳. تأثیر AutoGen — مکالمه‌ای

HiveOS از **Communication Bus** برای ارتباط بین عامل‌ها استفاده می‌کند که مفهومی مشابه **message passing** AutoGen دارد. اما در HiveOS، ارتباط از طریق **Protocolهای استاندارد (MCP و A2A)** انجام می‌شود — نه گفتگوی آزاد LLM.

#### ۴. تأثیر OpenAI Agents SDK — سادگی و ابزارها

HiveOS ایده **primitiveهای ساده** OpenAI SDK را در طراحی ابزارها و handoffها به کار گرفته، اما آن را با **Flow Engine** و **لایه orchestration** تکمیل می‌کند.

### موقعیت HiveOS در مقایسه با فریمورک‌ها

| بعد | LangGraph | CrewAI | AutoGen | OpenAI SDK | **HiveOS** |
|-----|-----------|--------|---------|------------|------------|
| **معماری** | Graph State Machine | Role-Based Teams | Conversational | Primitive-Based | **Graph + Domain-Based** |
| **تعریف جریان** | Python Graph | YAML + Python | Python Code | Python Code | **YAML Flow DSL** |
| **دامنه (Domain)** | ❌ | ❌ | ❌ | ❌ | **✅ بومی (Domain Plugin)** |
| **Persistence** | ✅ PostgreSQL | ❌ | ❌ | ❌ | **✅ SQLite (StorageEngine)** |
| **Human-in-Loop** | ✅ interrupt | ⚠️ محدود | ✅ محدود | ⚠️ محدود | **✅ Approval Gate Engine** |
| **مشاهده‌پذیری** | ✅ LangSmith | ⚠️ محدود | ⚠️ محدود | ✅ Tracing | **✅ Brain + Decision Tracer** |
| **نصب و اشتراک** | ❌ | ❌ | ❌ | ❌ | **✅ Package Registry** |
| **چندمستأجری** | ❌ | ❌ | ❌ | ❌ | **✅ Workspace (Multi-tenant)** |
| **مدیریت دسترسی** | ❌ | ❌ | ❌ | ❌ | **✅ RBAC** |

### مزایای منحصربه‌فرد HiveOS

1. **Domain-Native Architecture:** عامل‌ها دانش خود را از **دامنه‌های نصب‌شدنی (installable domains)** می‌گیرند — نه از پرامپت‌های سخت‌کد شده
2. **Flow DSL:** جریان‌های کاری به صورت **YAML قابل حمل** تعریف می‌شوند — بر خلاف کد Python خاص هر فریمورک
3. **Glass Box Principle:** همه چیز قابل مشاهده است — **Brain** 3D visualization، **Decision Tracer**، **Approval Gates**
4. **StorageEngine:** persistence داخلی با SQLite — بدون نیاز به دیتابیس خارجی
5. **Ecosystem Packaging:** flows و domainها قابل بسته‌بندی (tar.gz)، اشتراک‌گذاری و نصب هستند
6. **Hermes Runtime:** هر عامل روی Hermes Agent runtime اجرا می‌شود — از توانایی‌های Hermes (skills، tools، memory) استفاده می‌کند

---

## ۱۰. نکات کلیدی (Key Takeaways) {#key-takeaways}

> 📌 **خلاصه‌ای برای تصمیم‌گیرندگان فنی**

| # | نکته کلیدی | توضیح |
|---|------------|-------|
| ۱ | **LangGraph برای Production** | اگر به persistence، reliability و observability در مقیاس نیاز دارید، LangGraph گزینه اول است. بالاترین هزینه یادگیری اما بالاترین بازده در بلندمدت. |
| ۲ | **CrewAI برای Prototyping سریع** | اگر می‌خواهید در چند ساعت یک نمونه کار کنید و workflow شما ساده است، CrewAI بهترین انتخاب است. برای production به زیرساخت اضافی نیاز دارد. |
| ۳ | **AutoGen برای Code-Centric** | اگر هسته کار شما تولید و اجرای کد توسط agentهاست، AutoGen با Docker sandbox بی‌رقب است. |
| ۴ | **OpenAI SDK برای MVPهای ساده** | اگر در اکوسیستم OpenAI هستید و نیازهای ساده دارید، این SDK بهترین است. برای پیچیدگی‌های بیشتر به LangGraph مهاجرت کنید. |
| ۵ | **ترکیب فریمورک‌ها ممکن است** | LangGraph برای orchestration اصلی + CrewAI/AutoGen برای زیروظایف — یک الگوی رایج و مؤثر. |
| ۶ | **هزینه را جدی بگیرید** | CrewAI و AutoGen به دلیل فراخوانی‌های بیشتر LLM، هزینه بالاتری دارند. LangGraph و OpenAI SDK مقرون‌به‌صرفه‌تر هستند. |
| ۷ | **HiveOS مسیر متفاوتی دارد** | HiveOS یک **سیستم عامل چندعاملی** است، نه یک فریمورک عامل. روی **دامنه‌محوری، قابلیت حمل، و مشاهده‌پذیری** تمرکز دارد و می‌تواند در کنار هر یک از این فریمورک‌ها کار کند. |
| ۸ | **ابسترکشن کلید مهاجرت است** | ابزارهای خود را به صورت **تابع‌های خالص (plain functions)** تعریف کنید تا بتوانید بین فریمورک‌ها جابجا شوید. |
| ۹ | **فریمورک درست را زود انتخاب کنید** | مهاجرت بین فریمورک‌ها هزینه‌بر است. با یک PoC ساده در هر فریمورک شروع کنید (۱-۲ روز) و سپس تصمیم نهایی را بگیرید. |
| ۱۰ | **Human-in-the-Loop را فراموش نکنید** | در محیط تولید، همیشه یک مسیر برای دخالت انسان در تصمیمات حیاتی داشته باشید. LangGraph و HiveOS在这方面 قوی‌ترین هستند. |

### توصیه نهایی

هیچ فریمورکی برای همه موارد «بهترین» نیست. انتخاب باید بر اساس:

1. **ماهیت workflow شما** (قطعی ↔ اکتشافی)
2. **نیازهای production** (persistence, observability, scale)
3. **تخصص تیم شما** (آشنایی با graph, Python, OpenAI)
4. **بودجه** (هزینه فراخوانی LLM)
5. **اکوسیستم فعلی** (Azure, OpenAI, LangChain)

انجام شود.

> **توصیه HiveOS:** اگر از صفر شروع می‌کنید و می‌خواهید در بلندمدت انعطاف داشته باشید، با **LangGraph** شروع کنید. اگر نیاز به نمونه‌سازی سریع دارید، **CrewAI**. و اگر به دنبال یک پلتفرم جامع برای orchestration عامل‌ها با قابلیت domain-native هستید، به **HiveOS** نگاهی بیندازید.

---

## پیوست: الگوهای Orchestration از Microsoft Azure

مایکروسافت در [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) پنج الگوی اصلی برای orchestration معرفی می‌کند که هر چهار فریمورک و HiveOS از ترکیبی از آن‌ها استفاده می‌کنند:

| الگو | توضیح | LangGraph | CrewAI | AutoGen | OpenAI SDK | HiveOS |
|------|-------|-----------|--------|---------|------------|--------|
| **Sequential** | زنجیره خطی عامل‌ها | ✅ | ✅ Sequential | ⚠️ | ✅ | ✅ Flow DSL |
| **Concurrent** | اجرای موازی (fan-out/fan-in) | ✅ Fan-out/Fan-in | ❌ | ⚠️ GroupChat | ⚠️ | ✅ (از طریق وابستگی) |
| **Group Chat** | گفتگوی گروهی | ❌ | ❌ | ✅ بومی | ❌ | ⚠️ (از طریق Bus) |
| **Handoff** | واگذاری به عامل تخصصی | ✅ (از طریق گره) | ✅ (از طریق نقش) | ✅ (از طریق پیام) | ✅ بومی | ✅ (از طریق Flow) |
| **Magentic** | هماهنگی پویا (peer-to-peer) | ⚠️ | ❌ | ✅ | ❌ | ⚠️ (آینده) |

> **منبع:** [Microsoft Azure AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) — جولای ۲۰۲۶

---

## منابع و مراجع (References)

- [AI Agent Framework Comparison 2026 — CallSphere](https://callsphere.ai/blog/ai-agent-framework-comparison-2026)
- [7 Agent-to-Agent Interaction Frameworks — Galileo AI](https://galileo.ai/blog/7-agent-to-agent-interaction-frameworks)
- [AI Agent Orchestration Patterns — Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [HiveOS Architecture — مستندات داخلی](../02-Architecture/01-high-level-arch.md)
- [HiveOS Flow DSL — مستندات داخلی](../02-Architecture/02-flow-dsl.md)

---

> **آخرین به‌روزرسانی:** ۲۰۲۶-۰۷-۱۶  
> **مسیر فایل:** `docs/06-Research/agents/03-Frameworks/01-agent-frameworks-overview.md`

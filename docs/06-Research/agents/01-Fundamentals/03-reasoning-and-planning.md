# الگوهای استدلال و برنامه‌ریزی در عامل‌های هوش مصنوعی — Reasoning & Planning Patterns in AI Agents

> **منبع:** برگرفته و بومی‌سازی‌شده از مقالات arXiv «ReAct: Synergizing Reasoning and Acting in Language Models» (Yao et al., 2023)، «Plan-and-Solve Prompting» (Wang et al., 2023)، «ReWOO: Reasoning WithOut Observation» (Xu et al., 2023)، و مستندات IBM ReAct Agent

---

## ۱. مقدمه: چرا استدلال و برنامه‌ریزی برای عامل‌ها حیاتی است؟

یک عامل هوش مصنوعی (AI Agent) برای عملکرد مؤثر در دنیای واقعی به بیش از یک مدل زبانی بزرگ (LLM) نیاز دارد. مدل زبانی به تنهایی می‌تواند متن تولید کند، اما برای **اقدام در جهان خارج** — فراخوانی API، جستجوی پایگاه داده، اجرای کد، تعامل با ابزارها — به ساختاری نیاز دارد که استدلال (Reasoning) را به اقدام (Action) متصل کند.

دو الگوی اصلی برای این اتصال وجود دارند:

| الگو | ایدهٔ اصلی | مناسب برای |
|------|-----------|-----------|
| **ReAct (Reasoning + Acting)** | حلقهٔ فکر → اقدام → مشاهده به صورت تکراری | وظایف پویا و غیرقابل پیش‌بینی |
| **Plan-and-Execute** | ابتدا برنامه‌ریزی کامل، سپس اجرای گام‌به‌گام | وظایف با مراحل مشخص و قابل پیش‌بینی |
| **Function Calling** | فراخوانی مستقیم تابع بر اساس تشخیص مدل | وظایف ساده و تک‌مرحله‌ای |

در این مستند، هر سه الگو را با جزئیات فنی، دیاگرام، نمونه کد، و نحوهٔ نگاشت به معماری HiveOS بررسی می‌کنیم.

---

## ۲. الگوی ReAct — Reasoning + Acting

### ۲.۱ الهام از انسان

الگوی **ReAct** اولین بار در سال ۲۰۲۳ توسط Yao و همکاران در مقالهٔ «ReAct: Synergizing Reasoning and Acting in Language Models» معرفی شد. ایدهٔ اصلی از نحوهٔ استدلال انسان الهام گرفته شده است:

> انسان برای انجام یک کار پیچیده، به صورت طبیعی بین **فکر کردن (Thinking)** و **عمل کردن (Acting)** تناوب ایجاد می‌کند.

برای مثال، هنگام بستن چمدان برای سفر:
1. **فکر:** «آب‌وهوای مقصد چطور است؟»
2. **اقدام:** بررسی پیش‌بینی آب‌وهوا
3. **مشاهده:** «سرد است»
4. **فکر:** «چه لباس گرمی دارم؟»
5. **اقدام:** چک کردن کمد
6. **مشاهده:** «همه لباس‌های گرم در انبار هستند»
7. **فکر:** «پس باید لایه‌لایه بپوشم»

ReAct این فرایند طبیعی را به صورت یک **حلقهٔ ساختاریافته (structured loop)** در می‌آورد که LLM می‌تواند در آن استدلال (Thought)، اقدام (Action)، و مشاهده (Observation) را به صورت متناوب انجام دهد.

### ۲.۲ حلقهٔ اصلی ReAct (Thought → Action → Observation Loop)

```text
┌─────────────────────────────────────────────────────┐
│                 ReAct Loop                           │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    │
│  │  Thought  │───▶│  Action  │───▶│Observation │    │
│  │ (استدلال) │    │ (اقدام)  │    │ (مشاهده)   │    │
│  └──────────┘    └──────────┘    └────────────┘    │
│        ▲                                            │
│        │          ┌──────────────────────┐          │
│        └──────────│ پاسخ نهایی (Final)   │          │
│                   │ یا ادامهٔ حلقه       │          │
│                   └──────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

سه گام اصلی حلقه:

1. **Thought (فکر):** مدل وضعیت فعلی را تحلیل می‌کند، گام بعدی را برنامه‌ریزی می‌کند، و تصمیم می‌گیرد چه اقدامی لازم است. این همان **Chain-of-Thought Reasoning** است — مدل با صدای بلند فکر می‌کند.

2. **Action (اقدام):** مدل یک اقدام مشخص انجام می‌دهد — معمولاً فراخوانی یک ابزار (Tool Call) یا API. اقدام می‌تواند جستجوی وب، پرس‌وجوی پایگاه داده، اجرای کد، یا هر عملیات قابل تعریف دیگری باشد.

3. **Observation (مشاهده):** نتیجهٔ اقدام به مدل بازگردانده می‌شود. این مشاهده می‌تواند دادهٔ جدید، پیام خطا، یا تأیید موفقیت باشد.

### ۲.۳ ReAct Prompting — پرامپت نویسی برای حلقهٔ ReAct

برای اینکه LLM بتواند در حلقهٔ ReAct عمل کند، باید با یک **پرامپت سیستم (System Prompt)** خاص هدایت شود. معروف‌ترین نمونه، پرامپت `ZERO_SHOT_REACT_DESCRIPTION` در LangChain است:

```text
Answer the following questions as best you can. You have access to the following tools:

{tool_descriptions}

Use the following format:

Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
```

**مؤلفه‌های کلیدی این پرامپت:**

| مؤلفه | توضیح |
|-------|-------|
| **تعریف ابزارها** | لیست ابزارهای قابل استفاده با توضیحات |
| **فرمت خروجی** | قالب ثابت Thought/Action/Observation |
| **شرط پایان** | دستور تکرار حلقه تا رسیدن به پاسخ نهایی |
| **Scratchpad** | فضایی برای ذخیرهٔ تاریخچهٔ استدلال |

### ۲.۴ مثال عملی از اجرای ReAct

فرض کنید کاربر می‌پرسد: «دمای هوای تهران امروز چقدر است؟»

```text
User: دمای هوای تهران امروز چقدر است؟

Thought: کاربر دمای هوای تهران را می‌خواهد. من باید اطلاعات آب‌وهوای امروز را پیدا کنم. می‌توانم از ابزار جستجوی آب‌وهوا استفاده کنم.

Action: weather_search
Action Input: {"city": "Tehran", "date": "today"}

Observation: {"temperature": "38°C", "condition": "آفتابی", "humidity": "15%"}

Thought: اطلاعات آب‌وهوا را دریافت کردم. دمای امروز تهران ۳۸ درجه سانتی‌گراد است. می‌توانم پاسخ نهایی را بدهم.

Final Answer: دمای هوای امروز تهران ۳۸ درجه سانتی‌گراد و هوا آفتابی است. رطوبت ۱۵٪.

```

### ۲.۵ پیاده‌سازی ReAct در کد (LangGraph)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import json

# --- تعریف state ---
class AgentState(TypedDict):
    messages: List[str]
    next_action: str

# --- تعریف ابزارها ---
def weather_search(city: str) -> str:
    """جستجوی آب‌وهوا برای یک شهر"""
    return json.dumps({"temperature": "38°C", "condition": "آفتابی"})

def web_search(query: str) -> str:
    """جستجوی عمومی در وب"""
    return f"نتایج جستجو برای: {query}"

# --- نود استدلال (Reasoning Node) ---
def reasoning_node(state: AgentState):
    """نودی که LLM را صدا می‌زند و تصمیم می‌گیرد下一步 چیست"""
    # در عمل اینجا LLM صدا زده می‌شود
    prompt = f"""با توجه به تاریخچه، تصمیم بگیر اقدام بعدی چیست:
    تاریخچه: {state['messages']}
    اگر به پاسخ نهایی رسیده‌ای، "final" برگردان،
    در غیر این صورت نام ابزار و ورودی را برگردان."""
    
    # شبیه‌سازی خروجی LLM
    if "weather" in str(state['messages']):
        return {"next_action": "final", "messages": state['messages'] + ["پاسخ: ۳۸ درجه"]}
    return {"next_action": "weather_search", "messages": state['messages']}

# --- نود اجرا (Action Node) ---
def action_node(state: AgentState):
    """نودی که ابزار مشخص‌شده را اجرا می‌کند"""
    action = state['next_action']
    if action == "weather_search":
        result = weather_search("Tehran")
    elif action == "web_search":
        result = web_search(state['messages'][-1])
    else:
        result = "اقدام نامشخص"
    
    observation = f"نتیجهٔ {action}: {result}"
    return {"messages": state['messages'] + [observation]}

# --- ساخت گراف ---
graph = StateGraph(AgentState)

graph.add_node("reason", reasoning_node)
graph.add_node("act", action_node)

graph.set_entry_point("reason")

# یال شرطی: اگر final بود برو به END، در غیر این صورت به act
graph.add_conditional_edges(
    "reason",
    lambda s: "act" if s['next_action'] != "final" else "end",
    {"act": "act", "end": END}
)

graph.add_edge("act", "reason")

app = graph.compile()
```

> **نکته:** در پیاده‌سازی واقعی، نود `reason` یک LLM واقعی (مثلاً GPT-4 یا Claude) را با پرامپت ReAct صدا می‌زند. کد بالا صرفاً ساختار را نشان می‌دهد.

---

## ۳. Function Calling — فراخوانی تابع

### ۳.۱ تعریف

**Function Calling** (که با نام **Tool Use** نیز شناخته می‌شود) قابلیتی است که توسط OpenAI در ژوئن ۲۰۲۳ معرفی شد. در این الگو، مدل زبانی مستقیماً تشخیص می‌دهد که **کی** و **با چه آرگومان‌هایی** یک تابع را فراخوانی کند. خروجی مدل یک شیء JSON ساختاریافته است، نه یک رشتهٔ متنی آزاد.

### ۳.۲ تفاوت با ReAct

| ویژگی | Function Calling | ReAct |
|-------|-----------------|-------|
| **خروجی** | JSON ساختاریافته | متن آزاد با قالب مشخص |
| **چند مرحله** | تک‌مرحله‌ای (یک تابع) | چندمرحله‌ای (حلقه) |
| **استدلال** | حداقل (بدون CoT صریح) | حداکثر (CoT در هر گام) |
| **انعطاف‌پذیری** | کم — الگوی ثابت | زیاد — تطبیق پویا |
| **هزینه (Token)** | کم | زیاد (به دلیل CoT) |
| **سرعت** | بالا | پایین‌تر |

### ۳.۳ نحوهٔ کار Function Calling

```python
import openai

# تعریف تابع برای مدل
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "دریافت دمای هوای یک شهر",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "نام شهر"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "دمای تهران چقدر است؟"}],
    tools=tools
)

# مدل تصمیم می‌گیرد تابع را فراخوانی کند
tool_call = response.choices[0].message.tool_calls[0]
# tool_call.function.name = "get_weather"
# tool_call.function.arguments = '{"city": "Tehran"}'

# اجرای واقعی تابع در سمت برنامه
weather_data = get_weather(**json.loads(tool_call.function.arguments))

# ارسال نتیجه به مدل برای پاسخ نهایی
response2 = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "دمای تهران چقدر است؟"},
        response.choices[0].message,
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(weather_data)
        }
    ]
)
```

### ۳.۴ مزایا و محدودیت‌های Function Calling

**مزایا:**
- ⚡ **سرعت بالا:** بدون سربار استدلال اضافی
- 💰 **هزینهٔ کمتر:** تعداد token کمتر نسبت به ReAct
- 🔧 **سادگی پیاده‌سازی:** فقط یک فراخوانی API
- ✅ **خروجی قابل پیش‌بینی:** JSON ساختاریافته

**محدودیت‌ها:**
- 🔒 **انعطاف‌ناپذیری:** مدل مسیر از پیش تعیین‌شده‌ای دارد
- 🧠 **عدم استدلال عمیق:** قابلیت تصمیم‌گیری پویا محدود است
- 🔄 **عدم پشتیبانی از حلقه:** برای وظایف چندمرحله‌ای مناسب نیست

### ۳.۵ چه زمانی از Function Calling استفاده کنیم؟

| موقعیت | انتخاب مناسب |
|--------|-------------|
| **یک سؤال ساده با یک ابزار** (مثلاً‌: وضعیت آب‌وهوا) | ✅ Function Calling |
| **چند ابزار مستقل** (مثلاً: گرفتن قیمت سهام و نرخ ارز) | ✅ Function Calling |
| **زنجیره‌ای از ابزارها با وابستگی** (مثلاً: جستجوی مقاله، سپس تحلیل آن) | ❌ ReAct یا Plan-and-Execute |
| **تصمیم‌گیری پویا بر اساس نتایج میانی** | ❌ ReAct |
| **لاگ و توضیح‌پذیری بالا** | ❌ ReAct |

---

## ۴. Tool Use — استفاده از ابزار

### ۴.۱ ابزارها در معماری عامل

**ابزار (Tool)** هر قابلیت قابل فراخوانی است که عامل می‌تواند از آن استفاده کند. ابزارها پل ارتباطی بین LLM و جهان خارج هستند.

**انواع ابزارها:**

| نوع ابزار | مثال |
|-----------|------|
| **جستجو (Search)** | Google Search, Bing, Semantic Scholar |
| **پایگاه داده (Database)** | PostgreSQL, Redis, Vector DB |
| **API خارجی** | GitHub API, Slack API, Stripe API |
| **اجرای کد (Code Execution)** | Python REPL, Sandbox |
| **سیستم فایل (Filesystem)** | خواندن/نوشتن فایل |
| **کامپیوتر (Computer Use)** | کنترل مرورگر، کلیک، تایپ |

### ۴.۲ ثبت ابزار (Tool Registration)

در هر فریم‌ورک عاملی، ابزارها باید با یک **اسکیما (Schema)** مشخص ثبت شوند:

```python
# LangChain / LangGraph
from langchain.tools import tool

@tool
def get_stock_price(symbol: str) -> dict:
    """دریافت قیمت روز سهام یک نماد بورسی
    
    Args:
        symbol: نماد بورسی (مثلاً: AAPL, TSLA)
    Returns:
        قیمت و اطلاعات مرتبط
    """
    return {"symbol": symbol, "price": 185.50, "change": "+2.3%"}


# اسکیما به صورت خودکار از type hints استخراج می‌شود
print(get_stock_price.args_schema.schema())
# {
#   "type": "object",
#   "properties": {
#     "symbol": {
#       "type": "string",
#       "description": "نماد بورسی (مثلاً: AAPL, TSLA)"
#     }
#   },
#   "required": ["symbol"]
# }
```

### ۴.۳ ابزارها و MCP (Model Context Protocol)

**MCP** پروتکلی است که ارتباط عامل‌ها با ابزارها را استاندارد می‌کند. هر ابزار از طریق یک **MCP Server** در دسترس عامل قرار می‌گیرد:

```text
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│   AI Agent   │────▶│  MCP Client  │────▶│  MCP Server    │
│  (LLM + Loop)│     │  (در عامل)   │     │  (ابزارها)     │
└──────────────┘     └──────────────┘     └────────────────┘
                                                   │
                                           ┌───────┴───────┐
                                           │               │
                                     ┌─────────┐   ┌──────────┐
                                     │Search   │   │Database  │
                                     │API      │   │Query     │
                                     └─────────┘   └──────────┘
```

مزایای MCP برای ابزارها:
- **استانداردسازی:** همهٔ ابزارها یک رابط یکسان دارند
- **قابلیت کشف (Discoverability):** عامل می‌تواند ابزارهای موجود را کشف کند
- **امنیت:** دسترسی با رعایت خط‌مشی (Policy) کنترل می‌شود

---

## ۵. الگوی Plan-and-Execute — برنامه‌ریزی و اجرا

### ۵.۱ مفهوم

الگوی **Plan-and-Execute** رویکردی است که در آن عامل ابتدا یک **برنامهٔ کامل (Full Plan)** از تمام گام‌های لازم تهیه می‌کند و سپس آن را اجرا می‌نماید. این الگو در مقابل ReAct قرار می‌گیرد که در آن برنامه‌ریزی و اجرا به صورت گام‌به‌گام و درهم‌تنیده انجام می‌شود.

مبنای این الگو مقالهٔ «Plan-and-Solve Prompting» (Wang et al., 2023) و پروژهٔ **BabyAGI** (Yohei Nakajima) است.

### ۵.۲ دیاگرام Plan-and-Execute

```text
┌────────────────────────────────────────────────────────────┐
│                   Plan-and-Execute Agent                    │
│                                                            │
│  ┌──────────────┐                                          │
│  │    Planner   │  LLM بزرگ: برنامه‌ریزی استراتژیک           │
│  │  (برنامه‌ریز) │  دریافت هدف → تولید لیست گام‌ها            │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Plan List (لیست گام‌ها)                           │      │
│  │  1. جستجوی پیش‌بینی آب‌وهوای تهران                  │      │
│  │  2. استخراج دمای امروز از نتایج                     │      │
│  │  3. تبدیل به واحد سلسیوس                           │      │
│  │  4. تولید پاسخ نهایی شامل توصیهٔ لباس               │      │
│  └──────────────────────────────────────────────────┘      │
│         │                                                   │
│         ▼ (اجرای گام‌به‌گام)                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Step 1      │───▶│  Step 2      │───▶│  Step 3      │  │
│  │  (ابزار A)   │    │  (ابزار B)   │    │  (LLM کوچک)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │    Solver   │  ترکیب نتایج و تولید پاسخ نهایی            │
│  │  (حل‌کننده)  │                                          │
│  └──────────────┘                                          │
└────────────────────────────────────────────────────────────┘
```

### ۵.۳ مقایسهٔ ReAct با Plan-and-Execute

| معیار | ReAct | Plan-and-Execute |
|-------|-------|------------------|
| **رویکرد** | استدلال و اقدام در هم | جداسازی برنامه‌ریزی از اجرا |
| **تعداد فراخوانی LLM بزرگ** | یک بار در هر گام | فقط در مرحلهٔ برنامه‌ریزی |
| **سرعت** | کندتر (LLM در هر گام) | سریع‌تر (اجرای بدون LLM) |
| **هزینه** | بیشتر | کمتر |
| **انعطاف‌پذیری** | بالا (تطبیق پویا) | متوسط (برنامهٔ ثابت) |
| **شفافیت** | متوسط (استدلال ضمنی) | بالا (برنامهٔ صریح) |
| **بهترین برای** | وظایف اکتشافی و پویا | وظایف با مراحل قابل پیش‌بینی |

### ۵.۴ انواع Plan-and-Execute

#### ۵.۴.۱ Plan-and-Execute پایه

ساده‌ترین شکل: Planner یک لیست خطی از گام‌ها تولید می‌کند و Worker آن‌ها را یکی‌یکی اجرا می‌کند.

```python
# شبه‌کد LangGraph برای Plan-and-Execute
from langgraph.graph import StateGraph

class PlanState(TypedDict):
    plan: List[str]
    current_step: int
    results: Dict[str, Any]
    final_answer: str

def planner_node(state: PlanState):
    """LLM بزرگ برنامه را می‌نویسد"""
    plan = llm.invoke(f"برای پرسش '{state['query']}' یک برنامه گام‌به‌گام بنویس")
    return {"plan": parse_steps(plan)}

def worker_node(state: PlanState):
    """گام بعدی را اجرا می‌کند (بدون LLM یا با LLM کوچک)"""
    step = state['plan'][state['current_step']]
    result = execute_step(step)  # فراخوانی ابزار
    return {
        "results": {**state['results'], step: result},
        "current_step": state['current_step'] + 1
    }
```

#### ۵.۴.۲ ReWOO — Reasoning WithOut Observation

مقالهٔ **ReWOO** (Xu et al., 2023) یک پیشرفت بر Plan-and-Execute است که امکان **ارجاع به نتایج گام‌های قبلی** را با متغیر فراهم می‌کند.

```text
Plan: باید بدانم چه تیم‌هایی در سوپربول امسال حضور دارند
E1: Search[چه تیم‌هایی در سوپربول ۲۰۲۶ حضور دارند؟]
Plan: باید بدانم کوارتربک هر تیم کیست
E2: LLM[کوارتربک تیم اول از #E1]
Plan: باید بدانم کوارتربک تیم دوم کیست
E3: LLM[کوارتربک تیم دوم از #E1]
Plan: باید آمار اولین کوارتربک را پیدا کنم
E4: Search[آمار #E2 در این فصل]
Plan: باید آمار دومین کوارتربک را پیدا کنم
E5: Search[آمار #E3 در این فصل]
```

در اینجا `#E1` به نتیجهٔ گام اول اشاره دارد. این مکانیسم اجازه می‌دهد Worker بدون نیاز به LLM، وابستگی‌ها را مدیریت کند.

#### ۵.۴.۳ LLMCompiler

**LLMCompiler** اجرای موازی گام‌های مستقل را با استفاده از **DAG (Directed Acyclic Graph)** امکان‌پذیر می‌کند:

```text
              ┌──────────┐
              │  Planner  │
              └────┬─────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ جستجوی A │ │ جستجوی B │ │  LLM C   │  (گام‌های مستقل = موازی)
└──────────┘ └──────────┘ └──────────┘
      │            │            │
      └─────┬──────┴──────┬────┘
            ▼             ▼
      ┌──────────┐  ┌──────────┐
      | ترکیب D  |  | تحلیل E  |   (گام‌های وابسته = ترتیبی)
      └──────────┘  └──────────┘
            │             │
            └──────┬──────┘
                   ▼
            ┌──────────┐
            │  Solver  │
            └──────────┘
```

---

## ۶. مقایسهٔ جامع الگوها

| ویژگی | Function Calling | ReAct | Plan-and-Execute |
|-------|-----------------|-------|------------------|
| **تعداد دفعات LLM** | ۱–۲ | n (تعداد گام‌ها) | ۱ (برنامه‌ریزی) + n (اجرا) |
| **استدلال (Reasoning)** | ❌ خیر | ✅ CoT در هر گام | ✅ برنامه‌ریزی صریح |
| **تطبیق‌پذیری (Adaptability)** | ❌ کم | ✅ زیاد | ⚠️ متوسط |
| **شفافیت (Explainability)** | ❌ کم | ✅ زیاد | ✅ زیاد |
| **سرعت** | ⚡ بالا | 🐢 پایین | ⚡ متوسط |
| **هزینه** | 💰 کم | 💰💰 زیاد | 💰 متوسط |
| **پشتیبانی از ابزارهای متعدد** | ⚠️ محدود | ✅ کامل | ✅ کامل |
| **پیچیدگی پیاده‌سازی** | 🔧 ساده | 🏗️ متوسط | 🏗️ متوسط |
| **مدیریت خطای پویا** | ❌ ضعیف | ✅ قوی | ⚠️ متوسط |

### ۶.۱ راهنمای انتخاب الگو

```text
آیا وظیفه فقط یک فراخوانی ابزار ساده است؟
├── ✅ بله → Function Calling
└── ❌ خیر
    ├── آیا گام‌ها از قبل قابل پیش‌بینی هستند؟
    │   ├── ✅ بله → Plan-and-Execute
    │   └── ❌ خیر
    │       └── آیا نیاز به تطبیق پویا با نتایج میانی داریم؟
    │           ├── ✅ بله → ReAct
    │           └── ❌ خیر → Plan-and-Execute (با بازبرنامه‌ریزی)
```

---

## ۷. نگاشت الگوها به فریم‌ورک‌های عاملی (Agent Frameworks)

### ۷.۱ LangGraph

LangGraph از شرکت LangChain، محبوب‌ترین فریم‌ورک برای پیاده‌سازی الگوهای استدلال است:

| الگو | پشتیبانی در LangGraph |
|------|----------------------|
| **ReAct** | ✅ ماژول `create_react_agent` (پیش‌ساخته) |
| **Function Calling** | ✅ از طریق LangChain tools |
| **Plan-and-Execute** | ✅ notebook رسمی در مخزن LangGraph |
| **ReWOO** | ✅ notebook رسمی |
| **LLMCompiler** | ✅ پشتیبانی از DAG |

```python
# LangGraph: استفاده از ReAct Agent پیش‌ساخته
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[search_tool, weather_tool, calculator_tool],
    prompt="شما یک دستیار هوشمند هستید...",
    max_iterations=10  # حداکثر تعداد حلقه
)

result = agent.invoke({"messages": [{"role": "user", "content": "دمای تهران چقدر است؟"}]})
```

### ۷.۲ CrewAI

CrewAI رویکرد **نقش‌محور (Role-Based)** دارد. در این فریم‌ورک، هر عامل یک نقش مشخص دارد و الگوی استدلال به صورت پیش‌فرض ساده‌تر است:

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="محقق آب‌وهوا",
    goal="جستجوی دقیق اطلاعات آب‌وهوا",
    backstory="متخصص هواشناسی با دسترسی به ابزارهای جستجو",
    tools=[weather_search],
    allow_delegation=False
)

analyzer = Agent(
    role="تحلیل‌گر",
    goal="تحلیل داده‌های آب‌وهوا و ارائه توصیه",
    backstory="تحلیل‌گر داده با توانایی استدلال",
    tools=[],
    allow_delegation=True  # می‌تواند به Researcher واگذار کند
)
```

CrewAI از **حالت ترتیبی (Sequential Process)** و **حالت سلسله‌مراتبی (Hierarchical Process)** پشتیبانی می‌کند که دومی شبیه Plan-and-Execute با یک مدیر (Manager) است.

### ۷.۳ AutoGen (Microsoft)

AutoGen رویکرد **گفتگومحور (Conversational)** دارد:

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent(
    name="assistant",
    system_message="شما یک عامل ReAct هستید. ابتدا فکر کنید، سپس اقدام کنید.",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": "..."}]}
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",  # یا "ALWAYS" برای human-in-the-loop
    code_execution_config={"use_docker": False}
)

# AutoGen به طور طبیعی از حلقهٔ ReAct پشتیبانی می‌کند
# چون AssistantAgent هر بار استدلال می‌کند و UserProxyAgent ابزارها را اجرا می‌کند
user_proxy.initiate_chat(assistant, message="دمای تهران امروز چقدر است؟")
```

### ۷.۴ OpenAI Agents SDK

OpenAI Agents SDK از چهار مؤلفهٔ اصلی تشکیل شده: **Agent**, **Tool**, **Handoff**, **Guardrail**.

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """دریافت دمای هوای یک شهر"""
    return f"دمای {city} امروز ۳۸ درجه سانتی‌گراد است."

agent = Agent(
    name="WeatherAssistant",
    instructions="شما یک دستیار آب‌وهوا هستید. از ابزار get_weather استفاده کن.",
    tools=[get_weather],
    handoffs=[],  # برای چندعاملی
    input_guardrails=[],  # برای امنیت
)

result = Runner.run_sync(agent, input="دمای تهران امروز چقدر است؟")
```

---

## ۸. نگاشت به HiveOS — HiveOS Mapping

### ۸.۱ معماری HiveOS و حلقهٔ ReAct

در معماری **HiveOS**، عامل‌ها در دامنه‌ها (Domains) مستقر هستند و هر عامل می‌تواند از الگوی ReAct برای استدلال و اقدام استفاده کند. نگاشت ReAct به مؤلفه‌های HiveOS به صورت زیر است:

```text
┌────────────────────────────────────────────────────┐
│                   HiveOS Architecture               │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │          Mothership (Orchestrator)           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Planning  │ │ Policy   │ │ State Mgmt │  │   │
│  │  │ Unit     │ │ Unit     │ │ & Memory   │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────┬──────────────────────────────────┘   │
│             │                                       │
│  ┌──────────▼──────────────────────────────────┐   │
│  │         Agent Domain (دامنهٔ عامل)           │   │
│  │                                              │   │
│  │  ┌──────────────────────────────────┐        │   │
│  │  │        ReAct Loop in HiveOS      │        │   │
│  │  │                                  │        │   │
│  │  │  Thought ─→ Action ─→ Observation│        │   │
│  │  │    │            │           │     │        │   │
│  │  │    │            ▼           │     │        │   │
│  │  │    │     ┌────────────┐    │     │        │   │
│  │  │    │     │  Tool Use  │    │     │        │   │
│  │  │    │     │  از طریق   │    │     │        │   │
│  │  │    │     │  MCP/Gatewy│    │     │        │   │
│  │  │    │     └────────────┘    │     │        │   │
│  │  │    └───────────────────────┘     │        │   │
│  │  └──────────────────────────────────┘        │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────┐  ┌──────────────┐  │
│  │      MCP Servers            │  │   Gateway    │  │
│  │  (ابزارهای استاندارد)        │  │  (ارتباط با  │  │
│  │                             │  │   دنیای خارج)│  │
│  └─────────────────────────────┘  └──────────────┘  │
└────────────────────────────────────────────────────┘
```

### ۸.۲ نگاشت مؤلفه‌ها

| مفهوم در ReAct | معادل در HiveOS |
|---------------|-----------------|
| **Thought (استدلال)** | مدل زبانی (LLM) درون عامل — هر عامل یک مدل اصلی دارد |
| **Action (اقدام)** | فراخوانی ابزار از طریق **Gateway** یا **MCP Client** |
| **Observation (مشاهده)** | بازگشت نتیجه از طریق مسیریابی (Routing) به عامل |
| **ابزارها (Tools)** | سرویس‌های MCP یا توابع ثبت‌شده در پیکربندی عامل |
| **حافظه (Memory)** | سیستم حافظهٔ HiveOS — ذخیرهٔ تاریخچهٔ استدلال |
| **Orchestration** | **Mothership** که حلقه را مدیریت و محدود می‌کند |
| **Policy (خط‌مشی)** | Policy Unit در Mothership — محدودیت‌های دسترسی به ابزارها |
| **Human-in-the-Loop** | دروازه (Gateway) برای تأیید انسانی |

### ۸.۳ سه الگوی استدلال در HiveOS

در HiveOS، هر عامل می‌تواند بسته به نوع وظیفه از یکی از سه الگوی زیر استفاده کند:

#### ۸.۳.۱ الگوی ساده: Function Calling در HiveOS

برای وظایف ساده و تک‌مرحله‌ای:

```yaml
# پیکربندی عامل HiveOS با Function Calling
agent:
  name: weather-checker
  domain: tools
  reasoning_pattern: function-calling  # الگوی ساده
  llm:
    model: gpt-4o-mini  # مدل سبک و سریع
  tools:
    - name: get_weather
      mcp_server: weather-service
      description: دریافت دمای هوای یک شهر
    - name: get_time
      mcp_server: time-service
```

#### ۸.۳.۲ الگوی پیشرفته: ReAct در HiveOS

برای وظایف چندمرحله‌ای و اکتشافی:

```yaml
agent:
  name: research-assistant
  domain: research
  reasoning_pattern: react  # الگوی ReAct
  llm:
    model: claude-opus-4  # مدل قوی برای استدلال عمیق
    system_prompt: |
      شما یک عامل تحقیقاتی در HiveOS هستید.
      
      برای پاسخ به سؤالات، از ابزارهای زیر استفاده کنید:
      
      {tools_descriptions}
      
      قالب پاسخ:
      Thought: تحلیل فعلی و گام بعدی
      Action: نام ابزار
      Action Input: ورودی ابزار (JSON)
      Observation: نتیجه
      
      حلقه را تا رسیدن به پاسخ نهایی ادامه دهید.
      
  max_iterations: 15  # حداکثر ۱۵ گام
  tools:
    - name: web_search
      mcp_server: search-service
    - name: read_document
      mcp_server: document-store
    - name: code_interpreter
      mcp_server: sandbox
  memory:
    type: persistent  # حافظهٔ پایدار برای یادآوری تاریخچه
    scope: session
```

#### ۸.۳.۳ الگوی ترکیبی: Plan-and-Execute در HiveOS

برای وظایف با مراحل قابل برنامه‌ریزی:

```yaml
agent:
  name: report-generator
  domain: analytics
  reasoning_pattern: plan-and-execute
  llm:
    planner_model: claude-opus-4  # مدل قوی برای برنامه‌ریزی
    worker_model: gpt-4o-mini     # مدل سبک برای اجرا
  plan:
    max_steps: 20
    re_plan_enabled: true         # امکان بازبرنامه‌ریزی
    parallel_execution: true      # اجرای موازی گام‌های مستقل
  tools:
    - name: query_database
      mcp_server: analytics-db
    - name: generate_chart
      mcp_server: visualization
    - name: export_pdf
      mcp_server: document-service
```

### ۸.۴ نمونه: عامل ReAct در HiveOS

سناریو: کاربر از عامل می‌خواهد «روند فروش سه‌ماههٔ آخر را تحلیل کند و یک نمودار از آن بسازد.»

```text
=== شروع حلقهٔ ReAct در HiveOS ===

Thought: کاربر روند فروش سه‌ماهه را می‌خواهد. ابتدا باید داده‌ها را از پایگاه داده بگیرم.

Action: query_database
Action Input: {"query": "SELECT month, sales FROM quarterly_sales WHERE quarter = 'Q2-2026'"}

Observation: [
  {"month": "April", "sales": 45000},
  {"month": "May", "sales": 52000},
  {"month": "June", "sales": 61000}
]

Thought: داده‌ها را دارم. روند صعودی است. حالا باید یک نمودار خطی از این داده‌ها بسازم.

Action: generate_chart
Action Input: {"type": "line", "data": [...], "title": "Q2 2026 Sales Trend"}

Observation: chart_generated (file: /output/q2-sales-trend.png)

Thought: نمودار ساخته شد. حالا تحلیل نهایی را به کاربر ارائه می‌دهم.

Final Answer:
📊 **تحلیل فروش سه‌ماههٔ دوم ۲۰۲۶**

روند فروش در Q2 2026 صعودی بوده است:
- آوریل: ۴۵,۰۰۰ دلار
- مه: ۵۲,۰۰۰ دلار  (۱۵٪+)
- ژوئن: ۶۱,۰۰۰ دلار (۱۷٪+)

نمودار در فایل q2-sales-trend.png ذخیره شده است.

=== پایان حلقه ===
```

### ۸.۵ Human-in-the-Loop در حلقهٔ ReAct-HiveOS

یکی از تفاوت‌های مهم HiveOS، پشتیبانی از **Human-in-the-Loop** در میانهٔ حلقه است:

```text
Thought: باید فاکتور شماره ۱۰۲۴ را لغو کنم. اما این عملیات حساس است.

Action: human_approval  # درخواست تأیید انسانی
Action Input: {
  "action": "cancel_invoice",
  "invoice_id": "1024",
  "amount": 15000,
  "reason": "درخواست مشتری",
  "requested_by": "agent@finance"
}

[HUMAN-IN-THE-LOOP: کاربر در Gateway تأیید می‌کند]

Observation: approval_granted

Action: cancel_invoice
Action Input: {"invoice_id": "1024"}

Observation: invoice_cancelled

Thought: فاکتور با تأیید کاربر لغو شد.

Final Answer: فاکتور ۱۰۲۴ به مبلغ ۱۵,۰۰۰ دلار لغو شد.
```

---

## ۹. چالش‌ها و بهترین روش‌ها (Challenges & Best Practices)

### ۹.۱ چالش‌های رایج

| چالش | توضیح | راهکار |
|------|-------|--------|
| **Loop نامحدود** | عامل در حلقه گیر می‌کند و تمام نمی‌شود | تعیین `max_iterations`، تشخیص حلقهٔ تکراری |
| **هزینهٔ Token** | استدلال مکرر Token زیادی مصرف می‌کند | استفاده از Plan-and-Execute برای کاهش فراخوانی LLM |
| **توهم (Hallucination)** | مدل نتایج جعلی به عنوان Observation گزارش می‌کند | اعتبارسنجی نتایج، استفاده از tool schema دقیق |
| **خطای ابزار** | ابزار خطا برمی‌گرداند و عامل نمی‌داند چه کند | پیام‌های خطای descriptive، fallback strategy |
| **Latency** | زمان زیاد به دلیل فراخوانی متوالی LLM | اجرای موازی (LLMCompiler)، کش کردن نتایج |

### ۹.۲ بهترین روش‌ها (Best Practices)

1. **همیشه `max_iterations` تعیین کنید** — از حلقهٔ نامحدود جلوگیری کنید
2. **ابزارها را با توضیحات دقیق ثبت کنید** — مدل باید بداند هر ابزار چه می‌کند
3. **از State Management استفاده کنید** — تاریخچهٔ کامل استدلال را ذخیره کنید
4. **Error Handling در ابزارها** — ابزارها باید خطاهای descriptive برگردانند
5. **Caching نتایج ابزارها** — از فراخوانی تکراری جلوگیری کنید
6. **Observability** — تمام حلقه را لاگ کنید برای Debugging
7. **مدل مناسب انتخاب کنید** — ReAct نیاز به مدل قوی دارد؛ Function Calling با مدل سبک‌تر هم کار می‌کند

---

## ۱۰. جمع‌بندی (Summary)

| الگو | ایدهٔ اصلی | قیمت | سرعت | انعطاف | کاربرد اصلی |
|------|-----------|------|------|--------|------------|
| **Function Calling** | LLM → JSON → اجرای تابع | 💰 | ⚡⚡ | ❌ | وظایف ساده و تک‌مرحله‌ای |
| **ReAct** | Thought → Action → Observation | 💰💰💰 | 🐢 | ✅✅ | وظایف پویا و اکتشافی |
| **Plan-and-Execute** | برنامه → اجرا → پاسخ | 💰💰 | ⚡ | ✅ | وظایف قابل پیش‌بینی چندمرحله‌ای |

### نکات کلیدی برای معماری HiveOS:

1. **انتخاب الگوی مناسب**: هر دامنه (Domain) در HiveOS می‌تواند الگوی استدلال متفاوتی داشته باشد — دامنهٔ ابزارهای ساده از Function Calling، دامنهٔ تحقیقات از ReAct، دامنهٔ گزارش‌گیری از Plan-and-Execute.

2. **ترکیب الگوها**: Mothership می‌تواند یک وظیفه را با Plan-and-Execute به زیروظایف بشکند و هر زیروظیفه را با ReAct به یک عامل تخصصی واگذار کند.

3. **حافظه و زمینه (Memory & Context)**: حلقهٔ ReAct به حافظهٔ طولانی نیاز دارد. HiveOS با سیستم حافظهٔ پایدار (Persistent Memory) این نیاز را برآورده می‌کند.

4. **ابزارهای استاندارد از طریق MCP**: همهٔ ابزارها در HiveOS از طریق MCP در دسترس هستند — این کار ثبت و کشف ابزارها را استاندارد می‌کند.

5. **حکمرانی (Governance)**: خط‌مشی‌های Policy Unit در Mothership بر روی Action‌های حلقه نظارت می‌کنند و از اقدامات غیرمجاز جلوگیری می‌نمایند.

---

> **نویسنده:** مستند فنی HiveOS — برگرفته از مقالات «ReAct: Synergizing Reasoning and Acting in Language Models» (Yao et al., 2023)، «Plan-and-Solve Prompting» (Wang et al., 2023)، «ReWOO» (Xu et al., 2023)، مستندات IBM ReAct Agent، و LangChain Blog on Plan-and-Execute Agents
>
> **تاریخ:** جولای ۲۰۲۶
> **مسیر:** `docs/06-Research/agents/01-Fundamentals/03-reasoning-and-planning.md`

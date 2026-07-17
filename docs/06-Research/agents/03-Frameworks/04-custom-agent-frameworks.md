# فریمورک‌های عاملی سفارشی — Custom Agent Frameworks

> **نویسنده:** تیم مستندات HiveOS
> **تاریخ:** جولای ۲۰۲۶
> **منابع:** HiveOS Architecture · LangChain/LangGraph Docs · Semantic Kernel · AutoGPT · smolagents (HuggingFace)

---

## ۱. مقدمه: چرا فریمورک سفارشی؟

چهار فریمورک اصلی (LangGraph, CrewAI, AutoGen, OpenAI SDK) دنیای وسیعی را پوشش می‌دهند، اما گاهی نیاز به **فریمورک اختصاصی** دارید:

### چه زمانی فریمورک سفارشی لازم است؟

| سناریو | مشکل فریمورک‌های موجود | راهکار |
|--------|----------------------|--------|
| **دامنهٔ بسیار خاص** | LangGraph بیش‌ازحد عمومی است | فریمورک دامنه‌محور (Domain-Specific) |
| **نیاز به معماری خاص** | هیچ‌کدام از الگوی مورد نظر پشتیبانی نمی‌کنند | معماری سفارشی |
| **بهینه‌سازی هزینه** | فریمورک‌های عمومی LLM را زیاد صدا می‌زنند | فریمورک کم‌هزینه با منطق قطعی |
| **یکپارچه‌سازی با سیستم legacy** | فریمورک‌ها با API قدیمی سازگار نیستند | فریمورک تطبیقی |
| **نیازهای امنیتی خاص** | فریمورک‌های عمومی sandbox کافی ندارند | فریمورک امن با ایزوله‌سازی قوی |
| **آموزشی / تحقیقاتی** | می‌خواهید عمیقاً بفهمید agentها چطور کار می‌کنند | فریمورک از صفر |

> **نکته:** HiveOS خودش یک **فریمورک سفارشی** است — بر اساس نیازهای خاص یک Multi-Agent Operating System برای دامنه‌های کسب‌وکاری طراحی شده.

---

## ۲. نمونه‌های موفق فریمورک‌های سفارشی

### ۲.۱ AutoGPT — قدیمی‌ترین فریمورک عاملی منبع‌باز

**معماری:** یک حلقهٔ ساده که LLM را با پرامپت ReAct صدا می‌زند.

```python
# AutoGPT simplified loop
class AutoGPT:
    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.memory = memory
        self.history = []
    
    async def run(self, goal: str) -> str:
        self.history.append({"role": "system", "content": f"Goal: {goal}"})
        
        for iteration in range(MAX_ITERATIONS):
            # ۱. LLM تصمیم می‌گیرد下一步 چیست
            response = await self.llm.generate(
                messages=self.history,
                tools=list(self.tools.values())
            )
            
            # ۲. بررسی پاسخ
            if response.is_final():
                return response.content
            
            # ۳. اجرای ابزار
            if response.has_tool_call():
                tool_name = response.tool_calls[0].function.name
                tool_args = json.loads(
                    response.tool_calls[0].function.arguments
                )
                result = self.tools[tool_name].run(**tool_args)
                
                # ۴. ذخیره در تاریخچه
                self.history.append({
                    "role": "assistant",
                    "content": f"Tool: {tool_name}\nResult: {result}"
                })
        
        return "Max iterations reached"
```

**نقاط قوت:** سادگی مطلق — هرکسی می‌تواند بفهمد چطور کار می‌کند
**نقاط ضعف:** عدم مدیریت state پیچیده، عدم fault tolerance

### ۲.۲ HuggingFace smolagents

یک فریمورک **مینیمال** و **مدرن** که روی **code agents** تمرکز دارد:

```python
from smolagents import CodeAgent, HfApiModel, tool

@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """دریافت نرخ تبدیل ارز"""
    # فراخوانی API واقعی
    return 750_000  # IRR per USD (مثال)

agent = CodeAgent(
    model=HfApiModel("Qwen/Qwen2.5-Coder-32B-Instruct"),
    tools=[get_exchange_rate],
    max_steps=10,
    verbosity_level=2
)

# عامل کد Python می‌نویسد و اجرا می‌کند
result = agent.run(
    "مبلغ ۵۰۰ دلار را به تومان تبدیل کن با نرخ امروز، "
    "سپس ۹٪ مالیات بر ارزش افزوده را محاسبه کن"
)
```

**فلسفه:** به جای اینکه LLM JSON tool call تولید کند، **کد Python** می‌نویسد — انعطاف بسیار بیشتر.

### ۲.۳ Semantic Kernel (Microsoft)

یک فریمورک لایه‌بالاتر که **planning** را به صورت Native پشتیبانی می‌کند:

```python
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.planners import SequentialPlanner

kernel = Kernel()
kernel.add_service(AzureChatCompletion("gpt-4o"))

# ثبت مهارت‌ها (ابزارها)
kernel.import_plugin_from_directory(
    "plugins/financial_plugins"
)

# برنامه‌ریز خودکار
planner = SequentialPlanner(kernel)
plan = await planner.create_plan(
    goal="محاسبه مالیات حقوق فروردین ۱۴۰۴"
)

# اجرای برنامه
result = await plan.invoke()
```

---

## ۳. طراحی فریمورک عاملی از صفر (Building from Scratch)

بیایید یک **فریمورک عاملی مینیمال** اما کامل طراحی کنیم:

### ۳.۱ هسته (Core)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable
import json, asyncio, logging
from datetime import datetime

# ===========================
# ۱. انواع پایه (Base Types)
# ===========================

@dataclass
class Tool:
    """یک ابزار که عامل می‌تواند استفاده کند"""
    name: str
    description: str
    parameters: dict  # JSON Schema
    function: Callable

    async def run(self, **kwargs) -> Any:
        """اجرای ابزار با آرگومان‌های داده شده"""
        try:
            result = await self.function(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

@dataclass
class AgentConfig:
    """تنظیمات عامل"""
    name: str
    system_prompt: str
    tools: list[Tool]
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_steps: int = 20

@dataclass
class Message:
    """یک پیام در تاریخچه"""
    role: str  # system | user | assistant | tool
    content: str
    tool_calls: list = None
    tool_call_id: str = None
    timestamp: datetime = field(default_factory=datetime.now)

# ===========================
# ۲. موتور اجرا (Execution Engine)
# ===========================

class AgentRuntime:
    """موتور اجرای عامل — هستهٔ فریمورک"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.messages: list[Message] = []
        self.logger = logging.getLogger(f"Agent:{config.name}")
        
        # مقداردهی اولیه
        self.messages.append(Message(
            role="system",
            content=config.system_prompt
        ))
    
    async def run(self, user_input: str) -> str:
        """اجرای کامل عامل با ورودی کاربر"""
        self.messages.append(Message(
            role="user",
            content=user_input
        ))
        
        for step in range(self.config.max_steps):
            self.logger.info(f"🧠 Step {step + 1}: Calling LLM")
            
            # گام ۱: فراخوانی LLM
            response = await self._call_llm()
            
            # گام ۲: بررسی پاسخ LLM
            if response["type"] == "final":
                # پاسخ نهایی
                self.messages.append(Message(
                    role="assistant",
                    content=response["content"]
                ))
                return response["content"]
            
            elif response["type"] == "tool_call":
                # فراخوانی ابزار
                tool_name = response["tool_name"]
                tool_args = response["tool_args"]
                
                self.logger.info(f"🔧 Tool: {tool_name}({tool_args})")
                
                # اجرای ابزار
                tool_result = await self._execute_tool(
                    tool_name, tool_args
                )
                
                self.logger.info(f"📊 Result: {str(tool_result)[:200]}...")
                
                # ذخیره در تاریخچه
                self.messages.append(Message(
                    role="assistant",
                    content=f"Calling tool: {tool_name}",
                    tool_calls=[{
                        "id": f"call_{step}",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args)
                        }
                    }]
                ))
                self.messages.append(Message(
                    role="tool",
                    content=str(tool_result),
                    tool_call_id=f"call_{step}"
                ))
            
            else:
                # خطا
                self.logger.error(f"❌ Unknown response type: {response}")
                return f"Error: Unknown LLM response type"
        
        return "Max steps reached without final answer"
    
    async def _call_llm(self) -> dict:
        """فراخوانی LLM — در عمل از OpenAI/Anthropic API استفاده می‌کند"""
        # اینجا یک stub است — در عمل API واقعی صدا زده می‌شود
        # شبیه‌سازی:
        last_msg = self.messages[-1].content
        if "نهایی" in last_msg:
            return {"type": "final", "content": "پاسخ نهایی"}
        else:
            return {
                "type": "tool_call",
                "tool_name": "web_search",
                "tool_args": {"query": last_msg}
            }
    
    async def _execute_tool(self, name: str, args: dict) -> Any:
        """اجرای ابزار مشخص‌شده"""
        if name in self.config.tools_by_name:
            tool = self.config.tools_by_name[name]
            return await tool.run(**args)
        return {"error": f"Tool '{name}' not found"}
```

### ۳.۲ مدیریت حافظه (Memory Management)

```python
@dataclass  
class Memory:
    """حافظهٔ عامل — ساده، قابل گسترش"""
    short_term: list[Message] = field(default_factory=list)
    long_term: dict = field(default_factory=dict)
    
    def add_to_short_term(self, message: Message):
        """افزودن به حافظهٔ کوتاه‌مدت"""
        self.short_term.append(message)
        # محدودیت اندازه
        if len(self.short_term) > 50:
            self._compress()
    
    def _compress(self):
        """فشرده‌سازی حافظه — خلاصه‌سازی پیام‌های قدیمی"""
        old_messages = self.short_term[:-20]
        summary = f"[خلاصهٔ {len(old_messages)} پیام قبلی]"
        self.short_term = [Message(
            role="system",
            content=summary
        )] + self.short_term[-20:]
    
    def save_to_long_term(self, key: str, value: Any):
        """ذخیره در حافظهٔ بلندمدت"""
        self.long_term[key] = {
            "value": value,
            "saved_at": datetime.now().isoformat()
        }
    
    def query_long_term(self, key: str) -> Any:
        """بازیابی از حافظهٔ بلندمدت"""
        entry = self.long_term.get(key)
        return entry["value"] if entry else None
```

### ۳.۳ مدیریت خطا و بازیابی

```python
class RetryHandler:
    """مدیریت تلاش مجدد برای ابزارها"""
    
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # ثانیه
    
    async def execute_with_retry(
        self, tool: Tool, **kwargs
    ) -> dict:
        """اجرای ابزار با قابلیت تلاش مجدد"""
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                result = await tool.run(**kwargs)
                
                # بررسی موفقیت
                if result.get("success", True):
                    return result
                
                last_error = result.get("error", "Unknown error")
                
            except Exception as e:
                last_error = str(e)
            
            # تأخیر نمایی (Exponential Backoff)
            delay = self.BASE_DELAY * (2 ** (attempt - 1))
            logging.warning(
                f"🔄 Retry {attempt}/{self.MAX_RETRIES} "
                f"for tool '{tool.name}' after {delay}s: {last_error}"
            )
            await asyncio.sleep(delay)
        
        return {"success": False, "error": f"All retries failed: {last_error}"}
```

---

## ۴. معماری HiveOS به عنوان فریمورک سفارشی

HiveOS یک فریمورک عاملی اختصاصی است که برای **سیستم‌های چندعاملی سازمانی** طراحی شده. مقایسه با فریمورک‌های عمومی:

| ویژگی | LangGraph | CrewAI | HiveOS |
|--------|-----------|--------|--------|
| **State Management** | TypedDict + Reducer | Implicit (task outputs) | StorageEngine (SQLite) |
| **Multi-Agent** | Graph nodes | Crew roles | Domain Registry + Mothership |
| **Persistence** | ✅ ChatGPT | ❌ | ✅ SQLite + Migrations |
| **Human-in-Loop** | interrupt_before | Callbacks | Approval Gate Engine ✅ |
| **Observability** | LangSmith | Limited | Audit Trail + Brain 3D |
| **Domain-Specific** | ❌ General | ❌ General | ✅ Domain Registry ✅ |
| **RBAC** | ❌ | ❌ | ✅ Complete RBAC |
| **Desktop UI** | ❌ | ❌ | ✅ FastAPI Dashboard + PWA |

### اجزای فریمورک HiveOS:

```python
# نمای کلی معماری HiveOS Agent Framework
from hiveos.agent import Agent
from hiveos.domain import DomainRegistry
from hiveos.mothership import Mothership
from hiveos.flow import FlowEngine

# ۱. ثبت دامنه‌ها
registry = DomainRegistry(storage_engine=storage)
registry.scan_domains()  # جستجوی خودکار دامنه‌ها

# ۲. ثبت عامل‌ها
agent = Agent(
    name="financial-analyst",
    domain="accounting",
    llm_config={"model": "claude-sonnet-4"},
    tools=[
        FinancialStatementReader(),
        RatioAnalyzer(),
        ReportGenerator()
    ]
)
registry.register_agent(agent)

# ۳. تعریف Flow
flow = FlowEngine.define_flow({
    "name": "financial-report",
    "orchestrator": "mothership",
    "steps": [
        {"agent": "data-collector", "parallel": True},
        {"agent": "financial-analyst", "depends_on": ["data-collector"]},
        {"agent": "report-writer", "depends_on": ["financial-analyst"]}
    ]
})

# ۴. اجرا با RBAC و Audit
result = await Mothership.run_flow(
    flow=flow,
    user="user@company.com",
    context={"task": "تحلیل صورت‌های مالی ۱۴۰۴"}
)
```

---

## ۵. چارچوب تصمیم‌گیری: بسازیم یا بخریم؟

| معیار | فریمورک موجود (Buy) | فریمورک سفارشی (Build) |
|-------|-------------------|---------------------|
| **سرعت پیاده‌سازی** | سریع (روزها) | کند (هفته‌ها تا ماه‌ها) |
| **انعطاف‌پذیری** | محدود به امکانات فریمورک | نامحدود |
| **هزینه نگهداری** | کم (بروزرسانی توسط فریمورک) | زیاد (تیم خودتان) |
| **ویژگی‌های خاص** | شاید پشتیبانی نکند | دقیقاً مطابق نیاز |
| **مستندات و جامعه** | عالی | باید خودتان بسازید |
| **آمادگی تولید (Production)** | معمولاً خوب | نیاز به کار اضافی |

### معیارهای تصمیم‌گیری:

1. **اگر نیاز به یکپارچه‌سازی با سیستم legacy دارید** → Build (فریمورک‌ها معمولاً inflexible هستند)
2. **اگر دامنهٔ خیلی خاصی دارید** (مثل حسابداری ایران) → Build یا Customize روی یک فریمورک
3. **اگر تیم limited دارید** → Buy (LangGraph یا CrewAI)
4. **اگر مقیاس خیلی بزرگ دارید** → Build (بهینه‌سازی هزینه و latency)
5. **اگر نیاز به HITL پیچیده دارید** → LangGraph (قوی‌ترین HITL) یا HiveOS

---

## ۶. جمع‌بندی

| # | نکته |
|---|------|
| ۱ | **فریمورک سفارشی** زمانی لازم است که فریمورک‌های عمومی نیازهای خاص شما را پوشش نمی‌دهند |
| ۲ | **AutoGPT** ساده‌ترین معماری را دارد — یک حلقهٔ ReAct ساده |
| ۳ | **smolagents (HuggingFace)** رویکرد جالبی دارد: عامل کد Python می‌نویسد به جای JSON tool call |
| ۴ | **Semantic Kernel (Microsoft)** روی planning تأکید دارد |
| ۵ | **هستهٔ هر فریمورک:** LLM + Tools + Memory + Loop |
| ۶ | **بازیابی از خطا (Retry + Fallback)** را هر فریمورک باید داشته باشد |
| ۷ | **HiveOS یک فریمورک سفارشی Domain-Specific** است با ویژگی‌های سازمانی (RBAC, Audit, HITL, Persistence) |
| ۸ | **تصمیم Build vs. Buy** به تیم، دامنه، مقیاس و نیازهای خاص شما بستگی دارد |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل‌های مرتبط:**
> - `docs/06-Research/agents/03-Frameworks/01-agent-frameworks-overview.md`
> - `src/hiveos/agent/` — پیاده‌سازی Agent در HiveOS
> - `src/hiveos/mothership/` — لایه‌ orchestration

# معماری‌های عامل هوش مصنوعی — AI Agent Architectures

> **منبع:** برگرفته و بومی‌سازی‌شده از مقالات arXiv «Intelligent Agent Architectures: A Survey» (Nwakanma et al., 2024)، «Tree-of-Thoughts: Deliberate Problem Solving with LLMs» (Yao et al., 2023)، «Reflexion: Language Agents with Verbal Reinforcement Learning» (Shinn et al., 2023)، «Mixture-of-Agents Enhances Large Language Model Capabilities» (Wang et al., 2024)، مستندات LangGraph و منابع کلاسیک AI

> **مسیر:** `docs/06-Research/agents/01-Fundamentals/02-agent-architectures.md`

---

## فهرست مطالب (Table of Contents)

| # | بخش | توضیح |
|---|------|--------|
| ۱ | [معماری‌های کلاسیک عامل](#۱-معماری‌های-کلاسیک-عامل-classic-agent-architectures) | Reactive, Deliberative (BDI), Hybrid |
| ۲ | [معماری‌های مدرن مبتنی بر LLM](#۲-معماری‌های-مدرن-مبتنی-بر-llm-modern-llm-based-architectures) | ReAct, Plan-and-Execute, ToT, Reflection, MoA |
| ۳ | [لایه‌های معماری](#۳-لایه‌های-معماری-architectural-layers) | Perception, Reasoning, Memory, Action |
| ۴ | [حالت ماشین در برابر معماری گراف](#۴-حالت-ماشین-در-برابر-معماری-گراف-state-machines-vs-graph-based) | LangGraph-style State Machines |
| ۵ | [الگوهای تصمیم‌گیری](#۵-الگوهای-تصمیم‌گیری-decision-making-patterns) | Single-pass, Iterative, Hierarchical |
| ۶ | [جدول مقایسهٔ جامع](#۶-جدول-مقایسه-جامع-comparison-table) | همهٔ معماری‌ها در یک نگاه |
| ۷ | [نگاشت به HiveOS](#۷-نگاشت-به-hiveos-mapping-to-hiveos) | ارتباط با معماری HiveOS |

---

## ۱. معماری‌های کلاسیک عامل (Classic Agent Architectures)

پیش از ظهور مدل‌های زبانی بزرگ (LLMs)، عامل‌های هوش مصنوعی با سه معماری اصلی طراحی می‌شدند که هرکدام رویکرد متفاوتی به **ادراک → استدلال → اقدام (Perception → Reasoning → Action)** داشتند.

### ۱.۱ معماری واکنشی (Reactive Architecture)

عامل‌های **واکنشی (Reactive)** ساده‌ترین نوع معماری هستند. در این معماری، عامل **بدون حافظهٔ داخلی (internal state)** و **بدون برنامه‌ریزی (planning)** کار می‌کند — مستقیماً از **ادراک (Perception)** به **اقدام (Action)** می‌رسد.

> **تشبیه برای مخاطب ایرانی:** مثل یک **ترموستات هوشمند** — اگر دما از حد معین بالاتر برود، کولر را روشن می‌کند. هیچ «فکر» یا «برنامه»ای در کار نیست؛ فقط یک قانون ساده: اگه X دیدی، Y کن.

```text
┌─────────────────────────────────────────┐
│       Reactive Agent Architecture         │
│                                           │
│  ┌────────────┐     ┌──────────────┐     │
│  │  Sensors   │────▶│   Condition- │     │
│  │ (حسگرها)   │     │   Action     │     │
│  │            │     │   Rules      │     │
│  └────────────┘     │ (قوانین شرط- │     │
│         ▲           │   اقدام)    │     │
│         │           └──────┬───────┘     │
│         │                  │             │
│  ┌──────┴───────┐         ▼             │
│  │  Environment  │   ┌────────────┐     │
│  │  (محیط)      │◀──│ Effectors  │     │
│  └──────────────┘   │ (عملگرها)  │     │
│                     └────────────┘     │
└─────────────────────────────────────────┘
```

**ویژگی‌های کلیدی:**

| ویژگی | توضیح |
|--------|-------|
| **حافظه (Memory)** | ❌ ندارد — بدون وضعیت داخلی (Stateless) |
| **برنامه‌ریزی (Planning)** | ❌ ندارد |
| **سرعت پاسخ** | ⚡ بسیار بالا |
| **پیچیدگی** | 🔧 پایین |
| **مقیاس‌پذیری** | بالا برای محیط‌های ساده |

**نمونهٔ کد — عامل واکنشی ساده:**

```python
from typing import Dict, Callable

class ReactiveAgent:
    """عامل واکنشی: مستقیماً از حسگر به عملگر می‌رسد"""

    def __init__(self):
        # قوانین شرط → اقدام (Condition → Action Rules)
        self.rules: Dict[str, Callable] = {
            "enemy_visible": self._attack_enemy,
            "low_health":   self._find_healing,
            "resource_near": self._collect_resource,
        }
        self.sensors = {}  # داده‌های دریافتی از محیط

    def perceive(self, sensor_data: dict):
        """دریافت داده از محیط"""
        self.sensors = sensor_data

    def decide(self) -> str:
        """تصمیم‌گیری بر اساس قوانین — هیچ استدلالی انجام نمی‌شود"""
        for condition, action in self.rules.items():
            if self.sensors.get(condition, False):
                action()
                return f"executed: {condition}"
        return "no_rule_matched"

    def _attack_enemy(self):
        print("⚔️ حمله به دشمن!")

    def _find_healing(self):
        print("💊 جستجوی منابع درمانی")

    def _collect_resource(self):
        print("📦 جمع‌آوری منبع")

# استفاده
agent = ReactiveAgent()
agent.perceive({"enemy_visible": True, "low_health": False})
agent.decide()  # خروجی: ⚔️ حمله به دشمن!
```

**مزایا و محدودیت‌ها:**

| مزایا | محدودیت‌ها |
|-------|-----------|
| ✅ سرعت بالا — تصمیم در میلی‌ثانیه | ❌ بدون حافظه — نمی‌تواند از تجربه یاد بگیرد |
| ✅ پیاده‌سازی ساده | ❌ انعطاف‌ناپذیر — قوانین ثابت |
| ✅ مقیاس‌پذیری برای سیستم‌های ساده | ❌ شکست در وظایف پیچیده چندمرحله‌ای |
| ✅ Robust در محیط‌های قابل پیش‌بینی | ❌ بدون توانایی برنامه‌ریزی بلندمدت |

**کاربردهای واقعی:** کنترل‌کننده‌های صنعتی، ترموستات‌های هوشمند، ربات‌های سادهٔ خط‌دنبال‌کن، فایروال‌های مبتنی بر قانون.

### ۱.۲ معماری استدلالی (Deliberative Architecture — BDI)

معماری **استدلالی یا تعمّدی (Deliberative)** بر پایهٔ **مدل‌سازی صریح جهان (explicit world model)** و **برنامه‌ریزی (Planning)** است. معروف‌ترین زیرمجموعهٔ آن **BDI (Belief-Desire-Intention)** است که در سال ۱۹۹۵ توسط Rao و Georgeff در مقالهٔ معروف «BDI Agents: From Theory to Practice» معرفی شد.

> **تشبیه برای مخاطب ایرانی:** مثل یک **مدیر پروژه** که (۱) از وضعیت فعلی آگاه است (Belief)، (۲) می‌داند چه می‌خواهد (Desire)، و (۳) یک برنامهٔ عملی برای رسیدن به هدف دارد (Intention).

```text
┌──────────────────────────────────────────────────┐
│           BDI Agent Architecture                   │
│                                                    │
│  ┌──────────────┐                                 │
│  │   Beliefs    │  باورها — مدل عامل از جهان       │
│  │  (باورها)    │  "Tehran temp = 38°C"           │
│  └──────┬───────┘                                 │
│         │                                          │
│  ┌──────▼───────┐                                 │
│  │   Desires    │  آرزوها — اهداف عامل              │
│  │  (آرزوها)    │  "Maximize user satisfaction"    │
│  └──────┬───────┘                                 │
│         │                                          │
│  ┌──────▼───────┐    ┌──────────────────────┐     │
│  │  Intentions  │───▶│   Plan Library       │     │
│  │  (نیت‌ها)    │    │  (کتابخانهٔ برنامه)  │     │
│  └──────┬───────┘    └──────────────────────┘     │
│         │                                          │
│         ▼                                          │
│  ┌──────────────┐                                 │
│  │   Action     │  اقدام — اجرای برنامهٔ انتخاب‌شده│
│  │  (اقدام)     │                                 │
│  └──────────────┘                                 │
└──────────────────────────────────────────────────┘
```

**سه مؤلفهٔ اصلی BDI:**

| مؤلفه (Component) | توضیح | مثال |
|-------------------|-------|------|
| **Belief (باور)** | دانش عامل از جهان — می‌تواند ناقص یا نامطمئن باشد | `belief("weather", "tehran", 38)` |
| **Desire (آرزو)** | وضعیت‌های مطلوبی که عامل می‌خواهد به آن برسد | `desire("answer_user_within_5s")` |
| **Intention (نیت)** | برنامهٔ عملی که عامل برای رسیدن به Desire انتخاب کرده | `intention: [search_weather, format_response, send_reply]` |

**حلقهٔ اجرایی BDI — پیاده‌سازی شبه‌کد:**

```python
from enum import Enum
from typing import List, Dict, Any
import time

class BeliefState:
    """باورهای عامل — مدل داخلی از جهان"""
    def __init__(self):
        self.facts: Dict[str, Any] = {}

    def update(self, sensor_data: Dict[str, Any]):
        self.facts.update(sensor_data)

    def query(self, key: str) -> Any:
        return self.facts.get(key, None)

class Desire:
    """آرزو — هدفی که عامل دنبال می‌کند"""
    def __init__(self, name: str, priority: int, condition_fn):
        self.name = name
        self.priority = priority
        self.condition_fn = condition_fn  # تابع بررسی امکان‌پذیری

    def is_achievable(self, beliefs: BeliefState) -> bool:
        return self.condition_fn(beliefs)

class Plan:
    """برنامه — دنباله‌ای از اقدامات برای رسیدن به هدف"""
    def __init__(self, name: str, steps: List[str]):
        self.name = name
        self.steps = steps

class BDIAgent:
    """عامل BDI — Belief-Desire-Intention"""

    def __init__(self):
        self.beliefs = BeliefState()
        self.desires: List[Desire] = []
        self.intentions: List[Plan] = []
        self.plans: Dict[str, Plan] = {}  # کتابخانهٔ برنامه‌ها

    def perceive(self, sensor_data: Dict[str, Any]):
        """به‌روزرسانی باورها از طریق حسگرها"""
        self.beliefs.update(sensor_data)

    def deliberate(self):
        """بررسی آرزوها — کدام آرزو قابل دستیابی است؟"""
        achievable = [
            d for d in self.desires
            if d.is_achievable(self.beliefs)
        ]
        if achievable:
            # انتخاب آرزوی با اولویت بالاتر
            chosen = max(achievable, key=lambda d: d.priority)
            self._form_intention(chosen)

    def _form_intention(self, desire: Desire):
        """تشکیل نیت — انتخاب برنامهٔ مناسب از کتابخانه"""
        plan = self.plans.get(f"plan_for_{desire.name}")
        if plan:
            self.intentions.append(plan)

    def execute(self):
        """اجرای برنامهٔ فعلی"""
        if not self.intentions:
            return

        plan = self.intentions[0]
        for step in plan.steps:
            print(f"🔧 اجرای گام: {step}")
            time.sleep(0.5)

        self.intentions.pop(0)

    def run_cycle(self):
        """حلقهٔ اصلی BDI — مثل مغز یک عامل"""
        self.deliberate()
        self.execute()
```

**مقایسهٔ Reactive در برابر Deliberative:**

| معیار | Reactive | Deliberative (BDI) |
|-------|----------|-------------------|
| **حافظه** | ❌ ندارد | ✅ مدل صریح از جهان (Beliefs) |
| **برنامه‌ریزی** | ❌ بدون برنامه | ✅ برنامه‌ریزی صریح (Intentions) |
| **سرعت** | ⚡ بالا | 🐢 پایین‌تر (هزینهٔ استدلال) |
| **انعطاف‌پذیری** | ❌ کم | ✅ زیاد |
| **پیچیدگی** | 🔧 ساده | 🏗️ پیچیده |
| **مناسب برای** | کارهای ساده و تکراری | کارهای پیچیده و استراتژیک |

### ۱.۳ معماری ترکیبی (Hybrid Architecture)

معماری **ترکیبی (Hybrid)** قوی‌ترین نقاط Reactive و Deliberative را با هم تلفیق می‌کند: یک **لایهٔ واکنشی سریع (Reactive Layer)** برای پاسخ‌های فوری و یک **لایهٔ استدلالی (Deliberative Layer)** برای برنامه‌ریزی بلندمدت.

```text
┌──────────────────────────────────────────────────────┐
│              Hybrid Agent Architecture                  │
│                                                        │
│  ┌─────────────────────────────────────────────┐      │
│  │        Deliberative Layer (استدلالی)          │      │
│  │  ┌────────┐ ┌────────┐ ┌────────────────┐   │      │
│  │  │Planner │ │Scheduler│ │ World Model   │   │      │
│  │  └────────┘ └────────┘ └────────────────┘   │      │
│  └────────────────────┬────────────────────────┘      │
│                       │                                │
│  ┌────────────────────▼────────────────────────┐      │
│  │         Control Layer (کنترل)                 │      │
│  │  مدیریت تعارض، اولویت‌بندی، زمان‌بندی         │      │
│  └────────────────────┬────────────────────────┘      │
│                       │                                │
│  ┌────────────────────▼────────────────────────┐      │
│  │         Reactive Layer (واکنشی)               │      │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐   │      │
│  │  │Condition │ │ Reflex   │ │ Emergency  │   │      │
│  │  │→ Action  │ │ Handlers │ │ Responses  │   │      │
│  │  └──────────┘ └──────────┘ └────────────┘   │      │
│  └────────────────────┬────────────────────────┘      │
│                       │                                │
│                       ▼                                │
│                 ┌──────────────┐                       │
│                 │ Environment  │                       │
│                 │ (محیط)      │                       │
│                 └──────────────┘                       │
└──────────────────────────────────────────────────────┘
```

**لایه‌های معماری ترکیبی:**

| لایه | سرعت | وظیفه | مثال |
|------|------|-------|------|
| **Reactive Layer** | ⚡ میلی‌ثانیه | واکنش‌های فوری به محرک‌های بحرانی | ترمز اضطراری در خودروی خودران |
| **Control Layer** | ⏱️ ده‌ها میلی‌ثانیه | هماهنگی بین لایه‌ها، تفکیک تعارض | تصمیم‌گیری کدام لایه پاسخ دهد |
| **Deliberative Layer** | 🐢 ثانیه تا دقیقه | برنامه‌ریزی بلندمدت، استدلال عمیق | برنامه‌ریزی مسیر سفر |

> **نکته:** معماری ترکیبی اساس بسیاری از سیستم‌های رباتیک مدرن (مثل ROS — Robot Operating System) و سیستم‌های خودران (خودروهای تسلا، هواپیماهای بدون سرنشین) است.

```python
class HybridAgent:
    """عامل ترکیبی با لایهٔ واکنشی و استدلالی"""

    def __init__(self):
        # لایهٔ واکنشی — اولویت بالا، پاسخ فوری
        self.reflexes = {
            "collision_imminent": self._emergency_brake,
            "overheating":         self._shutdown_protect,
        }
        # لایهٔ استدلالی — برنامه‌ریزی بلندمدت
        self.planner = LongTermPlanner()
        self.current_plan = []

    def sense(self, input_data: dict):
        """حلقهٔ اصلی ادراک → تصمیم → اقدام"""
        # گام ۱: بررسی واکنش‌های فوری (Reactive)
        for trigger, reflex_action in self.reflexes.items():
            if input_data.get(trigger):
                reflex_action(input_data)
                return  # واکنش فوری، نیازی به استدلال نیست

        # گام ۲: بررسی نیاز به برنامه‌ریزی مجدد (Deliberative)
        if self._plan_needs_update(input_data):
            self.current_plan = self.planner.create_plan(
                goal=input_data.get("goal"),
                context=input_data
            )

        # گام ۳: اجرای گام بعدی برنامه
        if self.current_plan:
            next_step = self.current_plan.pop(0)
            self._execute_step(next_step)

    def _emergency_brake(self, data):
        print("🛑 ترمز اضطراری! — واکنش فوری")

    def _shutdown_protect(self, data):
        print("🌡️ خاموشی محافظتی — دمای بحرانی!")
```

---

## ۲. معماری‌های مدرن مبتنی بر LLM (Modern LLM-Based Architectures)

با ظهور **مدل‌های زبانی بزرگ (Large Language Models / LLMs)**، نسل جدیدی از معماری‌های عامل شکل گرفت که در آنها LLM نقش «مغز» مرکزی را ایفا می‌کند — بر خلاف معماری‌های کلاسیک که منطق تصمیم‌گیری با کدهای صریح (explicit code) نوشته می‌شد.

### ۲.۱ معماری ReAct — Reasoning + Acting

معماری **ReAct** که در سال ۲۰۲۳ توسط Yao و همکاران معرفی شد، از مشهورترین و پرکاربردترین معماری‌های LLM-based است. ایدهٔ اصلی: **تناوب بین استدلال (Reasoning) و اقدام (Acting)** در یک حلقه.

```text
┌──────────────────────────────────────────────────────────┐
│                   ReAct Architecture                       │
│                                                           │
│   ┌───────────┐                                           │
│   │  ورودی    │  "دمای تهران چند درجه است؟"                │
│   │  (Input)  │                                           │
│   └─────┬─────┘                                           │
│         ▼                                                 │
│   ┌─────────────────────────────────────────────────┐    │
│   │         ReAct Loop (حلقهٔ اصلی)                  │    │
│   │                                                  │    │
│   │   ┌─────────────────────────────────┐            │    │
│   │   │  THOUGHT (استدلال)              │            │    │
│   │   │  "باید دمای تهران را پیدا کنم.   │            │    │
│   │   │   از ابزار جستجوی آب‌وهوا        │            │    │
│   │   │   استفاده می‌کنم."              │            │    │
│   │   └─────────────┬───────────────────┘            │    │
│   │                 ▼                                │    │
│   │   ┌─────────────────────────────────┐            │    │
│   │   │  ACTION (اقدام)                  │            │    │
│   │   │  weather_search(city="Tehran")   │            │    │
│   │   └─────────────┬───────────────────┘            │    │
│   │                 ▼                                │    │
│   │   ┌─────────────────────────────────┐            │    │
│   │   │  OBSERVATION (مشاهده)           │            │    │
│   │   │  {temp: 38°C, condition: sunny} │            │    │
│   │   └─────────────┬───────────────────┘            │    │
│   │                 │                                │    │
│   │        ┌────────┴────────┐                       │    │
│   │        ▼                 ▼                       │    │
│   │   ┌──────────┐    ┌──────────┐                   │    │
│   │   │ ادامه    │    │ پاسخ    │                   │    │
│   │   │ حلقه    │    │ نهایی   │                   │    │
│   │   └──────────┘    └──────────┘                   │    │
│   └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**سه مرحلهٔ حلقهٔ ReAct با جزئیات کامل:**

```python
"""
ReAct Loop — پیاده‌سازی مفهومی

حلقه از سه فاز تشکیل شده:
Phase 1 — Thought:  LLM ورودی + تاریخچه را تحلیل می‌کند
Phase 2 — Action:   یک ابزار مشخص با آرگومان‌های معین فراخوانی می‌شود
Phase 3 — Observation: نتیجه به LLM بازگردانده می‌شود

شرط خروج: LLM به "Final Answer" می‌رسد یا max_iterations تمام می‌شود
"""
import json
from typing import List, Dict, Optional

class ReActAgent:
    """پیاده‌سازی مفهومی معماری ReAct"""

    def __init__(self, llm, tools: List[Dict], max_iterations: int = 10):
        self.llm = llm                    # مدل زبانی (مغز عامل)
        self.tools = tools                # ابزارهای قابل استفاده
        self.max_iterations = max_iterations
        self.scratchpad: List[str] = []   # تاریخچهٔ استدلال

    def build_prompt(self, user_input: str) -> str:
        """ساخت پرامپت کامل با توضیحات ابزارها و تاریخچه"""
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )

        prompt = f"""شما یک عامل هوشمند با دسترسی به ابزارهای زیر هستید:

{tool_descriptions}

برای پاسخ به سؤال کاربر، از قالب زیر استفاده کنید:

Thought: تحلیل وضعیت و تصمیم‌گیری برای گام بعدی
Action: نام ابزار انتخابی (از لیست بالا)
Action Input: پارامترهای ابزار به صورت JSON
Observation: نتیجهٔ ابزار

این حلقه را تا رسیدن به پاسخ نهایی ادامه دهید.
وقتی به پاسخ رسیدید، از قالب زیر استفاده کنید:

Thought: من به پاسخ رسیده‌ام
Final Answer: پاسخ نهایی

تاریخچهٔ اقدامات قبلی:
{self._format_scratchpad()}

ورودی کاربر: {user_input}
"""
        return prompt

    def _format_scratchpad(self) -> str:
        return "\n".join(self.scratchpad[-6:])  # آخرین ۶ ورود

    def run(self, user_input: str) -> str:
        """اجرای کامل حلقهٔ ReAct"""
        for iteration in range(self.max_iterations):
            # Phase 1: استدلال — LLM تصمیم می‌گیرد
            prompt = self.build_prompt(user_input)
            response = self.llm.generate(prompt)
            print(f"\n🔄 Iteration {iteration + 1}")
            print(f"   LLM Response: {response[:100]}...")

            # Phase 2: تشخیص اقدام یا پایان
            if "Final Answer" in response:
                final = response.split("Final Answer:")[-1].strip()
                self.scratchpad.append(f"Final Answer: {final}")
                return final

            # استخراج نام ابزار و ورودی
            action = self._parse_action(response)
            if not action:
                continue

            # Phase 3: اجرای ابزار
            print(f"   ⚡ Action: {action['name']}({action['input']})")
            result = self._execute_tool(action['name'], action['input'])
            print(f"   👁️ Observation: {result[:80]}...")

            # ذخیره در تاریخچه
            self.scratchpad.append(
                f"Thought: ...\nAction: {action['name']}\n"
                f"Action Input: {action['input']}\n"
                f"Observation: {result}"
            )

        return "⚠️ به حداکثر تعداد تکرار رسیدم."

    def _parse_action(self, response: str) -> Optional[Dict]:
        """استخراج نام ابزار و پارامترها از پاسخ LLM"""
        # در عمل: regex یا JSON parsing
        if "Action:" not in response:
            return None
        lines = response.split("\n")
        action_line = [l for l in lines if l.startswith("Action:")][0]
        input_line = [l for l in lines if l.startswith("Action Input:")][0]
        return {
            "name": action_line.replace("Action:", "").strip(),
            "input": json.loads(input_line.replace("Action Input:", "").strip())
        }

    def _execute_tool(self, name: str, args: dict) -> str:
        """یافتن و اجرای ابزار مناسب"""
        for tool in self.tools:
            if tool['name'] == name:
                return tool['function'](**args)
        return f"ERROR: ابزار '{name}' یافت نشد"
```

**ویژگی‌های کلیدی ReAct:**

| ویژگی | توضیح |
|--------|-------|
| **شفافیت (Transparency)** | تمام مراحل استدلال قابل مشاهده است (Scratchpad) |
| **انعطاف‌پذیری (Flexibility)** | مسیر تصمیم‌گیری بر اساس نتایج میانی تغییر می‌کند |
| **قابلیت رفع خطا (Correctability)** | اگر اقدامی خطا داد، LLM می‌تواند مسیر جایگزین انتخاب کند |
| **هزینهٔ Token** | بالا — هر دور حلقه یک فراخوانی کامل LLM |
| **سرعت** | پایین‌تر — به دلیل فراخوانی متوالی LLM |

### ۲.۲ معماری Plan-and-Execute

معماری **Plan-and-Execute** که از مقالهٔ «Plan-and-Solve Prompting» (Wang et al., 2023) نشأت گرفته، استدلال را به دو فاز مجزا تفکیک می‌کند: **برنامه‌ریزی (Planning)** و **اجرا (Execution)**.

> **تفاوت کلیدی با ReAct:** در ReAct، استدلال و اقدام در هم تنیده شده‌اند. در Plan-and-Execute، ابتدا یک برنامهٔ کامل تولید می‌شود، سپس اجرا می‌گردد.

```text
┌──────────────────────────────────────────────────────┐
│              Plan-and-Execute Architecture              │
│                                                        │
│  ┌──────────────────┐                                  │
│  │   User Input     │  "یک مقاله درباره AI بنویس"     │
│  └────────┬─────────┘                                  │
│           ▼                                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │  PHASE 1: PLANNING (برنامه‌ریزی)                 │  │
│  │                                                  │  │
│  │  ┌──────────────────────┐                       │  │
│  │  │      Planner LLM     │  مدل قوی (Claude, GPT-4)│  │
│  │  │ (برنامه‌ریز)        │                       │  │
│  │  └──────────┬───────────┘                       │  │
│  │             ▼                                   │  │
│  │  ┌──────────────────────┐                       │  │
│  │  │  Plan: List of Steps │                       │  │
│  │  │  1. Search AI trends │                       │  │
│  │  │  2. Find key papers  │                       │  │
│  │  │  3. Draft outline    │                       │  │
│  │  │  4. Write sections   │                       │  │
│  │  │  5. Review & polish  │                       │  │
│  │  └──────────────────────┘                       │  │
│  └─────────────────────────────────────────────────┘  │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │  PHASE 2: EXECUTION (اجرا)                      │  │
│  │                                                  │  │
│  │  Step 1 ──▶ Step 2 ──▶ Step 3 ──▶ Step 4 ──▶ Step 5│  │
│  │   │            │            │            │       │  │
│  │   ▼            ▼            ▼            ▼       │  │
│  │  ┌──┐        ┌──┐        ┌──┐        ┌──┐      │  │
│  │  │Tool│      │Tool│      │LLM │      │LLM │      │  │
│  │  │A   │      │B   │      │C   │      │D   │      │  │
│  │  └──┘        └──┘        └──┘        └──┘      │  │
│  └─────────────────────────────────────────────────┘  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │   Final Output   │  مقالهٔ نهایی                    │
│  └──────────────────┘                                  │
└──────────────────────────────────────────────────────┘
```

**پیاده‌سازی مفهومی Plan-and-Execute:**

```python
from typing import List, Dict, Callable
import time

class PlanAndExecuteAgent:
    """عامل Plan-and-Execute — جداسازی برنامه‌ریزی از اجرا"""

    def __init__(self, planner_llm, worker_llm=None):
        self.planner = planner_llm    # LLM قوی برای برنامه‌ریزی
        self.worker = worker_llm or planner_llm  # LLM برای اجرا
        self.plan: List[str] = []
        self.results: Dict[int, str] = {}

    def plan_phase(self, goal: str) -> List[str]:
        """فاز ۱: برنامه‌ریزی — LLM یک برنامهٔ گام‌به‌گام می‌نویسد"""
        prompt = f"""هدف: {goal}

یک برنامهٔ گام‌به‌گام برای رسیدن به این هدف بنویس.
هر گام باید مشخص و قابل اندازه‌گیری باشد.
خروجی را به صورت لیست شماره‌دار برگردان."""

        plan_text = self.planner.generate(prompt)
        # استخراج گام‌ها از متن
        self.plan = self._parse_steps(plan_text)
        print(f"📋 Plan ({len(self.plan)} steps):")
        for i, step in enumerate(self.plan, 1):
            print(f"   {i}. {step}")
        return self.plan

    def execute_phase(self):
        """فاز ۲: اجرا — گام‌ها یکی‌یکی اجرا می‌شوند"""
        for i, step in enumerate(self.plan):
            print(f"\n🔧 Executing step {i+1}: {step}")
            result = self._execute_step(step)
            self.results[i] = result
            print(f"   ✅ Result: {result[:100]}...")
            time.sleep(0.1)

    def _parse_steps(self, text: str) -> List[str]:
        lines = text.strip().split("\n")
        steps = []
        for line in lines:
            cleaned = line.strip()
            # حذف شماره‌گذاری
            if cleaned and (cleaned[0].isdigit() or cleaned.startswith("-")):
                step = cleaned.split(". ", 1)[-1] if ". " in cleaned else cleaned
                step = step.lstrip("- ")
                steps.append(step)
        return steps

    def _execute_step(self, step: str) -> str:
        """اجرای یک گام — می‌تواند فراخوانی LLM یا ابزار باشد"""
        # شبیه‌سازی اجرا
        return f"اجرای «{step}» با موفقیت انجام شد."

    def run(self, goal: str) -> Dict:
        """اجرای کامل دو فازی"""
        print("=" * 50)
        print("🚀 Plan-and-Execute Agent")
        print("=" * 50)

        self.plan_phase(goal)
        self.execute_phase()

        return {"plan": self.plan, "results": self.results}
```

**مقایسهٔ ReAct و Plan-and-Execute:**

| معیار | ReAct | Plan-and-Execute |
|-------|-------|------------------|
| **زمان‌بندی استدلال** | همزمان با اجرا | پیش از اجرا |
| **تعداد فراخوانی LLM** | ۱+ در هر گام (زیاد) | ۱ بار برنامه‌ریزی + بهینه |
| **انعطاف در برابر تغییر** | ✅ بالا (تطبیق پویا) | ⚠️ متوسط (نیاز به بازبرنامه‌ریزی) |
| **شفافیت برنامه** | متوسط (استدلال ضمنی) | ✅ بالا (برنامهٔ صریح) |
| **بهترین برای** | وظایف اکتشافی (Exploratory) | وظایف با ساختار مشخص (Structured) |

### ۲.۳ معماری Tree-of-Thoughts (ToT)

معماری **Tree-of-Thoughts (درخت افکار)** که در سال ۲۰۲۳ توسط Yao و همکاران ارائه شد، استدلال Chain-of-Thought را به یک **درخت جستجو (Search Tree)** تعمیم می‌دهد. به جای یک مسیر خطی از افکار، LLM چندین شاخهٔ فکری موازی تولید می‌کند و بهترین مسیر را انتخاب می‌نماید.

> **تشبیه برای مخاطب ایرانی:** مثل یک **شطرنج‌باز حرفه‌ای** که قبل از حرکت، چندین حالت مختلف را در ذهن خود شبیه‌سازی می‌کند («اگر من این حرکت را بکنم، حریف چه پاسخی می‌دهد؟...») و بهترین گزینه را انتخاب می‌کند.

```text
┌────────────────────────────────────────────────────────────┐
│              Tree-of-Thoughts (ToT) Architecture              │
│                                                              │
│                    ┌──── ROOT ────┐                          │
│                   /        |        \                        │
│                  ▼        ▼         ▼                        │
│             ┌────────┐ ┌────────┐ ┌────────┐                │
│             │Thought │ │Thought │ │Thought │   ← سطح ۱:     │
│             │  A1    │ │  A2    │ │  A3    │     تولید k ایده│
│             └───┬────┘ └───┬────┘ └───┬────┘                │
│                / \        / \        / \                    │
│               ▼   ▼      ▼   ▼      ▼   ▼                  │
│          ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│          │B1  │ │B2  │ │B3  │ │B4  │ │B5  │ │B6  │ ← سطح ۲:│
│          │    │ │    │ │    │ │    │ │    │ │    │   گسترش  │
│          └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘       │
│            │      │      │      │      │      │            │
│            ▼      ▼      ▼      ▼      ▼      ▼            │
│         ┌────────────────────────────┐                     │
│         │  ارزیابی (Evaluation)       │                     │
│         │  BFS یا DFS برای انتخاب    │                     │
│         │  بهترین مسیر               │                     │
│         └─────────────┬──────────────┘                     │
│                       ▼                                    │
│                ┌──────────────┐                            │
│                │  Final Path  │  "مسیر بهینه انتخاب‌شده"    │
│                └──────────────┘                            │
└────────────────────────────────────────────────────────────┘
```

| مؤلفه ToT | توضیح | مثال |
|-----------|-------|------|
| **Thought Decomposition** | شکستن مسئله به گام‌های فکری مجزا | هر «فکر» یک حرکت در مسئله |
| **Thought Generation** | تولید چندین فکر ممکن در هر گام | k = ۵ گزینه مختلف |
| **State Evaluation** | ارزیابی هر گره (node) از درخت | امتیاز ۰ تا ۱۰ |
| **Search Algorithm** | الگوریتم جستجو (BFS یا DFS) | BFS برای عمق کم، DFS برای عمق زیاد |

```python
import heapq
from typing import List, Callable, Optional

class TreeOfThoughts:
    """پیاده‌سازی مفهومی Tree-of-Thoughts"""

    def __init__(self, llm, max_branches: int = 3, max_depth: int = 5):
        self.llm = llm
        self.k = max_branches       # تعداد شاخه‌ها در هر گره
        self.max_depth = max_depth  # حداکثر عمق درخت

    def solve(self, problem: str) -> List[str]:
        """حل مسئله با جستجوی درختی بهترین-اول (Best-First Search)"""
        # هر گره: (اولویت، عمق، مسیر، حالت)
        start_state = f"مسئله: {problem}\nقدم اول: "
        heap = [(0, 0, [start_state], start_state)]
        best_path = []

        while heap:
            priority, depth, path, state = heapq.heappop(heap)

            if depth >= self.max_depth:
                best_path = path
                break

            # تولید k فکر جدید
            next_thoughts = self._generate_thoughts(state)

            for thought in next_thoughts:
                new_state = state + f"\n→ {thought}"
                score = self._evaluate_thought(new_state)
                new_path = path + [thought]

                # اگر امتیاز خوب بود، به heap اضافه کن
                if score > 0.7:  # آستانهٔ قبول
                    heapq.heappush(heap, (-score, depth + 1, new_path, new_state))

        return best_path or ["مسیری یافت نشد"]

    def _generate_thoughts(self, state: str) -> List[str]:
        """تولید k فکر جدید از وضعیت فعلی"""
        prompt = f"""با توجه به وضعیت فعلی:
{state}

{self.k} گام بعدی محتمل و منطقی تولید کن.
هر گام در یک خط جدا."""

        response = self.llm.generate(prompt)
        thoughts = [t.strip() for t in response.split("\n") if t.strip()]
        return thoughts[:self.k]

    def _evaluate_thought(self, state: str) -> float:
        """ارزیابی یک گره از درخت — امتیاز ۰ تا ۱"""
        prompt = f"""این مسیر فکری را ارزیابی کن:
{state}

امتیاز ۰ تا ۱ بده (فقط عدد)."""
        score_text = self.llm.generate(prompt)
        try:
            return float(score_text.strip()[:4])
        except ValueError:
            return 0.5  # میانگین در صورت خطا
```

**کاربردهای ToT:**

| حوزه | مثال |
|------|------|
| **حل مسئلهٔ ریاضی** | بازیابی ۲۴ با چهار عدد — LLM شاخه‌های مختلف عملیات را بررسی می‌کند |
| **برنامه‌ریزی** | تولید چندین برنامهٔ سفر و انتخاب بهترین |
| **خلاقیت** | نوشتن داستان با چندین مسیر روایی مختلف |
| **تصمیم‌گیری استراتژیک** | تحلیل چندین سناریوی تجاری و انتخاب بهترین |

### ۲.۴ معماری Reflection (Reflexion)

معماری **Reflection (بازاندیشی)** که در مقالهٔ «Reflexion: Language Agents with Verbal Reinforcement Learning» (Shinn et al., 2023) معرفی شد، به عامل اجازه می‌دهد از **اشتباهات خود درس بگیرد** و در دفعات بعدی بهتر عمل کند.

> **ایدهٔ اصلی:** عامل علاوه بر اجرای وظیفه، یک **حافظهٔ متنی (Textual Memory)** از شکست‌ها و درس‌های خود نگه می‌دارد و قبل از هر اقدام جدید، به این حافظه رجوع می‌کند.

```text
┌─────────────────────────────────────────────────────────┐
│              Reflexion Architecture                       │
│                                                           │
│  ┌──────────┐                                            │
│  │  Task    │  ورودی: "یک API بنویس که..."                │
│  └────┬─────┘                                            │
│       ▼                                                  │
│  ┌─────────────────────────────────────────────────┐     │
│  │           Actor (بازیگر — عامل اصلی)             │     │
│  │  ┌────────────────────────────────────────┐     │     │
│  │  │                                       │     │     │
│  │  │  ┌─────────┐  ┌─────────┐  ┌────────┐│     │     │
│  │  │  │ Thought │─▶│ Action  │─▶│Observ. ││     │     │
│  │  │  └─────────┘  └─────────┘  └────────┘│     │     │
│  │  └────────────────────────────────────────┘     │     │
│  └────────────────────┬────────────────────────────┘     │
│                       │                                   │
│         ┌─────────────┴─────────────┐                     │
│         ▼                           ▼                     │
│  ┌──────────────┐          ┌────────────────┐            │
│  │   Evaluator  │          │   Self-Reflect │            │
│  │  (ارزیاب)    │          │  (بازاندیش)    │            │
│  │  بررسی       │          │  تحلیل علت     │            │
│  │  موفقیت/    │          │  شکست و تولید  │            │
│  │  شکست       │          │  درس            │            │
│  └──────┬───────┘          └───────┬────────┘            │
│         │                          │                      │
│         └──────────┬───────────────┘                      │
│                    ▼                                      │
│  ┌──────────────────────────────────┐                    │
│  │        Memory (حافظه)            │                    │
│  │  "دفعه قبل خطا: تایپو در نام     │                    │
│  │   تابع. درس: همیشه از type hints │                    │
│  │   و Pydantic validation استفاده  │                    │
│  │   کن."                           │                    │
│  └──────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

**چهار مؤلفهٔ Reflexion:**

| مؤلفه | وظیفه |
|-------|-------|
| **Actor** | عامل اصلی — وظیفه را اجرا می‌کند (می‌تواند ReAct باشد) |
| **Evaluator** | ارزیاب — تشخیص موفقیت یا شکست (بر اساس تست‌ها، بازخورد کاربر، یا LLM) |
| **Self-Reflection** | بازاندیش — تحلیل علت خطا و تولید یک «درس» متنی |
| **Memory** | حافظه — ذخیرهٔ درس‌های قبلی برای استفاده در آینده |

```python
class ReflexionAgent:
    """عامل با قابلیت بازاندیشی (Self-Reflection)"""

    def __init__(self, actor, evaluator):
        self.actor = actor              # عامل اجرایی (مثلاً ReAct)
        self.evaluator = evaluator      # ارزیاب موفقیت
        self.memory: List[str] = []     # حافظهٔ درس‌ها

    def run_with_reflexion(self, task: str, max_attempts: int = 3) -> str:
        """اجرای وظیفه با قابلیت یادگیری از خطا"""
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔄 Attempt {attempt}/{max_attempts}")

            # تزریق حافظه به Actor
            context = self._build_context(task)
            result = self.actor.run(context)

            # ارزیابی نتیجه
            is_success, feedback = self.evaluator.evaluate(result, task)

            if is_success:
                print(f"✅ موفقیت در تلاش {attempt}")
                return result

            # بازاندیشی — تولید درس از شکست
            lesson = self._reflect(feedback, result)
            self.memory.append(lesson)
            print(f"📝 درس ثبت‌شده: {lesson[:100]}...")

        return f"❌ شکست پس از {max_attempts} تلاش. درس‌ها: {self.memory}"

    def _build_context(self, task: str) -> str:
        """ساخت context با تزریق حافظهٔ درس‌ها"""
        memory_text = ""
        if self.memory:
            memory_text = "درس‌های قبلی (حتماً رعایت کن):\n"
            for i, lesson in enumerate(self.memory[-5:], 1):
                memory_text += f"{i}. {lesson}\n"

        return f"{memory_text}\nوظیفهٔ فعلی: {task}"

    def _reflect(self, feedback: str, result: str) -> str:
        """تحلیل خطا و تولید درس"""
        prompt = f"""نتیجه: {result}
بازخورد: {feedback}

تحلیل کن چرا این اقدام شکست خورد و یک درس قابل استفاده برای دفعه بعد بنویس.
درس باید مشخص، عملی، و قابل تکرار باشد."""
        return self.actor.llm.generate(prompt)
```

### ۲.۵ معماری Mixture-of-Agents (MoA)

معماری **Mixture-of-Agents (ترکیب عامل‌ها)** که در سال ۲۰۲۴ توسط Wang و همکاران در مقاله‌ای از Salesforce AI Research معرفی شد، از **چندین عامل تخصصی (specialized agents)** به صورت موازی استفاده می‌کند تا خروجی نهایی از **ترکیب (aggregation)** خروجی‌های آنها حاصل شود.

> **ایدهٔ اصلی:** مثل یک **پانل تخصصی (Panel of Experts)** — چند متخصص هرکدام از زاویهٔ خود به مسئله نگاه می‌کنند و سپس یک «گردآورنده» بهترین پاسخ‌ها را ترکیب می‌کند.

```text
┌──────────────────────────────────────────────────────────┐
│            Mixture-of-Agents (MoA) Architecture            │
│                                                           │
│                     ┌──────────┐                          │
│                     │  Query   │                          │
│                     └────┬─────┘                          │
│                          │                                │
│         ┌────────────────┼────────────────┐              │
│         ▼                ▼                ▼              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Agent A   │  │  Agent B   │  │  Agent C   │        │
│  │ تخصص: کدنویسی│  │ تخصص: مستند│  │ تخصص: تست │        │
│  │ (LLM=GPT-4) │  │ (LLM=Sonnet)│  │ (LLM=Haiku)│        │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │
│         │               │               │                │
│         ▼               ▼               ▼                │
│  ┌──────────────────────────────────────────────┐       │
│  │         Aggregate Layer (لایهٔ ترکیب)         │       │
│  │                                               │       │
│  │  Proposer Agent: هر عامل پاسخ مستقل می‌دهد    │       │
│  │  Aggregator Agent: بهترین پاسخ‌ها را ترکیب    │       │
│  │  می‌کند و خروجی نهایی را تولید می‌نماید       │       │
│  └──────────────────────┬───────────────────────┘       │
│                         ▼                                │
│                  ┌──────────────┐                        │
│                  │ Final Output │                        │
│                  └──────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

**انواع معماری MoA:**

| نوع | توضیح | مزیت |
|-----|-------|------|
| **MoA ساده** | همهٔ Agentها یک ورودی می‌گیرند، خروجی ترکیب می‌شود | سادگی، تنوع پاسخ |
| **MoA لایه‌ای (Layered)** | خروجی یک لایه ورودی لایهٔ بعد می‌شود | بهبود تدریجی کیفیت |
| **MoA با Routing** | Router مشخص می‌کند کدام Agent مناسب‌تر است | صرفه‌جویی در هزینه |

```python
from typing import List, Dict, Callable
import concurrent.futures

class MixtureOfAgents:
    """معماری ترکیب عامل‌ها (MoA) — اجرای موازی و ترکیب نتایج"""

    def __init__(self, agents: List[Dict], aggregator_llm):
        """
        agents: لیست agentها با مشخصات
        aggregator_llm: LLM که خروجی‌ها را ترکیب می‌کند
        """
        self.agents = agents
        self.aggregator = aggregator_llm

    def run(self, query: str) -> str:
        """اجرای موازی همهٔ Agentها و ترکیب نتایج"""

        # فاز ۱: اجرای موازی همهٔ Agentها
        print(f"🚀 Running {len(self.agents)} agents in parallel...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._run_agent, agent, query): agent['name']
                for agent in self.agents
            }
            results = {}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                print(f"   ✅ {name} completed")

        # فاز ۲: ترکیب نتایج
        print("\n🔄 Aggregating results...")
        final = self._aggregate(query, results)
        return final

    def _run_agent(self, agent: Dict, query: str) -> str:
        """اجرای یک Agent تخصصی"""
        prompt = f"""شما یک {agent['role']} هستید.
تخصص شما: {agent['expertise']}

به سؤال زیر از منظر تخصص خود پاسخ دهید:
{query}

پاسخ مختصر و دقیق بدهید."""
        return agent['llm'].generate(prompt)

    def _aggregate(self, query: str, results: Dict[str, str]) -> str:
        """ترکیب خروجی‌های Agentها برای تولید پاسخ نهایی"""
        responses_text = "\n\n".join([
            f"**{name}**:\n{response}"
            for name, response in results.items()
        ])
        prompt = f"""سؤال اصلی: {query}

پاسخ‌های متخصصان مختلف:
{responses_text}

نقش شما: پاسخ‌های بالا را ترکیب کن و یک پاسخ جامع، دقیق و منسجم تولید کن.
نقاط قوت هر پاسخ را حفظ کن و تضادها را برطرف کن."""

        return self.aggregator.generate(prompt)
```

**مزایای MoA:**

| مزیت | توضیح |
|------|-------|
| **تنوع (Diversity)** | هر Agent از زاویهٔ متفاوتی به مسئله نگاه می‌کند |
| **تاب‌آوری (Resilience)** | اگر یک Agent ضعیف عمل کند، بقیه جبران می‌کنند |
| **مقیاس‌پذیری (Scalability)** | به راحتی می‌توان Agent تخصصی جدید اضافه کرد |
| **کیفیت (Quality)** | ترکیب چند دیدگاه معمولاً از یک دیدگاه بهتر است |

---

## ۳. لایه‌های معماری (Architectural Layers)

هر عامل هوش مصنوعی — صرف‌نظر از معماری — از **لایه‌های مفهومی (Conceptual Layers)** مشخصی تشکیل شده است. درک این لایه‌ها برای طراحی معماری‌های پیچیده ضروری است.

```text
┌─────────────────────────────────────────────────────┐
│           لایه‌های معماری عامل (Architectural Layers)  │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Layer 1: Perception (ادراک)                 │    │
│  │  دریافت و پردازش ورودی از محیط               │    │
│  │  ─────────────────────────────────           │    │
│  │  متن، صوت، تصویر، حسگرها، API calls          │    │
│  └──────────────────┬──────────────────────────┘    │
│                     ▼                                │
│  ┌─────────────────────────────────────────────┐    │
│  │  Layer 2: Reasoning / Planning (استدلال)     │    │
│  │  تحلیل، برنامه‌ریزی، تصمیم‌گیری              │    │
│  │  ─────────────────────────────────           │    │
│  │  LLM, Chain-of-Thought, BDI, Rules          │    │
│  └──────────────────┬──────────────────────────┘    │
│                     ▼                                │
│  ┌─────────────────────────────────────────────┐    │
│  │  Layer 3: Memory (حافظه)                     │    │
│  │  ذخیره و بازیابی اطلاعات                     │    │
│  │  ─────────────────────────────────           │    │
│  │  Short-term, Long-term, Episodic, Semantic  │    │
│  └──────────────────┬──────────────────────────┘    │
│                     ▼                                │
│  ┌─────────────────────────────────────────────┐    │
│  │  Layer 4: Action / Tools (اقدام)            │    │
│  │  تعامل با جهان خارج                          │    │
│  │  ─────────────────────────────────           │    │
│  │  API calls, Code execution, MCP, Files      │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### ۳.۱ لایهٔ ادراک (Perception Layer)

اولین لایه‌ای که با جهان خارج تعامل دارد. وظیفه: **تبدیل داده‌های خام به بازنمایی قابل فهم برای عامل**.

| نوع ورودی | ابزارهای پردازش | چالش‌ها |
|-----------|----------------|---------|
| **متن (Text)** | Tokenizer, Embedding | طول محدود context |
| **تصویر (Image)** | Vision Encoder (CLIP, ViT) | حجم بالا |
| **صوت (Audio)** | Speech-to-Text (Whisper) | نویز محیط |
| **ساختاریافته (Structured)** | JSON Parser, Schema Validator | ناهماهنگی فرمت |
| **حسگر (Sensor)** | Signal Processing | Latency |

```python
class PerceptionLayer:
    """لایهٔ ادراک — تبدیل ورودی‌های خام به بازنمایی داخلی"""

    def __init__(self):
        self.encoders = {
            "text":  TextEncoder(),
            "image": ImageEncoder(),
            "audio": AudioEncoder(),
        }

    def process(self, raw_input: Dict) -> Dict:
        """پردازش و نرمال‌سازی ورودی"""
        processed = {}
        for modality, data in raw_input.items():
            if modality in self.encoders:
                processed[modality] = self.encoders[modality].encode(data)
            else:
                processed[modality] = data  # عبور مستقیم
        return processed
```

### ۳.۲ لایهٔ استدلال و برنامه‌ریزی (Reasoning / Planning Layer)

مغز عامل. این لایه **تصمیم می‌گیرد که下一步 چه کاری انجام دهد**. در معماری‌های مدرن، این لایه توسط **LLM** اداره می‌شود.

| الگوی استدلال | مکانیسم | هزینه | سرعت |
|--------------|---------|-------|------|
| **Direct (مستقیم)** | یک بار LLM | کم | ⚡⚡ |
| **Chain-of-Thought** | استدلال گام‌به‌گام | متوسط | ⚡ |
| **ReAct Loop** | حلقهٔ استدلال + اقدام | زیاد | 🐢 |
| **Tree-of-Thoughts** | جستجوی درختی | خیلی زیاد | 🐢🐢 |
| **Plan-and-Execute** | برنامه‌ریزی → اجرا | متوسط | ⚡ |

### ۳.۳ لایهٔ حافظه (Memory Layer)

عامل‌ها برای رفتار هوشمندانه به **حافظه** نیاز دارند. حافظه در عامل‌های مدرن به چند دسته تقسیم می‌شود:

| نوع حافظه | duration | مکانیسم | مثال |
|-----------|----------|---------|------|
| **حافظهٔ کوتاه‌مدت (Short-term)** | یک مکالمه | Context Window | پیام‌های جاری در ChatGPT |
| **حافظهٔ بلندمدت (Long-term)** | بین جلسات | Vector DB | ChromaDB, Pinecone |
| **حافظهٔ رویدادی (Episodic)** | طولانی | Structured Log | تاریخچهٔ اقدامات موفق/ناموفق |
| **حافظهٔ معنایی (Semantic)** | دائمی | Knowledge Graph | قوانین، facts |

```python
class MemoryLayer:
    """لایهٔ حافظه — سه سطح حافظه"""

    def __init__(self):
        self.short_term = []        # buffer محدود
        self.long_term = VectorDB()  # FAISS / ChromaDB
        self.episodic = []           # تاریخچهٔ رویدادها

    def add_short_term(self, item: str, max_items: int = 10):
        self.short_term.append(item)
        if len(self.short_term) > max_items:
            self.short_term.pop(0)  # FIFO

    def add_long_term(self, item: str, metadata: dict = None):
        self.long_term.add(item, metadata)

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """بازیابی ترکیبی — اول short-term بعد long-term"""
        # جستجوی کوتاه‌مدت
        st_results = [m for m in self.short_term if query in m]

        # جستجوی بلندمدت (semantic)
        lt_results = self.long_term.search(query, top_k)

        return st_results + lt_results
```

### ۳.۴ لایهٔ اقدام و ابزار (Action / Tool Layer)

این لایه پل ارتباطی عامل با **جهان خارج** است. هر اقدامی که عامل انجام می‌دهد — فراخوانی API، اجرای کد، ارسال ایمیل — از این لایه عبور می‌کند.

```text
┌──────────────────────────────────────────────────┐
│              Action / Tool Layer                   │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  MCP    │  │  HTTP   │  │  Code        │   │
│  │  Client  │  │  Client  │  │  Interpreter │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  File    │  │  DB     │  │  Notification│   │
│  │  System  │  │  Query  │  │  Service     │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                    │
└──────────────────────────────────────────────────┘
```

---

## ۴. حالت ماشین در برابر معماری گراف (State Machines vs Graph-Based)

دو رویکرد اصلی برای **مدل‌سازی جریان (Flow Modeling)** عامل‌ها وجود دارد: **حالت ماشین (State Machine)** و **گراف (Graph)**.

### ۴.۱ معماری حالت ماشین (State Machine Architecture)

در این رویکرد، عامل به عنوان یک **حالت ماشین محدود (Finite State Machine / FSM)** مدل می‌شود که از حالتی به حالت دیگر حرکت می‌کند.

```text
┌──────────────────────────────────────────────────────────┐
│              State Machine Agent Architecture               │
│                                                            │
│                    ┌──────────┐                            │
│        ┌──────────▶│   IDLE   │◀────────────────────┐     │
│        │           │ (آماده)  │                      │     │
│        │           └────┬─────┘                      │     │
│        │                │ ورودی جدید                  │     │
│        │                ▼                            │     │
│        │           ┌──────────┐                      │     │
│        │           │ PROCESS  │                      │     │
│        │           │(پردازش) │                      │     │
│        │           └────┬─────┘                      │     │
│        │            ┌───┴────┐                       │     │
│        │            ▼        ▼                       │     │
│        │    ┌──────────┐ ┌──────────┐                │     │
│        │    │ TOOL_USE │ │ REASON   │                │     │
│        │    │ (استفاده │ │ (استدلال)│                │     │
│        │    │ از ابزار)│ │          │                │     │
│        │    └─────┬────┘ └────┬─────┘                │     │
│        │          └────┬──────┘                       │     │
│        │               ▼                              │     │
│        │          ┌──────────┐                        │     │
│        └──────────│ RESPOND  │────────────────────────┘     │
│                   │ (پاسخ)   │                              │
│                   └──────────┘                              │
└──────────────────────────────────────────────────────────┘
```

**مزایا:** سادگی، قابلیت پیش‌بینی، دیباگ آسان.
**محدودیت‌ها:** انعطاف‌پذیری کم، مدیریت حالت‌های هم‌روند (concurrent) دشوار.

```python
from enum import Enum
from typing import Dict, Any

class AgentState(Enum):
    IDLE = "idle"
    PROCESS = "process"
    REASON = "reason"
    TOOL_USE = "tool_use"
    RESPOND = "respond"
    ERROR = "error"

class StateMachineAgent:
    """عامل مبتنی بر State Machine"""

    def __init__(self):
        self.state = AgentState.IDLE
        self.transitions = {
            AgentState.IDLE:    [AgentState.PROCESS],
            AgentState.PROCESS: [AgentState.REASON, AgentState.TOOL_USE],
            AgentState.REASON:  [AgentState.TOOL_USE, AgentState.RESPOND],
            AgentState.TOOL_USE: [AgentState.REASON, AgentState.RESPOND],
            AgentState.RESPOND: [AgentState.IDLE],
            AgentState.ERROR:   [AgentState.IDLE],
        }

    def transition_to(self, new_state: AgentState):
        if new_state in self.transitions[self.state]:
            print(f"🔄 {self.state.name} → {new_state.name}")
            self.state = new_state
        else:
            raise ValueError(
                f"انتقال نامعتبر: {self.state} → {new_state}"
            )
```

### ۴.۲ معماری گراف (Graph-Based Architecture — LangGraph Style)

معماری **گراف (Graph)** عامل را به عنوان یک **گراف جهت‌دار (Directed Graph)** مدل می‌کند که هر **گره (Node)** یک عملیات و هر **یال (Edge)** یک جریان داده است.

> **LangGraph** محبوب‌ترین فریم‌ورک برای معماری گراف-محور عامل‌ها است که توسط LangChain توسعه یافته.

```text
┌──────────────────────────────────────────────────────────┐
│              Graph-Based Architecture (LangGraph Style)    │
│                                                            │
│        ┌──────────────────────────────────────┐           │
│        │           State (وضعیت)               │           │
│        │  {messages: [...], next_action: ...} │           │
│        └──────────┬───────────┬───────────────┘           │
│                   │           │                            │
│         ┌─────────┘           └─────────┐                 │
│         ▼                                     ▼           │
│  ┌──────────────┐                    ┌──────────────┐    │
│  │  Node A      │                    │  Node B      │    │
│  │  (Reason)   │                    │  (Tool Call) │    │
│  └──────┬───────┘                    └──────┬───────┘    │
│         │                                   │            │
│         │       ┌────────────────────┐      │            │
│         └──────▶│  Conditional Edge  │◀─────┘            │
│                 │   (یال شرطی)       │                    │
│                 └─────────┬──────────┘                    │
│                           │                                │
│                 ┌─────────┴────────┐                      │
│                 ▼                  ▼                       │
│          ┌────────────┐    ┌────────────┐                 │
│          │  Node C    │    │    END     │                 │
│          │ (Response) │    │ (پایان)   │                 │
│          └────────────┘    └────────────┘                 │
└──────────────────────────────────────────────────────────┘
```

**مقایسهٔ State Machine و Graph:**

| ویژگی | State Machine | Graph (LangGraph) |
|-------|---------------|-------------------|
| **پیچیدگی** | 🔧 ساده | 🏗️ انعطاف‌پذیر |
| **حالت (State)** | ضمنی (implicit — موقعیت فعلی) | صریح (explicit — شیء State) |
| **یال‌های شرطی** | محدود | ✅ کامل (توابع شرط) |
| **حلقه (Loop)** | محدود (نیاز به طراحی خاص) | ✅ طبیعی (edges به عقب) |
| **هم‌روندی** | ❌ دشوار | ✅ ممکن (parallel edges) |
| **Human-in-Loop** | ❌ دشوار | ✅ built-in |
| **دیباگ** | ✅ آسان | ⚠️ متوسط |
| **مقیاس‌پذیری** | ⚠️ متوسط | ✅ بالا |

```python
"""
LangGraph-style Agent — معماری گراف محور با State مدیریت شده
"""
from typing import TypedDict, List, Callable, Dict, Any
from enum import Enum

# --- State ---
class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    next_node: str
    iteration: int
    memory: Dict[str, Any]

# --- Node types ---
NodeFunc = Callable[[AgentState], AgentState]
ConditionalEdge = Callable[[AgentState], str]

class GraphAgent:
    """عامل مبتنی بر گراف (شبیه LangGraph)"""

    def __init__(self):
        self.nodes: Dict[str, NodeFunc] = {}
        self.edges: Dict[str, Dict[str, str]] = {}
        self.conditional_edges: Dict[str, ConditionalEdge] = {}
        self.entry_point: str = ""

    def add_node(self, name: str, func: NodeFunc):
        """ثبت یک گره در گراف"""
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str):
        """یال ساده — بدون شرط"""
        if from_node not in self.edges:
            self.edges[from_node] = {}
        self.edges[from_node]["__default__"] = to_node

    def add_conditional_edge(
        self, from_node: str, condition_fn: ConditionalEdge
    ):
        """یال شرطی — تابع مشخص می‌کند به کدام گره برود"""
        self.conditional_edges[from_node] = condition_fn

    def set_entry_point(self, name: str):
        self.entry_point = name

    def run(self, initial_state: AgentState) -> AgentState:
        """اجرای گراف — از entry_point تا رسیدن به END"""
        state = initial_state
        current = self.entry_point

        max_steps = 20  # جلوگیری از حلقهٔ نامحدود
        step = 0

        while current != "END" and step < max_steps:
            print(f"\n🔄 Node: {current} (iteration: {state.get('iteration', 0)})")
            node_func = self.nodes.get(current)
            if not node_func:
                raise ValueError(f"گرهٔ '{current}' یافت نشد")

            # اجرای گره
            state = node_func(state)

            # تصمیم‌گیری برای گره بعدی
            if current in self.conditional_edges:
                next_node = self.conditional_edges[current](state)
            elif current in self.edges:
                next_node = self.edges[current].get(
                    "__default__", "END"
                )
            else:
                next_node = "END"

            current = next_node
            step += 1

        state['next_node'] = "END"
        return state


# --- مثال: گراف ReAct با LangGraph-style ---
def reason_node(state: AgentState) -> AgentState:
    """گره استدلال — LLM تصمیم می‌گیرد"""
    messages = state['messages']
    # شبیه‌سازی LLM
    last_msg = messages[-1]['content'] if messages else ""
    if "weather" in last_msg.lower():
        state['next_node'] = "call_tool"
    else:
        state['next_node'] = "respond"
    state['iteration'] += 1
    return state

def tool_node(state: AgentState) -> AgentState:
    """گره ابزار — فراخوانی API"""
    state['messages'].append({
        "role": "tool",
        "content": "🌤️ Tehran: 38°C, Sunny"
    })
    return state

def respond_node(state: AgentState) -> AgentState:
    """گره پاسخ — تولید پاسخ نهایی"""
    state['messages'].append({
        "role": "assistant",
        "content": "دمای هوای تهران ۳۸ درجه سانتی‌گراد است."
    })
    return state

def should_continue(state: AgentState) -> str:
    """یال شرطی — آیا ادامه دهیم یا پاسخ دهیم؟"""
    if state['iteration'] > 5:
        return "END"
    return state['next_node']

# ساخت گراف
graph = GraphAgent()
graph.add_node("reason", reason_node)
graph.add_node("call_tool", tool_node)
graph.add_node("respond", respond_node)
graph.add_edge("call_tool", "reason")  # بازگشت به reason
graph.add_conditional_edge("reason", should_continue)
graph.set_entry_point("reason")
```

---

## ۵. الگوهای تصمیم‌گیری (Decision-Making Patterns)

سه الگوی اصلی برای **تصمیم‌گیری** در معماری عامل‌ها وجود دارد:

### ۵.۱ تصمیم‌گیری تک‌گذر (Single-Pass Decision Making)

ساده‌ترین الگو: عامل ورودی را دریافت می‌کند، یک بار پردازش می‌کند، و خروجی می‌دهد. **بدون بازخورد (feedback)** و **بدون حلقه (loop)**.

```text
ورودی ──▶ [پردازش] ──▶ خروجی
         (یک بار)
```

**مثال:** Function Calling ساده — LLM یک بار ابزار را فراخوانی می‌کند و تمام.

### ۵.۲ تصمیم‌گیری تکراری (Iterative Decision Making)

الگوی **حلقه (Loop)**: عامل به صورت مکرر استدلال می‌کند، اقدام می‌کند، و از نتایج یاد می‌گیرد.

```text
ورودی ──▶ ┌─── [فکر] ──▶ [اقدام] ──▶ [مشاهده] ──┐ ──▶ خروجی
           │                                       │
           └─────────── حلقه ادامه دارد ───────────┘
```

**مثال:** ReAct, Reflexion — عامل تا رسیدن به پاسخ حلقه را تکرار می‌کند.

### ۵.۳ تصمیم‌گیری سلسله‌مراتبی (Hierarchical Decision Making)

الگوی **درختی**: تصمیم‌گیری در سطوح مختلف انجام می‌شود — یک **مدیر (Manager)** اهداف سطح بالا را به زیروظایف می‌شکند و عامل‌های زیردست (Sub-agents) هر کدام بخشی را اجرا می‌کنند.

```text
                        ┌──────────┐
                        │  هدف     │
                        │  (Goal)  │
                        └────┬─────┘
                             │
                    ┌────────┴────────┐
                    │  تقسیم به       │
                    │  زیروظایف       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ زیروظیفه │       │ زیروظیفه │       │ زیروظیفه │
   │   ۱      │       │   ۲      │       │   ۳      │
   └────┬─────┘       └────┬─────┘       └────┬─────┘
        ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ Agent A  │       │ Agent B  │       │ Agent C  │
   │ (تخصصی)  │       │ (تخصصی)  │       │ (تخصصی)  │
   └──────────┘       └──────────┘       └──────────┘
```

**مقایسهٔ الگوهای تصمیم‌گیری:**

| ویژگی | Single-Pass | Iterative | Hierarchical |
|-------|-------------|-----------|--------------|
| **تعداد LLM Calls** | ۱ | N (بسیار) | N (توزیع‌شده) |
| **سرعت** | ⚡⚡ بسیار بالا | 🐢 پایین | ⚡ متوسط |
| **کیفیت** | ⚠️ متوسط | ✅ بالا | ✅ بسیار بالا |
| **هزینه** | 💰 کم | 💰💰💰 بالا | 💰💰 متوسط |
| **شفافیت** | کم | زیاد | زیاد |
| **مناسب برای** | وظایف ساده | وظایف پیچیده | وظایف بسیار پیچیده |

---

## ۶. جدول مقایسهٔ جامع (Comparison Table)

### ۶.۱ مقایسهٔ معماری‌های کلاسیک

| معماری | حافظه | برنامه‌ریزی | سرعت | انعطاف | پیچیدگی | هزینهٔ محاسباتی |
|--------|------|------------|------|--------|---------|---------------|
| **Reactive** | ❌ ندارد | ❌ ندارد | ⚡⚡ بسیار بالا | ❌ کم | 🔧 ساده | بسیار کم |
| **Deliberative (BDI)** | ✅ مدل جهان | ✅ برنامهٔ صریح | 🐢 متوسط | ✅ زیاد | 🏗️ پیچیده | متوسط |
| **Hybrid** | ✅ ترکیبی | ✅ چندلایه | ⚡ بالا | ✅ زیاد | 🏗️🏗️ بسیار پیچیده | متوسط تا زیاد |

### ۶.۲ مقایسهٔ معماری‌های مدرن (LLM-Based)

| معماری | سال | LLM Calls | حلقه | حافظه | استدلال | هزینه | بهترین برای |
|--------|-----|-----------|------|-------|---------|-------|-----------|
| **ReAct** | ۲۰۲۳ | زیاد (۱+ در هر گام) | ✅ حلقهٔ T→A→O | Scratchpad | CoT در هر گام | 💰💰💰 | وظایف پویا و اکتشافی |
| **Plan-and-Execute** | ۲۰۲۳ | کم (۱ برنامه + n اجرا) | ⚠️ خطی | برنامهٔ صریح | برنامه‌ریزی متمرکز | 💰💰 | وظایف ساختاریافته |
| **Tree-of-Thoughts** | ۲۰۲۳ | بسیار زیاد (k^d) | ✅ درختی | درخت جستجو | جستجوی BFS/DFS | 💰💰💰💰 | مسائل استدلالی عمیق |
| **Reflection (Reflexion)** | ۲۰۲۳ | زیاد (تلاش‌های متعدد) | ✅ حلقه با بازخورد | حافظهٔ درس‌ها | خود-ارزیابی | 💰💰💰 | یادگیری از خطا |
| **MoA (Mixture-of-Agents)** | ۲۰۲۴ | N×L (N عامل × L لایه) | ✅ موازی | نتایج موقت | ترکیب چند دیدگاه | 💰💰💰💰💰 | وظایف باکیفیت بالا |

### ۶.۳ مقایسهٔ لایه‌های معماری

| لایه | ورودی | خروجی | فناوری‌ها |
|------|-------|-------|-----------|
| **Perception** | دادهٔ خام | بازنمایی داخلی | Tokenizer, CLIP, Whisper |
| **Reasoning** | بازنمایی داخلی | تصمیم | LLM, CoT, BDI Rules |
| **Memory** | اطلاعات | دانش بازیابی‌شده | Vector DB, Cache, KV Store |
| **Action** | دستور عمل | اثر در جهان | MCP, REST, Code Interpreter |

### ۶.۴ مقایسهٔ State Machine در برابر Graph

| معیار | State Machine | Graph (LangGraph) |
|-------|---------------|-------------------|
| **پیچیدگی پیاده‌سازی** | ساده | متوسط |
| **انعطاف‌پذیری مسیر** | کم (حالت‌های از پیش تعریف) | زیاد (یال‌های شرطی) |
| **مدیریت State** | ضمنی (موقعیت فعلی) | صریح (شیء مرکزی State) |
| **حلقه و بازگشت** | دشوار | طبیعی |
| **Human-in-the-Loop** | دشوار | built-in |
| **مقیاس‌پذیری** | محدود | بالا |
| **دیباگ و تست** | آسان | متوسط |
| **محبوبیت در LLM Agents** | کم | بسیار زیاد |

### ۶.۵ راهنمای انتخاب معماری (Architecture Selection Guide)

```text
آیا وظیفه ساده و تک‌مرحله‌ای است؟
├── ✅ بله → Reactive (کلاسیک) یا Function Calling (مدرن)
└── ❌ خیر
    ├── آیا مسیر اجرا از قبل قابل پیش‌بینی است؟
    │   ├── ✅ بله → Plan-and-Execute
    │   └── ❌ خیر
    │       ├── آیا نیاز به بررسی چندین مسیر موازی داریم؟
    │       │   ├── ✅ بله → Tree-of-Thoughts
    │       │   └── ❌ خیر
    │       │       ├── آیا عامل باید از خطاهای خود درس بگیرد؟
    │       │       │   ├── ✅ بله → Reflection (Reflexion)
    │       │       │   └── ❌ خیر → ReAct
    │       │       │
    │       ├── آیا چندین تخصص مجزا نیاز داریم؟
    │       │   ├── ✅ بله → MoA (Mixture-of-Agents)
    │       │   └── ❌ خیر → BDI یا Hybrid (کلاسیک)
    │       │
    │       ├── آیا معماری کلاسیک کافی است؟
    │       │   ├── ✅ محیط قابل پیش‌بینی → Reactive
    │       │   ├── ✅ نیاز به مدل جهان → BDI
    │       │   └── ✅ نیاز به هر دو → Hybrid
```

---

## ۷. نگاشت به HiveOS (Mapping to HiveOS)

### ۷.۱ معماری‌ها در HiveOS

در **HiveOS**، معماری‌های مختلف برای دامنه‌های (Domains) مختلف به کار گرفته می‌شوند:

| معماری | دامنه در HiveOS | مثال |
|--------|----------------|------|
| **Reactive** | دامنه‌های نظارتی (Monitoring) | تشخیص ناهنجاری و اقدام فوری |
| **BDI (Deliberative)** | دامنهٔ استراتژیک (Strategy) | برنامه‌ریزی تخصیص منابع |
| **Hybrid** | دامنهٔ Mothership | ترکیب واکنش سریع با برنامه‌ریزی بلندمدت |
| **ReAct** | دامنه‌های عاملی عمومی | factorهای جستجو، تحلیل، تحقیق |
| **Plan-and-Execute** | دامنه‌های تولید محتوا | factorهای گزارش‌گیری، مستندسازی |
| **Tree-of-Thoughts** | دامنهٔ R&D | اکتشاف راه‌حل‌های جدید |
| **Reflection** | دامنهٔ QA و تست | factorهای تست خود-اصلاح‌شونده |
| **MoA** | دامنه‌های حساس (Finance, Legal) | ترکیب نظر چند factor تخصصی |

### ۷.۲ لایه‌های معماری HiveOS

```text
┌──────────────────────────────────────────────────────────┐
│              HiveOS — Architectural Layers                  │
│                                                            │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Layer 1: Gateway (Perception)                   │     │
│  │  دروازهٔ ورودی — دریافت پیام از کاربران و سیستم‌ها │     │
│  │  → مسیریابی (Routing) → اعتبارسنجی (Validation)   │     │
│  └─────────────────────┬───────────────────────────┘     │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Layer 2: Mothership (Reasoning / Orchestration) │     │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │     │
│  │  │Planning  │ │ Policy  │ │ State & Memory │   │     │
│  │  │Unit     │ │ Unit    │ │ Mgmt          │   │     │
│  │  └──────────┘ └──────────┘ └────────────────┘   │     │
│  └─────────────────────┬───────────────────────────┘     │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Layer 3: Agent Domains (Action / Execution)     │     │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │     │
│  │  │ Domain A │ │ Domain B │ │ Domain C      │   │     │
│  │  │ (Search) │ │ (Finance)│ │ (Code Gen)    │   │     │
│  │  └──────────┘ └──────────┘ └────────────────┘   │     │
│  └─────────────────────┬───────────────────────────┘     │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Layer 4: MCP / Tool Ecosystem (Tools)          │     │
│  │  ابزارهای استاندارد از طریق Model Context Protocol│     │
│  └─────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### ۷.۳ HiveOS Flow Engine — ترکیب State Machine و Graph

HiveOS از یک **Flow Engine** استفاده می‌کند که ترکیبی از State Machine و Graph است:

- **State Machine** برای جریان‌های ساده و خطی (مثل onboarding flow)
- **LangGraph-style Graph** برای جریان‌های پیچیده با شاخه‌های شرطی و حلقه

```yaml
# HiveOS Agent Blueprint — معماری ترکیبی
agent:
  name: research-assistant
  domain: research
  architecture:
    # لایهٔ پایه: ReAct برای استدلال پویا
    reasoning: react
    llm:
      model: claude-opus-4
      max_iterations: 15

    # لایهٔ حافظه: سه سطح
    memory:
      short_term:
        type: buffer
        size: 20  # پیام
      long_term:
        type: vector_db
        backend: chroma
        collection: research-memories
      episodic:
        type: log
        path: /var/log/agents/research/episodes.jsonl

    # لایهٔ ابزار: از طریق MCP
    tools:
      - name: web_search
        mcp_server: search-service
      - name: read_pdf
        mcp_server: document-store
      - name: code_execute
        mcp_server: sandbox

    # لایهٔ خط‌مشی (Policy)
    governance:
      max_cost_per_run: 0.50  # دلار
      allowed_tools: [web_search, read_pdf, code_execute]
      human_approval:
        - tool: code_execute
          condition: "contains dangerous operations"
```

### ۷.۴ بینش‌های معماری برای HiveOS (Architecture Insights)

| بینش (Insight) | توضیح | تأثیر بر HiveOS |
|---------------|-------|----------------|
| **۱. هیچ معماری برتری ندارد** | انتخاب معماری به وظیفه، هزینه، و سرعت مورد نیاز بستگی دارد | هر دامنه (Domain) معماری مخصوص خود را دارد |
| **۲. معماری ترکیبی برنده است** | Hybrid و Graph-based بهترین تعادل را دارند | HiveOS Flow Engine از ترکیب State Machine + Graph استفاده می‌کند |
| **۳. حافظه عامل تعیین‌کننده است** | بدون حافظه، عامل نمی‌تواند یاد بگیرد یا تطبیق یابد | HiveOS سه سطح حافظه (STM, LTM, Episodic) دارد |
| **۴. شفافیت حیاتی است** | ReAct و Graph سطوح بالایی از شفافیت ارائه می‌دهند | تمام استدلال عامل‌ها در HiveOS قابل بازبینی است |
| **۵. هزینه را مدیریت کنید** | MoA و ToT هزینهٔ بالایی دارند — فقط برای وظایف باارزش | HiveOS دارای Policy Unit برای کنترل هزینه است |
| **۶. Human-in-the-Loop فراموش نشود** | در معماری‌های مدرن می‌توان human-in-loop را تعبیه کرد | Gateway HiveOS از تأیید انسانی در میانهٔ حلقه پشتیبانی می‌کند |
| **۷. از ابزارهای استاندارد استفاده کنید** | MCP ارتباط عامل با ابزارها را استاندارد می‌کند | تمام ابزارهای HiveOS از طریق MCP در دسترس هستند |

---

## جمع‌بندی (Summary)

| رده | معماری | بهترین کاربرد |
|-----|--------|-------------|
| 🏛️ **کلاسیک** | Reactive | واکنش‌های سریع و ساده |
| 🏛️ **کلاسیک** | BDI | برنامه‌ریزی و استدلال ساختاریافته |
| 🏛️ **کلاسیک** | Hybrid | ترکیب سرعت و استدلال |
| 🤖 **مدرن** | ReAct | وظایف پویا و اکتشافی |
| 🤖 **مدرن** | Plan-and-Execute | وظایف ساختاریافته و قابل پیش‌بینی |
| 🤖 **مدرن** | Tree-of-Thoughts | مسائل استدلالی عمیق و پیچیده |
| 🤖 **مدرن** | Reflection | یادگیری از خطا و خود-بهبودی |
| 🤖 **مدرن** | Mixture-of-Agents | وظایف با کیفیت بالا نیازمند تخصص‌های مختلف |
| 🔗 **زیرساخت** | State Machine | جریان‌های ساده و خطی |
| 🔗 **زیرساخت** | Graph (LangGraph) | جریان‌های پیچیده با شاخه‌های شرطی |

> **نکتهٔ نهایی:** طراحی معماری عامل یک «یک اندازه برای همه» نیست. در HiveOS، هر دامنه معماری متناسب با نیاز خود را انتخاب می‌کند — از Reactive ساده برای هشدارهای فوری تا MoA پیچیده برای تصمیمات مالی. درک نقاط قوت و ضعف هر معماری، کلید طراحی سیستم‌های عاملی مؤثر است.

---

> **نویسنده:** مستند فنی HiveOS — برگرفته از مقالات «Intelligent Agent Architectures: A Survey» (Nwakanma et al., 2024)، «ReAct: Synergizing Reasoning and Acting in Language Models» (Yao et al., 2023)، «Tree-of-Thoughts: Deliberate Problem Solving with LLMs» (Yao et al., 2023)، «Reflexion: Language Agents with Verbal Reinforcement Learning» (Shinn et al., 2023)، «Mixture-of-Agents Enhances Large Language Model Capabilities» (Wang et al., 2024)، «BDI Agents: From Theory to Practice» (Rao & Georgeff, 1995)، مستندات رسمی LangGraph، و منابع کلاسیک AI
>
> **تاریخ:** جولای ۲۰۲۶
> **مسیر:** `docs/06-Research/agents/01-Fundamentals/02-agent-architectures.md`

# بازتاب و خوداصلاحی — Reflection & Self-Correction in AI Agents

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **منابع:** Reflexion (Shinn et al., 2023) · Self-Refine (Madaan et al., 2023) · CRITIC (Gou et al., 2024) · Anthropic Constitutional AI · HiveOS Brain Decision Tracer

---

## ۱. مقدمه: چرا خوداصلاحی؟

یکی از مهم‌ترین تفاوت‌های یک **عامل هوشمند واقعی** با یک **اسکریپت ساده**، توانایی **بازتاب (Reflection)** و **خوداصلاحی (Self-Correction)** است. عوامل هوشمند می‌توانند:

1. **تشخیص دهند** که خروجی‌شان اشتباه است
2. **تحلیل کنند** چرا اشتباه رخ داده
3. **تصحیح کنند** مسیر خود را
4. **یاد بگیرند** از اشتباه برای آینده

| بدون خوداصلاحی | با خوداصلاحی |
|----------------|-------------|
| خطا را تکرار می‌کند | خطا را تشخیص و تصحیح می‌کند |
| لاگ می‌کند اما تغییری نمی‌دهد | از خطا یاد می‌گیرد |
| وابسته به انسان برای رفع خطا | خودمختار (autonomous) |
| degradation تدریجی | بهبود تدریجی |

> **تشبیه:** یک عامل بدون خوداصلاحی مثل **کارمندی است که هرگز به کارهای قبلی‌اش نگاه نمی‌کند** — ممکن است یک اشتباه را هر روز تکرار کند. عامل با خوداصلاحی مثل **کارمند حرفه‌ای** است که بعد از هر پروژه، مرور پس‌ازعمل (post-mortem) انجام می‌دهد و دفعهٔ بعد بهتر عمل می‌کند.

---

## ۲. الگوی Reflexion

مقالهٔ **Reflexion** (Shinn et al., 2023) یکی از تأثیرگذارترین کارها در این حوزه است.

### معماری Reflexion:

```text
┌─────────────────────────────────────────────────────────┐
│                   Reflexion Agent                        │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │  Actor   │───▶│ Evaluator│───▶│   Reflexion     │   │
│  │ (عامل)   │    │ (ارزیاب) │    │  (حافظهٔ反思)   │   │
│  └──────────┘    └──────────┘    └──────────────────┘   │
│       │               │                    │             │
│       │               │                    │             │
│       ▼               ▼                    ▼             │
│  ┌─────────────────────────────────────────────┐        │
│  │           حافظهٔ تجربی (Episodic Memory)      │        │
│  │  trial 1: failed — "خطا در محاسبه مالیات"     │        │
│  │  trial 2: failed — "فرمول اشتباه برای معافیت" │        │
│  │  trial 3: success — "از فرمول صحیح استفاده شد"│        │
│  └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### سه مؤلفهٔ اصلی:

1. **Actor (بازیگر):** عامل اصلی که وظیفه را انجام می‌دهد — مثلاً محاسبه مالیات
2. **Evaluator (ارزیاب):** خروجی Actor را بررسی می‌کند — آیا درست است یا غلط؟
3. **Reflexion (بازتاب):** حافظه‌ای از تجربیات قبلی شامل اشتباهات و درس‌ها

### پیاده‌سازی Reflexion:

```python
class ReflexionAgent:
    """عامل با قابلیت Reflexion — خوداصلاحی مبتنی بر حافظه"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.memory = []  # حافظهٔ تجربی
        
    async def run_with_reflexion(self, task: str, max_trials: int = 3) -> str:
        """اجرای وظیفه با قابلیت اصلاح خودکار"""
        
        for trial in range(1, max_trials + 1):
            # ۱. اجرا با زمینهٔ حافظه
            context = self._build_context(task)
            result = await self._execute(context)
            
            # ۲. ارزیابی خودکار
            evaluation = await self._evaluate(task, result)
            
            if evaluation["is_correct"]:
                # موفق — ذخیره و برگردان
                self._save_trial(trial, task, result, evaluation, "success")
                return result
            
            # ۳. بازتاب — تحلیل خطا
            reflection = await self._reflect(
                task=task,
                result=result,
                evaluation=evaluation
            )
            
            # ۴. ذخیره در حافظه
            self._save_trial(trial, task, result, evaluation, "failed", reflection)
            
        return f"Failed after {max_trials} trials. Last try: {result}"
    
    async def _reflect(self, task: str, result: str, evaluation: dict) -> str:
        """تولید بازتاب (reflection) دربارهٔ خطا"""
        prompt = f"""
        وظیفه: {task}
        خروجی فعلی: {result}
        خطا: {evaluation['error']}
        
        تحلیل کن چرا این خطا رخ داد و چه باید کرد:
        1. علت ریشه‌ای (root cause)
        2. راهکار اصلاحی
        3. چگونه از تکرار جلوگیری کنیم؟
        """
        return await self.llm.generate(prompt)
    
    def _build_context(self, task: str) -> str:
        """ساخت زمینه با استفاده از حافظهٔ تجربی"""
        if not self.memory:
            return task
        
        # خلاصه‌ای از درس‌های قبلی
        lessons = []
        for trial in self.memory[-3:]:  # آخرین ۳ تلاش
            if trial["status"] == "failed" and trial.get("reflection"):
                lessons.append(trial["reflection"])
        
        context = f"{task}\n\nدرس‌های قبلی:\n" + "\n".join(lessons)
        return context
```

### مثال عملی:

```text
وظیفه: محاسبه مالیات بر ارزش افزوده برای فاکتور ۵۰,۰۰۰,۰۰۰ تومان
─────────────────────────────────────────────────────────────────

▶ Trial 1 (بدون حافظه):
  → نتیجه: ۵۰,۰۰۰,۰۰۰ × ۹٪ = ۴,۵۰۰,۰۰۰ تومان
  → ارزیاب: ❌ نرخ VAT برای ۱۴۰۴ برابر ۱۰٪ است، نه ۹٪
  → بازتاب: "نرخ VAT ۱۴۰۴ را اشتباه زدم. باید از آخرین بخشنامه استفاده کنم."

▶ Trial 2 (با حافظه):
  → نتیجه: ۵۰,۰۰۰,۰۰۰ × ۱۰٪ = ۵,۰۰۰,۰۰۰ تومان
  → ارزیاب: ✅ درست است
  → ذخیره در حافظه: "نرخ VAT ۱۴۰۴ = ۱۰٪"
```

---

## ۳. الگوی Self-Refine

مقالهٔ **Self-Refine** (Madaan et al., 2023) رویکردی هم‌زمان دارد — به جای trial-and-error، در **همان گام** خروجی را اصلاح می‌کند:

```text
ورودی → [تولید اولیه] → [خودبازخورد] → [اصلاح] → خروجی نهایی
              │              │
              └──────┬───────┘
                     │
                (تکرار تا N بار)
```

```python
async def self_refine(llm, task: str, max_iterations: int = 3) -> str:
    """Self-Refine: تولید → نقد → اصلاح"""
    
    # ۱. تولید اولیه
    current = await llm.generate(f"تولید پاسخ برای: {task}")
    
    for i in range(max_iterations):
        # ۲. نقد خروجی فعلی
        feedback = await llm.generate(
            f"خروجی زیر را نقد کن. مشکلات، اشتباهات، نقاط ضعف:\n{current}"
        )
        
        # ۳. اصلاح بر اساس نقد
        improved = await llm.generate(
            f"""خروجی قبلی: {current}
            نقد: {feedback}
            
            بر اساس نقد بالا، خروجی را اصلاح کن.""",
        )
        
        # اگر بهبود معنی‌داری نداشت، متوقف شو
        if is_similar(current, improved, threshold=0.95):
            return improved
        
        current = improved
    
    return current
```

---

## ۴. الگوی CRITIC

**CRITIC** (Gou et al., 2024) از ابزارهای خارجی برای اعتبارسنجی استفاده می‌کند:

```text
عامل → [تولید خروجی] → [بررسی با ابزار خارجی] → [اصلاح]
                            │
                      ┌─────┴─────┐
                      │  جستجوی   │
                      │  وب / API │
                      │ کد / DB   │
                      └───────────┘
```

```python
class CRITICAgent:
    """Self-Correction با استفاده از ابزارهای خارجی برای تأیید"""
    
    async def verify_with_tools(self, output: str, task: str) -> tuple[bool, str]:
        """بررسی خروجی با ابزارهای خارجی"""
        
        if "محاسبه" in task:
            # محاسبات را دوباره با ماشین‌حساب بررسی کن
            calc_result = await self.tools["calculator"].run(
                extract_formula(output)
            )
            return output_matches(output, calc_result)
        
        elif "جستجو" in task or "واقعیت" in task:
            # واقعیت‌ها را با جستجوی وب بررسی کن
            facts = extract_facts(output)
            for fact in facts:
                web_result = await self.tools["web_search"].run(fact)
                if not verify_fact(fact, web_result):
                    return False, f"Fact not verified: {fact}"
            return True, "All facts verified"
        
        elif "کد" in task or "برنامه" in task:
            # کد را اجرا و تست کن
            code = extract_code(output)
            test_result = await self.tools["code_executor"].run(code)
            return test_result["passed"], test_result["error"]
        
        return False, "No verification tool available"
```

---

## ۵. Constitutional AI — خوداصلاحی اخلاقی

**Constitutional AI** (Anthropic, 2023) رویکردی برای خوداصلاحی بر اساس **اصول (Constitution)** است:

### نحوهٔ کار:

```text
مرحله ۱: تولید خروجی
  → "این مشتری به دلیل نمره اعتباری پایین واجد شرایط نیست."

مرحله ۲: نقد بر اساس قانون اساسی
  → اصل ۵: "هیچ تصمیمی نباید بر اساس تبعیض ناعادلانه باشد"
  → نقد: "آیا نمره اعتباری پایین به‌تنهایی دلیل کافی است؟"

مرحله ۳: اصلاح
  → "این مشتری به دلیل نمره اعتباری پایین واجد شرایط نیست.
     برای اطلاعات بیشتر دربارهٔ گزینه‌های جایگزین، لطفاً با پشتیبانی تماس بگیرید."
```

```python
CONSTITUTION = [
    {
        "principle": "دقت (Accuracy)",
        "critique": "آیا اعداد و ارقام درست محاسبه شده‌اند؟",
        "revision": "اعداد را مجدداً محاسبه کن و صحت‌سنجی کن"
    },
    {
        "principle": "انصاف (Fairness)",
        "critique": "آیا این پاسخ منصفانه است و تبعیض آمیز نیست؟",
        "revision": "پاسخ را به گونه‌ای بازنویسی کن که منصفانه و محترمانه باشد"
    },
    {
        "principle": "شفافیت (Transparency)",
        "critique": "آیا منطق پشت این تصمیم مشخص است؟",
        "revision": "توضیح بیشتری دربارهٔ دلیل تصمیم اضافه کن"
    },
    {
        "principle": "قابلیت حسابرسی (Auditability)",
        "critique": "آیا می‌توان این تصمیم را ردیابی و حسابرسی کرد؟",
        "revision": "اطلاعات ردیابی (منابع، محاسبات) را اضافه کن"
    }
]

async def constitutional_reflection(llm, output: str, principles: list) -> str:
    """خوداصلاحی بر اساس قانون اساسی"""
    current = output
    
    for principle in principles:
        # نقد
        critique = await llm.generate(
            f"خروجی: {current}\n"
            f"اصل: {principle['principle']}\n"
            f"سوال نقد: {principle['critique']}"
        )
        
        if is_critical(critique):
            # اصلاح
            current = await llm.generate(
                f"خروجی: {current}\n"
                f"نقد: {critique}\n"
                f"دستور اصلاح: {principle['revision']}"
            )
    
    return current
```

---

## ۶. خوداصلاحی در سیستم‌های چندعاملی

در **HiveOS**، خوداصلاحی در سه سطح پیاده‌سازی شده:

### سطح ۱: خوداصلاحی درون‌عاملی (Intra-Agent)

هر عامل خودش خروجی خود را بررسی و اصلاح می‌کند — الگوی Reflexion.

### سطح ۲: خوداصلاحی بین‌عاملی (Inter-Agent)

عامل‌ها خروجی یکدیگر را بررسی می‌کنند:

```python
# HiveOS — Cross-Agent Validation
class CrossAgentValidator:
    """یک عامل خروجی عامل دیگر را اعتبارسنجی می‌کند"""
    
    async def validate(self, agent_name: str, output: str) -> dict:
        prompt = f"""
        شما یک ممیز (reviewer) هستید.
        
        خروجی عامل '{agent_name}':
        {output}
        
        لطفاً بررسی کنید:
        ۱. آیا منطق (logic) درست است؟
        ۲. آیا اعداد دقیق هستند؟
        ۳. آیا هیچ نکته‌ای جا نیفتاده؟
        
        نتیجه: ✅ تأیید / ❌ نیاز به اصلاح
        """
        
        result = await self.llm.generate(prompt)
        return self.parse_validation(result)
```

### سطح ۳: خوداصلاحی سیستمی (System-Level)

**Brain Decision Tracer** در HiveOS تمام مسیرهای تصمیم‌گیری را ثبت می‌کند و امکان ردیابی و اصلاح را فراهم می‌کند:

```python
# HiveOS Brain — Decision Trace with Correction
from hiveos.brain.decision_tracer import DecisionTracer

tracer = DecisionTracer(storage=storage)

trace = await tracer.start_trace(
    agent="financial-analyst",
    task="محاسبه مالیات ۱۴۰۴"
)

# عامل کار می‌کند...
step_1 = await tracer.trace_step(trace.id, "بازیابی نرخ مالیات")

if "error" in step_1.result:
    # خوداصلاحی: تلاش مجدد با منبع دیگر
    correction = await tracer.trace_correction(
        trace_id=trace.id,
        step_id=step_1.id,
        correction_type="source_retry",
        new_result=await fetch_from_backup_source()
    )
```

---

## ۷. ماتریس الگوهای خوداصلاحی

| الگو | زمان استفاده | مزایا | معایب | هزینه Token |
|------|-------------|-------|-------|------------|
| **Reflexion** | وظایف چندمرحله‌ای با خطاهای قابل پیش‌بینی | درس از اشتباهات گذشته | نیاز به trialهای متعدد | بالا |
| **Self-Refine** | تولید محتوا، کد، تحلیل | یکباره، سریع | وابسته به کیفیت LLM | متوسط |
| **CRITIC** | وظایف نیازمند صحت (محاسبات، واقعیت) | تأیید خارجی، دقیق | نیاز به ابزار خارجی | متوسط |
| **Constitutional AI** | تصمیمات حساس (بانکی، حقوقی) | اخلاقی، شفاف | نیاز به تدوین اصول | پایین |
| **Cross-Agent** | سیستم‌های چندعاملی | دید چندجانبه | هزینه coordination | بالا |

---

## ۸. پیاده‌سازی ترکیبی در HiveOS

```python
class HiveOSSelfCorrectingAgent:
    """عامل خوداصلاح‌شوندهٔ HiveOS — ترکیب Reflexion + CRITIC + Constitutional"""
    
    async def execute(self, task: str) -> dict:
        result = {
            "task": task,
            "output": None,
            "trials": [],
            "final_status": None
        }
        
        for trial in range(1, 4):
            # ۱. اجرا
            output = await self._act(task, trial)
            
            # ۲. اعتبارسنجی CRITIC
            critic_result = await self._critic_validate(output)
            
            # ۳. بررسی قانون اساسی
            constitutional_check = await self._constitutional_check(output)
            
            # ۴. ثبت
            result["trials"].append({
                "trial": trial,
                "output": output,
                "critic": critic_result,
                "constitutional": constitutional_check
            })
            
            if critic_result["passed"] and constitutional_check["passed"]:
                result["output"] = output
                result["final_status"] = "success"
                return result
            
            # ۵. بازتاب برای trial بعدی
            if trial < 3:
                reflection = await self._reflect(
                    task, output, critic_result, constitutional_check
                )
                self.reflection_memory.append(reflection)
        
        result["final_status"] = "failed"
        return result
```

---

## ۹. جمع‌بندی

| # | نکته |
|---|------|
| ۱ | **خوداصلاحی** (Self-Correction) تفاوت عامل هوشمند با اسکریپت ساده است |
| ۲ | **Reflexion**: یادگیری از trialهای قبلی با حافظهٔ تجربی |
| ۳ | **Self-Refine**: نقد و اصلاح در همان گام — سریع‌تر از Reflexion |
| ۴ | **CRITIC**: اعتبارسنجی با ابزارهای خارجی (محاسبه، جستجو، اجرای کد) |
| ۵ | **Constitutional AI**: خوداصلاحی بر اساس اصول اخلاقی و سازمانی |
| ۶ | **Cross-Agent**: عامل‌ها کار هم را بررسی می‌کنند |
| ۷ | در **HiveOS**، Brain Decision Tracer تمام اصلاحات را ردیابی می‌کند |
| ۸ | **هزینهٔ خوداصلاحی** را در نظر بگیرید — همیشه لازم نیست، در وظایف حساس فعالش کنید |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل‌های مرتبط:**
> - `src/hiveos/brain/decision_tracer.py` — ردیابی تصمیمات و اصلاحات
> - `docs/06-Research/agents/04-Advanced-Patterns/02-multi-step-reasoning.md`

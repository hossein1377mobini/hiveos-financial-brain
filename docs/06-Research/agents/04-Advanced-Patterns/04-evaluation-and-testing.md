# ارزیابی و تست عامل‌های هوش مصنوعی — Evaluation & Testing of AI Agents

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **منابع:** LangSmith · Weights & Biases · MLflow · Promptfoo · DeepEval · HiveOS Testing Framework

---

## ۱. مقدمه: چرا تست عامل‌ها متفاوت است؟

تست یک **عامل هوش مصنوعی (AI Agent)** با تست نرم‌افزار سنتی تفاوت اساسی دارد:

| نرم‌افزار سنتی | عامل هوش مصنوعی |
|----------------|-----------------|
| خروجی قطعی (Deterministic) | خروجی احتمالی (Non-deterministic) |
| ورودی مشخص → خروجی مشخص | ورودی مشابه → خروجی‌های مختلف |
| تست واحد کافی است | نیاز به تست زنجیره‌ای |
| خطا = باگ در کد | خطا = استدلال نادرست |
| تصحیح = رفع باگ | تصحیح = بهبود پرامپت / داده |

> **نکته کلیدی:** تست عامل‌ها = تست نرم‌افزار + تست مدل + تست استدلال.

---

## ۲. سطوح تست (Testing Levels)

### ۲.۱ تست واحد ابزارها (Tool Unit Testing)

هر ابزار باید به صورت مجزا تست شود:

```python
# تست یک ابزار محاسبه مالیات
def test_tax_calculator():
    tool = TaxCalculatorTool()
    
    # ۱. ورودی استاندارد
    result = tool.run(salary=50_000_000, year=1404)
    assert result["tax_amount"] == 5_000_000  # 10% VAT
    assert result["status"] == "success"
    
    # ۲. لبه (Edge cases)
    result = tool.run(salary=0, year=1404)
    assert result["tax_amount"] == 0
    
    # ۳. خطا (Error cases)
    with pytest.raises(ValueError):
        tool.run(salary=-1000, year=1404)
```

### ۲.۲ تست پرامپت (Prompt Testing)

تست اینکه پرامپت عامل همیشه خروجی قابل قبول تولید می‌کند:

```python
import promptfoo

# تست با Promptfoo
results = promptfoo.evaluate(
    prompts=["system_prompt_v1.md", "system_prompt_v2.md"],
    tests=[
        {"vars": {"task": "محاسبه مالیات حقوق ۵۰ میلیون"}, "expected": {"contains": "۱۰٪"}},
        {"vars": {"task": "diss customer"}, "expected": {"not_contains": ["فحش", "توهین"]}},
        {"vars": {"task": ""}, "expected": {"output_type": "string", "min_length": 10}},
    ],
    providers=["openai:gpt-4o", "anthropic:claude-sonnet-4"]
)
```

### ۲.۳ تست سناریو (Scenario Testing)

زنجیره کامل یک وظیفه را تست می‌کند:

```python
@pytest.mark.asyncio
async def test_financial_analysis_scenario():
    agent = FinancialAnalysisAgent()
    
    # سناریوی کامل
    result = await agent.run({
        "task": "تحلیل شرکت X برای سرمایه‌گذاری",
        "company": "شرکت نمونه",
        "year": 1404
    })
    
    # بررسی‌های کیفی
    assert result["has_financial_ratios"] == True
    assert result["liquidity_ratio"] > 0
    assert result["has_recommendation"] == True
    assert len(result["report"]) > 500  # حداقل ۵۰۰ کلمه
    
    # بررسی دقیق اعداد
    assert abs(result["calculated_tax"] - expected_tax) < 1000
```

---

## ۳. معیارهای ارزیابی (Evaluation Metrics)

### ۳.۱ معیارهای کمی (Quantitative Metrics)

| معیار | توضیح | اندازه‌گیری |
|-------|-------|------------|
| **Success Rate** | درصد وظایف کامل‌شده | `موفق / کل` |
| **Accuracy** | دقت خروجی‌ها | `درست / کل` |
| **Latency** | زمان پاسخ | میانگین ثانیه |
| **Cost per Task** | هزینه به ازای هر وظیفه | مجموع tokenها / تعداد |
| **Retry Rate** | درصد نیاز به تلاش مجدد | `تلاش‌های مجدد / کل` |
| **Tool Error Rate** | درصد خطاهای ابزار | `خطاهای ابزار / فراخوانی` |
| **Hallucination Rate** | درصد توهم / اطلاعات نادرست | نمونه‌برداری دستی |

### ۳.۲ معیارهای کیفی (Qualitative Metrics)

| معیار | توضیح | روش اندازه‌گیری |
|-------|-------|----------------|
| **Coherence** | انسجام منطقی | LLM-as-Judge |
| **Completeness** | کامل بودن پاسخ | Checklist اتوماتیک |
| **Clarity** | وضوح توضیحات | ارزیابی انسانی |
| **Safety** | امنیت / نداشتن محتوای مضر | Constitutional AI check |
| **Fairness** | عدم تبعیض | بررسی آماری |

---

## ۴. LLM-as-Judge — ارزیابی با LLM

یکی از رایج‌ترین روش‌های ارزیابی عامل‌ها:

```python
class LLMAsJudge:
    """ارزیابی خروجی عامل با LLM مجزا"""
    
    def __init__(self, judge_model="claude-sonnet-4"):
        self.judge = judge_model
    
    async def evaluate(
        self,
        task: str,
        agent_output: str,
        criteria: list[str]
    ) -> dict:
        prompt = f"""
        شما یک داور (Judge) هستید. خروجی یک عامل هوش مصنوعی را ارزیابی کنید.
        
        وظیفه: {task}
        
        خروجی عامل:
        {agent_output}
        
        معیارهای ارزیابی:
        {chr(10).join(f'- {c}' for c in criteria)}
        
        به هر معیار امتیاز ۱-۵ بدهید و دلیل بیاورید.
        فرمت خروجی JSON:
        {{
            "scores": {{"معیار۱": 4, "معیار۲": 3, ...}},
            "average": 3.5,
            "strengths": ["..."],
            "weaknesses": ["..."],
            "overall_verdict": "pass" | "needs_improvement" | "fail",
            "detailed_reasoning": "..."
        }}
        """
        
        return await self.judge.generate(prompt)
```

---

## ۵. تست رگرسیون Agent (Agent Regression Testing)

با تغییر پرامپت، ابزار، یا معماری، باید مطمئن شوید رفتار قبلی خراب نشده:

```python
class AgentRegressionTest:
    """تست رگرسیون برای عامل‌ها"""
    
    def __init__(self):
        self.test_suite = []
    
    def add_test(self, name: str, task: str, assertions: list):
        self.test_suite.append({
            "name": name,
            "task": task,
            "assertions": assertions
        })
    
    async def run_all(self, agent) -> dict:
        results = {"passed": 0, "failed": 0, "details": []}
        
        for test in self.test_suite:
            output = await agent.run(test["task"])
            
            test_result = {"name": test["name"], "assertions": []}
            all_passed = True
            
            for assertion in test["assertions"]:
                passed = assertion(output)
                test_result["assertions"].append({
                    "check": assertion.__doc__ or str(assertion),
                    "passed": passed
                })
                if not passed:
                    all_passed = False
            
            if all_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(test_result)
        
        return results

# استفاده
regression = AgentRegressionTest()

regression.add_test(
    name="سلام ساده",
    task="سلام",
    assertions=[
        lambda o: len(o) > 0,
        lambda o: "سلام" in o or "خوش" in o,
    ]
)

regression.add_test(
    name="محاسبه سنوات",
    task="محاسبه سنوات ۱۴۰۴ برای ۳ سال سابقه",
    assertions=[
        lambda o: "سال" in o,
        lambda o: any(c.isdigit() for c in o),
    ]
)
```

---

## ۶. ابزارهای ارزیابی

| ابزار | کاربرد | مزایا | معایب |
|-------|--------|-------|-------|
| **LangSmith** | رهگیری + ارزیابی LangChain/LangGraph | یکپارچگی کامل | وابسته به LangChain |
| **Weights & Biases** | رهگیری آزمایش‌ها | داشبورد عالی | عمومی‌تر |
| **MLflow** | مدیریت چرخه ML | منبع‌باز، جامع | سنگین |
| **Promptfoo** | تست پرامپت‌ها | سریع، CLI | محدود به پرامپت |
| **DeepEval** | معیارهای ارزیابی Agent | تخصصی agent | نسبتاً جدید |
| **HiveOS Audit** | رهگیری کامل در HiveOS | Audit Trail بومی | فقط HiveOS |

---

## ۷. چالش‌های ارزیابی

| چالش | توضیح | راهکار |
|------|-------|--------|
| **Non-determinism** | خروجی‌های متفاوت در هر بار | اجرای چندباره + آمار |
| **Ground Truth** | مشخص نبودن پاسخ درست | ارزیابی نسبی (A/B testing) |
| **هزینه** | ارزیابی با LLM هزینه‌بر است | نمونه‌برداری + ارزیابی دسته‌ای |
| **زمان** | ارزیابی کامل زمان‌بر است | CI/CD با subset از تست‌ها |
| **سوبژکتیو بودن** | کیفیت ذهنی است | ارزیابی انسانی + LLM-as-Judge |

---

## ۸. جمع‌بندی

| # | نکته |
|---|------|
| ۱ | تست عامل‌ها = تست نرم‌افزار + تست مدل + تست استدلال |
| ۲ | **چهار سطح تست:** واحد (ابزار) → پرامپت → سناریو → رگرسیون |
| ۳ | **LLM-as-Judge** یک روش مؤثر و مقیاس‌پذیر برای ارزیابی خودکار است |
| ۴ | **معیارهای کمی** (Success Rate, Latency, Cost) با **کیفی** (Coherence, Safety) ترکیب شوند |
| ۵ | **تست رگرسیون** Agent را فراموش نکنید — تغییرات جزئی می‌توانند رفتار را خراب کنند |
| ۶ | **HiveOS Audit Trail** رهگیری کامل اجرا را فراهم می‌کند |
| ۷ | بهترین روش: **CI/CD pipeline** با subset از تست‌های سریع + اجرای شبانهٔ تست‌های کامل |
| ۸ | **مستندسازی خطاها:** هر خطایی که در production پیدا شد، به تست‌ها اضافه شود |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل‌های مرتبط:**
> - `tests/test_learning.py` — تست‌های یادگیری
> - `tests/test_brain.py` — تست‌های مغز

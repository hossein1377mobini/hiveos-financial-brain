# الگوهای استدلال چندمرحله‌ای در عامل‌های هوش مصنوعی — Multi-Step Reasoning Patterns in AI Agents

> **منبع:** برگرفته و بومی‌سازی‌شده از مقالات arXiv «Chain-of-Thought Prompting Elicits Reasoning in Large Language Models» (Wei et al., 2022)، «Tree of Thoughts: Deliberate Problem Solving with Large Language Models» (Yao et al., 2023)، «Graph of Thoughts: Solving Elaborate Problems with Large Language Models» (Besta et al., 2023)، «Self-Consistency Improves Chain-of-Thought Reasoning in Language Models» (Wang et al., 2022)، و «Automatic Chain of Thought Prompting in Large Language Models» (Zhang et al., 2022).
>
> **فایل مرتبط:** الگوهای ReAct، Plan-and-Execute، و Function Calling در `01-Fundamentals/03-reasoning-and-planning.md` پوشش داده شده‌اند. این فایل بر **الگوهای شناختی استدلال چندمرحله‌ای** تمرکز دارد.

---

## فهرست — Table of Contents

1. [مقدمه: فراتر از فراخوانی تک‌شات LLM](#۱-مقدمه-فراتر-از-فراخوانی-تک‌شات-llm)
2. [مرور الگوها — Patterns Overview](#۲-مرور-الگوها--patterns-overview)
3. [Chain-of-Thought (CoT) — زنجیره‌ی تفکر](#۳-chain-of-thought-cot--زنجیرهی-تفکر)
   - [۳.۱ Zero-shot CoT](#۳۱-zero-shot-cot)
   - [۳.۲ Few-shot CoT](#۳۲-few-shot-cot)
   - [۳.۳ Auto-CoT](#۳۳-auto-cot)
   - [۳.۴ پیاده‌سازی در پایتون](#۳۴-پیادهسازی-در-پایتون)
4. [Tree-of-Thought (ToT) — درخت تفکر](#۴-tree-of-thought-tot--درخت-تفکر)
   - [۴.۱ BFS در ToT](#۴۱-bfs-در-tot)
   - [۴.۲ DFS در ToT](#۴۲-dfs-در-tot)
   - [۴.۳ زمان انشعاب و هرس](#۴۳-زمان-انشعاب-و-هرس)
   - [۴.۴ پیاده‌سازی در پایتون](#۴۴-پیادهسازی-در-پایتون)
5. [Graph-of-Thought (GoT) — گراف تفکر](#۵-graph-of-thought-got--گراف-تفکر)
   - [۵.۱ ساختار گراف](#۵۱-ساختار-گراف)
   - [۵.۲ تجمیع (Aggregation)](#۵۲-تجمیع-aggregation)
   - [۵.۳ پیاده‌سازی در پایتون](#۵۳-پیادهسازی-در-پایتون)
6. [Self-Consistency — خودسازگاری](#۶-self-consistency--خودسازگاری)
   - [۶.۱ مکانیزم رای‌گیری](#۶۱-مکانیزم-رایگیری)
   - [۶.۲ پیاده‌سازی در پایتون](#۶۲-پیادهسازی-در-پایتون)
7. [ReACT — اشاره](#۷-react--اشاره)
8. [ماتریس تصمیم‌گیری — Decision Matrix](#۸-ماتریس-تصمیمگیری--decision-matrix)
9. [ادغام با Flow Engine HiveOS](#۹-ادغام-با-flow-engine-hiveos)
10. [جمع‌بندی و منابع](#۱۰-جمعبندی-و-منابع)

---

## ۱. مقدمه: فراتر از فراخوانی تک‌شات LLM

مدل‌های زبانی بزرگ (LLMs) در پاسخ به پرسش‌های مستقیم توانایی بالایی دارند، اما برای **مسائل چندمرحله‌ای** — جایی که یک فراخوانی ساده (single-shot) کافی نیست — به ساختارهای استدلالی پیشرفته‌تری نیاز داریم.

**مشکل:** یک فراخوانی LLM محدودیت‌های زیر را دارد:

| محدودیت | توضیح | مثال |
|---------|-------|------|
| **نقص در استدلال چندمرحله‌ای** | مدل نمی‌تواند گام‌های میانی را به‌درستی دنبال کند | «اگر X=5 و Y=X+3 و Z=Y×2، آن‌گاه Z=؟» |
| **نقص در جستجوی فضای راه‌حل** | مدل تنها یک مسیر را امتحان می‌کند | حل مسئله‌ی ریاضی با چند روش ممکن |
| **عدم امکان بازگشت** | اگر مسیر اشتباه رفت، قابل بازگشت نیست | Debugging یک برنامه |
| **حساسیت به توالی** | ترتیب کلمات در پرامپت تأثیر زیادی دارد | سوالاتی با ساختار شرطی |
| **عدم قطعیت** | مدل بدون ارزیابی قطعیت پاسخ می‌دهد | سوالات چندگزینه‌ای پیچیده |

**راه‌حل:** **استدلال چندمرحله‌ای (Multi-Step Reasoning)** — تکنیک‌هایی که LLM را به تولید **گام‌های میانی تفکر** (intermediate reasoning steps) وادار می‌کنند، فضای راه‌حل را به‌صورت ساختاریافته جستجو می‌کنند، و از طریق **رای‌گیری روی چندین مسیر** به پاسخ پایدارتر می‌رسند.

```text
Single-shot LLM:
┌──────────────────────────────────────────────────────┐
│  Input: "اگر X=5 و Y=X+3 و Z=Y×2، آن‌گاه Z=؟"        │
│  → LLM تولید می‌کند: "Z=16" ❌ (گاهی مستقیم خطا می‌رود) │
└──────────────────────────────────────────────────────┘

Multi-Step Reasoning:
┌──────────────────────────────────────────────────────────┐
│  Step 1: X = 5 ✓                                          │
│  Step 2: Y = X + 3 = 5 + 3 = 8 ✓                         │
│  Step 3: Z = Y × 2 = 8 × 2 = 16 ✓                        │
│  → پاسخ: "Z=16" ✅ (از طریق گام‌های شفاف و قابل راستی‌آزمایی) │
└──────────────────────────────────────────────────────────┘
```

---

## ۲. مرور الگوها — Patterns Overview

پنج الگوی اصلی استدلال چندمرحله‌ای که در این سند پوشش داده می‌شوند:

| الگو | سال | ایدهٔ اصلی | ساختار | نوع جستجو |
|------|-----|-----------|--------|----------|
| **CoT** (Chain-of-Thought) | 2022 | تولید زنجیره‌ای گام‌های تفکر | خطی — Linear | تکی (Single Path) |
| **Self-Consistency** | 2022 | نمونه‌گیری چند مسیر و رای‌گیری | خطی + جمعی — Linear + Ensemble | چندمسیره (Multi-Path) |
| **ToT** (Tree-of-Thought) | 2023 | جستجوی درختی در فضای تفکر | درختی — Tree | BFS / DFS |
| **GoT** (Graph-of-Thought) | 2023 | اتصال گره‌های تفکر در یک گراف | گرافی — Graph | Propagation + Aggregation |
| **ReAct** (Reasoning + Acting) | 2023 | تناوب بین تفکر و اقدام | حلقه — Loop | تعاملی با محیط |

> **نکته:** ReAct در فایل `01-Fundamentals/03-reasoning-and-planning.md` به تفصیل پوشش داده شده است. در اینجا فقط اشاره‌ای به آن می‌کنیم.

```text
سیر تکاملی الگوهای استدلال چندمرحله‌ای:

   CoT (2022)           Self-Consistency (2022)         ToT (2023)            GoT (2023)
خطی ساده                خطی + رای‌گیری                 جستجوی درختی           گراف جهت‌دار
                                                            ▲
┌─────┐    ┌─────┐      ┌─────┐                         ┌─┴─┐                 A
│ گام 1│───▶│ گام 2│     │ مسیر1│──▶ رای│                 │   │                ╱ ╲
└─────┘    └─────┘      │ مسیر2│──▶    │  ───────────▶ ┌─┴─┐ ┌─┴─┐            B   C
           ┌─────┐      │ مسیر3│──▶    │               │   │ │   │           ╱ ╲ ╱
           │ گام 3│     └─────┘  جمع                       BFS / DFS           D   E
           └─────┘
```

---

## ۳. Chain-of-Thought (CoT) — زنجیره‌ی تفکر

**Chain-of-Thought Reasoning** در سال ۲۰۲۲ توسط Wei و همکاران در Google Research معرفی شد. ایده: به جای اینکه از LLM بخواهیم مستقیماً پاسخ دهد، از او می‌خواهیم **گام‌به‌گام فکر کند** و هر مرحله از استدلال را تولید کند.

### ۳.۱ Zero-shot CoT

ساده‌ترین شکل CoT: اضافه کردن عبارت **"Let's think step by step"** به انتهای سوال. این تکنیک بدون نیاز به مثال (zero-shot) عمل می‌کند.

**مثال:**

```
User: ۲۵ عدد سیب دارم. ۱۳ تا را می‌خورم و ۷ تا به دوستم می‌دهم. چند سیب برایم می‌ماند؟

Zero-shot (بدون CoT):
→ پاسخ: "۵" (مستقیم و بدون استدلال)

Zero-shot CoT:
→ "Let's think step by step"
   ابتدا ۲۵ سیب دارم. ۱۳ تا را می‌خورم: ۲۵ - ۱۳ = ۱۲.
   سپس ۷ تا به دوستم می‌دهم: ۱۲ - ۷ = ۵.
   بنابراین ۵ سیب برایم می‌ماند.
→ پاسخ: "۵" (با استدلال شفاف)
```

**نحوه‌ی عملکرد:**

```text
Zero-shot CoT Pipeline:

┌──────────┐     ┌───────────────────┐     ┌───────────┐
│  سوال    │────▶│  "Let's think     │────▶│ تولید     │
│  اصلی    │     │  step by step..." │     │ گام‌های   │
└──────────┘     └───────────────────┘     │ استدلال   │
                                            └─────┬─────┘
                                                  ▼
                                         ┌────────────────┐
                                         │ استخراج پاسخ   │
                                         │ نهایی از متن   │
                                         └────────────────┘
```

**تنوع عبارات Zero-shot CoT:**

| عبارت ماشه‌ای (Trigger Phrase) | کارایی نسبی | مناسب برای |
|-------------------------------|-------------|-----------|
| "Let's think step by step" | ★★★★★ | مسائل عمومی و ریاضی |
| "Let's work this out in a step by step way" | ★★★★☆ | مسائل منطقی |
| "First, ..." | ★★★☆☆ | مسائل ترتیبی |
| "We can break this down" | ★★★★☆ | مسائل تحلیل داده |
| "Step-by-step reasoning:" | ★★★★★ | مسائل فنی و برنامه‌نویسی |

### ۳.۲ Few-shot CoT

در Few-shot CoT، به LLM چند **مثال** (few-shot demonstrations) از فرایند استدلال گام‌به‌گام داده می‌شود.

**مثال پرامپت:**

```text
سوال: راجر ۵ توپ تنیس دارد. او ۲ قوطی توپ تنیس می‌خرد. هر قوطی ۳ توپ دارد.
چند توپ تنیس الان دارد؟
پاسخ: راجر در ابتدا ۵ توپ دارد. ۲ قوطی هر کدام ۳ توپ = ۶ توپ. ۵ + ۶ = ۱۱. جواب ۱۱ است.

سوال: اینترنت در اتاق غذاخوری ۵۳۰ مگابیت در ثانیه است و در اتاق خواب ۴۲۰ مگابیت.
تفاوت سرعت بین دو اتاق چقدر است؟
پاسخ: ۵۳۰ - ۴۲۰ = ۱۱۰. جواب ۱۱۰ مگابیت در ثانیه است.

سوال: {سوال اصلی کاربر}
پاسخ:
```

**تحلیل:**

```text
Few-shot CoT Format:

[مثال ۱: سوال + گام‌های استدلال + پاسخ]
[مثال ۲: سوال + گام‌های استدلال + پاسخ]
[مثال ۳: سوال + گام‌های استدلال + پاسخ]
...
[سوال جدید:] {سوال}
پاسخ:
```

**تأثیر تعداد مثال‌ها بر دقت:**

| تعداد مثال‌ها | دقت (GSM8K) | هزینه (توکن) | توضیح |
|---------------|------------|--------------|-------|
| 0 (Zero-shot) | ~۴۰٪ | کم | فقط عبارت "Let's think step by step" |
| 2 | ~۶۰٪ | متوسط | دو مثال متنوع |
| 4 | ~۷۴٪ | متوسط-زیاد | چهار مثال از انواع مختلف مسائل |
| 8 | ~۷۸٪ | زیاد | هشت مثال متنوع |
| 16+ | ~۸۰٪ | بسیار زیاد | بازده کاهشی (diminishing returns) |

### ۳.۳ Auto-CoT

**Auto-CoT** (Zhang et al., 2022) فرایند تولید دستی مثال‌ها را خودکار می‌کند. دو گام اصلی:

1. **تقسیم‌بندی سوالات (Question Clustering):** سوالات ورودی را بر اساس شباهت به خوشه‌هایی تقسیم می‌کند.
2. **تولید مثال‌های استدلال (Demonstration Generation):** از هر خوشه یک نمونه را انتخاب کرده و با Zero-shot CoT برای آن استدلال می‌سازد.

```text
Auto-CoT Pipeline:

┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ مجموعه‌ای از │───▶│ خوشه‌بندی    │───▶│ انتخاب نمونه   │───▶│ تولید        │
│ سوالات       │    │ (Clustering) │    │ (Sampling)    │    │ استدلال      │
└─────────────┘    └──────────────┘    └───────────────┘    │ (Zero-shot   │
                                                             │  CoT)        │
                                                             └──────┬───────┘
                                                                    ▼
                                                            ┌──────────────┐
                                                            │ Few-shot CoT │
                                                            │ پرامپت نهایی  │
                                                            └──────────────┘
```

**الگوریتم Auto-CoT:**

```text
ورودی: مجموعه سوالات Q = {q1, q2, ..., qn}
خروجی: مجموعه demonstration‌های D = {d1, d2, ..., dk}

1. خوشه‌بندی: C = KMeansClustering(Q, k)
   - هر سوال qi به یک خوشه cj ∈ {1, ..., k} تعلق می‌گیرد

2. برای هر خوشه cj:
   a. انتخاب سوال نزدیک‌ترین به مرکز خوشه: q_rep = nearest_to_center(cj)
   b. تولید استدلال: r_j = LLM_zero_shot_cot(q_rep)
      - پرامپت: "Q: {q_rep}\nA: Let's think step by step. {r_j}"
   c. ساخت demonstration: d_j = {"question": q_rep, "reasoning": r_j}

3. همه D = {d1, ..., dk} را به عنوان few-shot examples
   به پرامپت نهایی اضافه کن
```

### ۳.۴ پیاده‌سازی در پایتون

```python
"""
Chain-of-Thought Reasoning — پیاده‌سازی در پایتون
شامل Zero-shot CoT، Few-shot CoT، و Auto-CoT
"""

import re
from typing import List, Dict, Optional

# ============================================================================
# ۱. Zero-shot CoT
# ============================================================================

def zero_shot_cot(llm, question: str, trigger: str = "Let's think step by step.") -> str:
    """
    اجرای Zero-shot Chain-of-Thought.

    Args:
        llm: تابع یا شیءای که پرامپت می‌گیرد و متن برمی‌گرداند
        question: سوال کاربر
        trigger: عبارت ماشه‌ای CoT

    Returns:
        پاسخ نهایی
    """
    prompt = f"Q: {question}\nA: {trigger}\n"

    # فراخوانی LLM — در عمل اینجا API صدا زده می‌شود
    raw_response = llm(prompt)

    # استخراج پاسخ نهایی (معمولاً بعد از "therefore" یا "answer")
    final_answer = extract_answer(raw_response)

    return {
        "question": question,
        "reasoning": raw_response,
        "answer": final_answer
    }


def extract_answer(text: str) -> str:
    """استخراج پاسخ نهایی از متن استدلال."""
    # الگوهای رایج برای پاسخ نهایی
    patterns = [
        r"[Tt]he answer is (\d+)",
        r"[Ss]o the answer is (.+?)[.\n]",
        r"[Tt]herefore,? (.+?)[.\n]",
        r"answer:?\s*(.+?)[\n.]",
        r"جواب\s*(.+?)[\n.]",
        r"پاسخ\s*(.+?)[\n.]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    # اگر الگویی پیدا نشد، آخرین جمله را برمی‌گردانیم
    sentences = text.strip().split(".")
    return sentences[-1].strip() if sentences else text.strip()


# ============================================================================
# ۲. Few-shot CoT
# ============================================================================

class FewShotExample:
    """یک مثال برای Few-shot CoT."""
    def __init__(self, question: str, reasoning: str, answer: str):
        self.question = question
        self.reasoning = reasoning
        self.answer = answer

    def format(self) -> str:
        return f"Q: {self.question}\nA: {self.reasoning}\nTherefore the answer is {self.answer}."


def few_shot_cot(llm, question: str, examples: List[FewShotExample]) -> str:
    """
    اجرای Few-shot Chain-of-Thought.

    Args:
        llm: تابع فراخوانی LLM
        question: سوال جدید
        examples: لیست مثال‌های استدلال

    Returns:
        پاسخ نهایی
    """
    # ساخت پرامپت: چند مثال + سوال جدید
    prompt_parts = []
    for ex in examples:
        prompt_parts.append(ex.format())
    prompt_parts.append(f"Q: {question}\nA:")

    prompt = "\n\n".join(prompt_parts)

    raw_response = llm(prompt)
    final_answer = extract_answer(raw_response)

    return {
        "question": question,
        "reasoning": raw_response,
        "answer": final_answer
    }


# ============================================================================
# ۳. Auto-CoT
# ============================================================================

class AutoCOT:
    """
    Auto Chain-of-Thought — تولید خودکار demonstrationها.
    """
    def __init__(self, llm, n_clusters: int = 5):
        self.llm = llm
        self.n_clusters = n_clusters
        self.demonstrations: List[FewShotExample] = []

    def build_demonstrations(self, questions: List[str]) -> List[FewShotExample]:
        """
        از روی مجموعه سوالات، demonstrationهای استدلال را می‌سازد.

        در عمل اینجا خوشه‌بندی (مثلاً با Sentence Transformers) انجام می‌شود.
        برای سادگی، سوالات دسته‌بندی فرضی شده‌اند.
        """
        # --- گام ۱: خوشه‌بندی سوالات (شبیه‌سازی) ---
        clusters = self._cluster_questions(questions)

        # --- گام ۲: برای هر خوشه، یک نمونه انتخاب و استدلال تولید کن ---
        for cluster_id, cluster_questions in clusters.items():
            if not cluster_questions:
                continue

            # انتخاب نزدیک‌ترین سوال به مرکز خوشه
            rep_question = cluster_questions[0]  # ساده‌سازی

            # تولید استدلال با Zero-shot CoT
            result = zero_shot_cot(self.llm, rep_question)
            reasoning = result["reasoning"]
            answer = result["answer"]

            # ذخیره به عنوان demonstration
            self.demonstrations.append(
                FewShotExample(rep_question, reasoning, answer)
            )

        return self.demonstrations

    def _cluster_questions(self, questions: List[str]) -> Dict[int, List[str]]:
        """
        خوشه‌بندی سوالات — اینجا یک پیاده‌سازی ساده.
        در عمل از embedding + KMeans استفاده کنید.
        """
        # شبیه‌سازی: سوالات را به n_clusters گروه تقسیم می‌کنیم
        clusters = {}
        for i, q in enumerate(questions):
            cluster_id = i % self.n_clusters
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(q)
        return clusters

    def answer(self, question: str) -> str:
        """پاسخ به سوال با استفاده از demonstrationهای ساخته‌شده."""
        if not self.demonstrations:
            # Fallback به Zero-shot
            return zero_shot_cot(self.llm, question)

        return few_shot_cot(self.llm, question, self.demonstrations)


# ============================================================================
# ۴. مثال استفاده
# ============================================================================

def mock_llm(prompt: str) -> str:
    """شبیه‌ساز LLM برای تست."""
    if "۲۵ عدد سیب" in prompt:
        return (
            "Let's think step by step. "
            "ابتدا ۲۵ سیب دارم. ۱۳ تا را می‌خورم: ۲۵ - ۱۳ = ۱۲. "
            "سپس ۷ تا به دوستم می‌دهم: ۱۲ - ۷ = ۵. "
            "Therefore the answer is 5."
        )
    if "۵۳۰" in prompt and "۴۲۰" in prompt:
        return "۵۳۰ - ۴۲۰ = ۱۱۰. The answer is 110."
    return "Let's think step by step. 5 + 3 = 8. The answer is 8."


if __name__ == "__main__":
    # Zero-shot CoT
    print("=== Zero-shot CoT ===")
    result = zero_shot_cot(mock_llm, "۲۵ عدد سیب دارم. ۱۳ تا را می‌خورم و ۷ تا می‌دهم.")
    print(f"سوال: {result['question']}")
    print(f"استدلال: {result['reasoning']}")
    print(f"پاسخ: {result['answer']}\n")

    # Few-shot CoT
    print("=== Few-shot CoT ===")
    examples = [
        FewShotExample(
            "راجر ۵ توپ دارد. ۲ قوطی ۳ تایی می‌خرد.",
            "۵ + (۲ × ۳) = ۵ + ۶ = ۱۱",
            "۱۱"
        )
    ]
    result = few_shot_cot(mock_llm, "اینترنت ۵۳۰ و ۴۲۰", examples)
    print(f"پاسخ: {result['answer']}\n")

    # Auto-CoT
    print("=== Auto-CoT ===")
    auto_cot = AutoCOT(mock_llm, n_clusters=3)
    auto_cot.build_demonstrations([
        "۲+۲ چقدر است؟",
        "۱۰-۳ چقدر است؟",
        "۵×۴ چقدر است؟",
        "۲۰÷۴ چقدر است؟",
        "۱۵+۷ چقدر است؟",
    ])
    print(f"تعداد demonstrationهای ساخته‌شده: {len(auto_cot.demonstrations)}")
    for d in auto_cot.demonstrations:
        print(f"  - {d.question}: {d.reasoning}")
```

---

## ۴. Tree-of-Thought (ToT) — درخت تفکر

**Tree-of-Thoughts** (Yao et al., 2023) فرایند استدلال را به عنوان یک **درخت جستجو** مدل می‌کند. هر گره درخت یک "حالت تفکر" (state of thought) است و یال‌ها انتقال بین این حالت‌ها را نشان می‌دهند.

```text
ساختار درخت تفکر (ToT):

                                 ┌──────────┐
                                 │  سوال    │
                                 │ (Root)   │
                                 └────┬─────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
               ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
               │ فکر ۱.۱  │      │ فکر ۱.۲  │      │ فکر ۱.۳  │
               │ (گام ۱  │      │ (گام ۱  │      │ (گام ۱  │
               │  مختلف) │      │  مختلف) │      │  مختلف) │
               └────┬────┘      └────┬────┘      └────┬────┘
                    │                 │                 │
              ┌─────┴──────┐    ┌─────┴──────┐         │
              │            │    │            │         │
         ┌────┴────┐  ┌────┴────┐  ...     ...        ...
         │ فکر ۲.۱ │  │ فکر ۲.۲ │
         │ (گام ۲) │  │ (گام ۲) │
         └────┬────┘  └────┬────┘
              │             │
         ┌────┴────┐  ┌────┴────┐
         │پاسخ A   │  │پاسخ B   │  ← برگ‌ها = پاسخ‌های نهایی
         └─────────┘  └─────────┘
```

### ۴.۱ BFS در ToT

**BFS (Breadth-First Search)** در ToT همه‌ی گره‌های یک سطح را قبل از رفتن به سطح بعدی بررسی می‌کند. مناسب برای مسائلی که عرض جستجوی محدودی دارند.

```text
BFS در ToT:

گام ۱:                              [Root]
                                    /    |    \
گام ۲:                         [۱.۱]  [۱.۲]  [۱.۳]    ← بررسی همه‌ی گام‌های اول
                                 |    ╱    ╲    |
گام ۳:                      [۲.۱] [۲.۲] [۲.۳] [۲.۴]  ← بررسی همه‌ی گام‌های دوم
                                 |    |    |    |
گام ۴:                      [A]  [B]  [C]  [D]       ← انتخاب بهترین برگ

ویژگی‌ها:
- کاوش کامل (complete exploration)
- حافظه‌بر (memory intensive at wide levels)
- مناسب برای: مسائل با عرض جستجوی ≤ ۱۰
```

**الگوریتم BFS-ToT:**

```text
BFS-ToT(question, max_levels, beam_width):
    queue = [{parent: null, thought: question, level: 0, value: 0}]
    solutions = []

    while queue not empty and level < max_levels:
        current = queue.pop()

        if is_solution(current):
            solutions.append(current)
            continue

        # تولید k فرزند از گره فعلی
        children = generate_k_thoughts(current, k=beam_width)

        # ارزیابی هر فرزند
        for child in children:
            child.value = evaluate_thought(child)

        # مرتب‌سازی بر اساس ارزش و نگه‌داشتن بهترین‌ها
        children.sort(by=value, descending)
        queue.extend(children[:beam_width])  # فقط beam_width تا

    return best(solutions)
```

### ۴.۲ DFS در ToT

**DFS (Depth-First Search)** در ToT یک شاخه را تا انتها دنبال می‌کند، سپس به عقب برمی‌گردد. مناسب برای مسائل با عمق جستجوی زیاد.

```text
DFS در ToT:

گام ۱:  [Root] → [۱.۱] (عمیق شو در اولین انتخاب)
گام ۲:  [Root] → [۱.۱] → [۲.۱]
گام ۳:  [Root] → [۱.۱] → [۲.۱] → [A] ← پاسخ یافت شد
گام ۴:  برگشت به [۲.۱] ← بررسی گزینه‌های دیگر
گام ۵:  [Root] → [۱.۱] → [۲.۲]
...

ویژگی‌ها:
- حافظه‌کار (memory efficient)
- ممکن است در شاخه‌های بی‌نهایت گیر کند
- مناسب برای: مسائل با عمق زیاد و عرض کم
```

**الگوریتم DFS-ToT:**

```text
DFS-ToT(node, max_depth, current_depth):
    if current_depth >= max_depth:
        return evaluate(node)

    if is_solution(node):
        return node

    best_value = -inf
    best_child = None

    # تولید فرزندان
    children = generate_k_thoughts(node, k=beam_width)

    for child in children:
        child.value = evaluate_thought(child)

        # هرس: اگر فرزند ارزش کافی ندارد، نادیده بگیر
        if child.value < prune_threshold:
            continue

        # جستجوی عمقی
        result = DFS-ToT(child, max_depth, current_depth + 1)

        if result.value > best_value:
            best_value = result.value
            best_child = result

    return best_child if best_child else node
```

### ۴.۳ زمان انشعاب و هرس

**قوانین انشعاب (Branching Rules):**

| شرط | توضیح | مثال |
|-----|-------|------|
| **عدم قطعیت بالا** | وقتی LLM بین چند گزینه مردد است | «می‌تواند روش A یا B باشد» |
| **مسیرهای جایگزین** | وقتی راه‌حل‌های متفاوتی ممکن است | حل معادله با دو روش مختلف |
| **نیاز به کاوش** | وقتی فضای مسئله ناآشناست | مسئله‌ی جدید و پیچیده |
| **بازخورد محیط** | وقتی Observation نشان می‌دهد مسیر فعلی ممکن نیست | خطای API، داده‌ی ناقص |

**قوانین هرس (Pruning Rules):**

| شرط | توضیح | پیاده‌سازی |
|-----|-------|-----------|
| **ارزش پایین** | ارزیابی LLM از گره کمتر از آستانه | `if value < threshold: prune` |
| **تشابه بالا** | دو گره تفکر مشابه تولید می‌کنند | `if similarity(a, b) > 0.9: prune one` |
| **عمق زیاد** | گره در عمق بیش از حد مجاز | `if depth > max_depth: prune` |
| **حلقه** | بازگشت به حالتی مشابه حالت قبلی | `if state in visited: prune` |
| **تناقض** | گره با حقایق قطعی تناقض دارد | `if contradicts(fact, thought): prune` |

```text
تصمیم‌گیری انشعاب vs هرس:

    ┌────────────────────────────┐
    │  ارزیابی گره فعلی          │
    │                            │
    │  value = evaluate(node)    │
    └────────────────────────────┘
              │
              ▼
    ┌────────────────────────────┐
    │  value > high_threshold?   │── Yes ──▶ ادامه در همین مسیر (بدون انشعاب)
    └────────────────────────────┘
              │ No
              ▼
    ┌────────────────────────────┐
    │  value > low_threshold?    │── Yes ──▶ انشعاب: k فرزند جدید
    └────────────────────────────┘
              │ No
              ▼
    ┌────────────────────────────┐
    │  هرس: این شاخه را رها کن   │
    └────────────────────────────┘
```

### ۴.۴ پیاده‌سازی در پایتون

```python
"""
Tree-of-Thought (ToT) Reasoning — پیاده‌سازی در پایتون
شامل BFS-ToT و DFS-ToT
"""

from typing import List, Optional, Callable
from dataclasses import dataclass, field
import math
import itertools


@dataclass
class ThoughtNode:
    """یک گره در درخت تفکر."""
    content: str                         # محتوای این گام تفکر
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = field(default_factory=list)
    value: float = 0.0                   # ارزش (برای هرس و انتخاب)
    depth: int = 0
    is_solution: bool = False

    def path_to_root(self) -> List[str]:
        """مسیر از ریشه تا این گره."""
        path = []
        node = self
        while node:
            path.insert(0, node.content)
            node = node.parent
        return path

    def __repr__(self) -> str:
        return f"ThoughtNode(depth={self.depth}, value={self.value:.2f}, content='{self.content[:40]}...')"


class TreeOfThought:
    """
    Tree-of-Thought جستجوگر.
    از دو استراتژی پشتیبانی می‌کند: BFS و DFS.
    """

    def __init__(
        self,
        thought_generator: Callable,       # تابع تولیدکننده‌ی گام‌های تفکر
        thought_evaluator: Callable,       # تابع ارزیاب ارزش هر گام
        solution_checker: Callable,        # تابع تشخیص راه‌حل نهایی
        max_depth: int = 5,
        branch_factor: int = 3,
        beam_width: int = 3,
        prune_threshold: float = 0.3,
    ):
        self.thought_generator = thought_generator
        self.thought_evaluator = thought_evaluator
        self.solution_checker = solution_checker
        self.max_depth = max_depth
        self.branch_factor = branch_factor
        self.beam_width = beam_width
        self.prune_threshold = prune_threshold
        self.total_nodes = 0

    def solve_bfs(self, question: str) -> ThoughtNode:
        """
        حل مسئله با BFS (Breadth-First Search).

        همه‌ی گره‌های یک سطح را بررسی می‌کند و
        بهترین‌ها را تا سطح بعدی نگه می‌دارد (Beam Search).
        """
        root = ThoughtNode(content=question, depth=0)
        current_level = [root]
        self.total_nodes = 1

        for depth in range(self.max_depth):
            next_level = []

            for node in current_level:
                if node.is_solution:
                    return node

                # تولید فرزندان (انشعاب)
                thoughts = self.thought_generator(node, k=self.branch_factor)

                for thought_content in thoughts:
                    child = ThoughtNode(
                        content=thought_content,
                        parent=node,
                        depth=depth + 1
                    )

                    # ارزیابی ارزش
                    child.value = self.thought_evaluator(child)
                    child.is_solution = self.solution_checker(child)

                    # هرس: گره‌های کم‌ارزش حذف می‌شوند
                    if child.value >= self.prune_threshold:
                        node.children.append(child)
                        next_level.append(child)
                        self.total_nodes += 1

            if not next_level:
                break  # همه‌ی گره‌ها هرس شدند

            # Beam Search: فقط beam_width تا از بهترین‌ها را نگه دار
            next_level.sort(key=lambda n: n.value, reverse=True)
            current_level = next_level[:self.beam_width]

        # بهترین گره از آخرین سطح را برگردان
        if current_level:
            return max(current_level, key=lambda n: n.value)
        return root

    def solve_dfs(self, question: str) -> Optional[ThoughtNode]:
        """
        حل مسئله با DFS (Depth-First Search).

        عمقی پیش می‌رود و با Backtracking برمی‌گردد.
        """
        root = ThoughtNode(content=question, depth=0)
        self.total_nodes = 1
        self.best_solution = None
        self.best_value = -math.inf

        def dfs(node: ThoughtNode):
            if node.is_solution:
                if node.value > self.best_value:
                    self.best_solution = node
                    self.best_value = node.value
                return

            if node.depth >= self.max_depth:
                return

            # تولید فرزندان
            thoughts = self.thought_generator(node, k=self.branch_factor)

            for thought_content in thoughts:
                child = ThoughtNode(
                    content=thought_content,
                    parent=node,
                    depth=node.depth + 1
                )
                child.value = self.thought_evaluator(child)
                child.is_solution = self.solution_checker(child)

                # هرس در DFS
                if child.value < self.prune_threshold:
                    continue

                node.children.append(child)
                self.total_nodes += 1

                dfs(child)

                # اگر راه‌حل خوبی پیدا شد، بقیه‌ی شاخه‌ها را نادیده بگیر
                if self.best_solution and self.best_value > 0.9:
                    return

        dfs(root)
        return self.best_solution or root


# ============================================================================
# مثال استفاده: حل مسئله‌ی "۲۴ بازی ریاضی"
# ============================================================================

def example_24_game():
    """
    مثال بازی ۲۴: با اعداد [۴, ۷, ۸, ۸] به ۲۴ برسید
    با استفاده از جمع، تفریق، ضرب و تقسیم.
    """

    def generate_thoughts(node: ThoughtNode, k: int) -> List[str]:
        """تولید گام‌های بعدی تفکر برای بازی ۲۴."""
        if node.depth == 0:
            # اولین گام: انتخاب دو عدد و یک عمل
            return [
                "Try: 4 × 7 = 28, remaining: [8, 8, 28]",
                "Try: 8 × 8 = 64, remaining: [4, 7, 64]",
                "Try: 8 - 4 = 4, remaining: [7, 8, 4]",
                "Try: 8 + 7 = 15, remaining: [4, 8, 15]",
                "Try: 8 ÷ 4 = 2, remaining: [7, 8, 2]",
            ][:k]
        elif node.depth == 1:
            return [
                "Try: 28 - 8 = 20, remaining: [8, 20]",
                "Try: 28 + 8 = 36, remaining: [8, 36]",
                "Try: 64 - 7 = 57, remaining: [4, 57]",
            ][:k]
        elif node.depth == 2:
            return [
                "Try: 20 + 4 = 24 → SOLUTION!",
                "Try: 36 - 12 = 24 → SOLUTION!",
            ][:k]
        return ["No more steps."]

    def evaluate_thought(node: ThoughtNode) -> float:
        """ارزیابی ارزش یک گام تفکر."""
        content = node.content.lower()
        if "solution" in content:
            return 1.0
        if "remaining" in content:
            if "۲۴" in content or "24" in content:
                return 0.9
        if "error" in content or "impossible" in content:
            return 0.0
        return 0.5

    def check_solution(node: ThoughtNode) -> bool:
        return "solution" in node.content.lower() or "24" in node.content == "24"

    tot = TreeOfThought(
        thought_generator=generate_thoughts,
        thought_evaluator=evaluate_thought,
        solution_checker=check_solution,
        max_depth=3,
        branch_factor=3,
        beam_width=2,
        prune_threshold=0.2,
    )

    print("=== حل بازی ۲۴ با BFS-ToT ===")
    result = tot.solve_bfs("با [۴, ۷, ۸, ۸] به ۲۴ برسید")
    path = result.path_to_root()
    print(f"گره‌های جستجو: {tot.total_nodes}")
    print(f"عمق راه‌حل: {result.depth}")
    for i, step in enumerate(path):
        print(f"  گام {i}: {step}")

    print(f"\n=== حل بازی ۲۴ با DFS-ToT ===")
    tot2 = TreeOfThought(
        thought_generator=generate_thoughts,
        thought_evaluator=evaluate_thought,
        solution_checker=check_solution,
        max_depth=3,
        branch_factor=3,
        beam_width=2,
        prune_threshold=0.2,
    )
    result2 = tot2.solve_dfs("با [۴, ۷, ۸, ۸] به ۲۴ برسید")
    path2 = result2.path_to_root()
    print(f"گره‌های جستجو: {tot2.total_nodes}")
    for i, step in enumerate(path2):
        print(f"  گام {i}: {step}")
```

---

## ۵. Graph-of-Thought (GoT) — گراف تفکر

**Graph-of-Thoughts** (Besta et al., 2023) درخت تفکر را به یک **گراف جهت‌دار** (Directed Graph) تعمیم می‌دهد. گره‌های تفکر می‌توانند چندین والد داشته باشند (تجمیع) و نتایج میانی می‌توانند در گره‌های بعدی ترکیب شوند.

### ۵.۱ ساختار گراف

```text
Graph-of-Thought:

                ┌──────────────────────────────────────────┐
                │  تفاوت اصلی: گره‌ها می‌توانند چند والد    │
                │  داشته باشند → تجمیع اطلاعات از چند مسیر  │
                └──────────────────────────────────────────┘

                        ┌──────────┐
                        │  سوال    │
                        └────┬─────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
         │ تحلیل ۱ │   │ تحلیل ۲ │   │ تحلیل ۳ │
         └────┬────┘   └────┬────┘   └────┬────┘
              │              │              │
              │         ┌────┴────┐         │
              │         │ نتیجه  │         │
              │         │ میانی  │         │
              │         └────┬────┘         │
              │              │              │
              └──────────────┼──────────────┘
                             │
                        ┌────┴────┐
                        │ تجمیع   │  ← این گره اطلاعات را
                        │ (Agg)   │     از چند مسیر جمع می‌کند
                        └────┬────┘
                             │
                        ┌────┴────┐
                        │ پاسخ   │
                        │ نهایی   │
                        └─────────┘
```

**انواع گره در GoT:**

| نوع گره | نماد | توضیح |
|---------|------|-------|
| **گره ورودی** (Input) | ● | سوال یا مسئله‌ی اصلی |
| **گره تفکر** (Thought) | ◯ | یک گام استدلال میانی |
| **گره تجمیع** (Aggregation) | ◉ | ترکیب چندین گره تفکر |
| **گره خروجی** (Output) | ◆ | پاسخ نهایی |

**عملگرهای GoT:**

| عملگر | توضیح | نماد |
|-------|-------|------|
| **تولید** (Generate) | یک گره جدید از یک گره موجود تولید می‌کند | → |
| **تجمیع** (Aggregate) | چند گره را در یک گره ترکیب می‌کند | →◉← |
| **بهبود** (Refine) | یک گره را با اطلاعات جدید بهبود می‌دهد | ⇝ |
| **کاهش** (Reduce) | مجموعه‌ای از گره‌ها را به یک پاسخ خلاصه می‌کند | ⇒ |

### ۵.۲ تجمیع (Aggregation)

تجمیع قلب GoT است. سه روش اصلی:

```text
روش‌های تجمیع در GoT:

۱. Majority Vote (رای اکثریت):
   ┌────────┐  ┌────────┐  ┌────────┐
   │ پاسخ A │  │ پاسخ B │  │ پاسخ C │
   └───┬────┘  └───┬────┘  └───┬────┘
       └──────────┼───────────┘
                  ▼
            ┌──────────┐
            │ رای‌گیری  │ ← پاسخ با بیشترین رأی
            └──────────┘

۲. Weighted Aggregation (تجمیع وزنی):
   ┌────────┐       ┌────────┐       ┌────────┐
   │ تحلیل ۱│       │ تحلیل ۲│       │ تحلیل ۳│
   │ w=0.5  │       │ w=0.3  │       │ w=0.2  │
   └───┬────┘       └───┬────┘       └───┬────┘
       └───────────────┼────────────────┘
                       ▼
               ┌──────────────┐
               │ ∑ (value × w) │ ← ترکیب وزنی
               └──────────────┘

۳. Critical Path (مسیر بحرانی):
   ┌────────┐    ┌────────┐    ┌────────┐
   │ گام A  │───▶│ گام B  │───▶│ پاسخ  │ ← مسیر اصلی
   └────────┘    └────────┘    └────────┘
        │                        ▲
        ▼                        │
   ┌────────┐                    │
   │ گام A' │────────────────────┘ ← مسیر فرعی (کمک به B)
   └────────┘
```

### ۵.۳ پیاده‌سازی در پایتون

```python
"""
Graph-of-Thought (GoT) Reasoning — پیاده‌سازی در پایتون
شامل ساختار گراف، تولید گره، تجمیع و جستجو
"""

from typing import List, Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import random


class NodeType(Enum):
    """انواع گره در GoT."""
    INPUT = "input"
    THOUGHT = "thought"
    AGGREGATION = "aggregation"
    OUTPUT = "output"


class AggregationMethod(Enum):
    """روش‌های تجمیع در GoT."""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_SUM = "weighted_sum"
    CRITICAL_PATH = "critical_path"
    LLM_SYNTHESIS = "llm_synthesis"


@dataclass
class GoTNode:
    """یک گره در گراف تفکر."""
    id: str = field(default_factory=lambda: f"n_{uuid.uuid4().hex[:8]}")
    content: str = ""
    node_type: NodeType = NodeType.THOUGHT
    parent_ids: Set[str] = field(default_factory=set)
    children_ids: Set[str] = field(default_factory=set)
    weight: float = 1.0
    value: float = 0.0
    metadata: Dict = field(default_factory=dict)


class GraphOfThought:
    """
    Graph-of-Thought engine.
    امکان ساخت گراف دلخواه از گره‌های تفکر و تجمیع آن‌ها.
    """

    def __init__(self, llm: Optional[Callable] = None):
        self.nodes: Dict[str, GoTNode] = {}
        self.llm = llm or self._default_llm

    def add_node(self, node: GoTNode) -> str:
        """اضافه کردن یک گره به گراف."""
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, from_id: str, to_id: str):
        """اضافه کردن یال جهت‌دار بین دو گره."""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].children_ids.add(to_id)
            self.nodes[to_id].parent_ids.add(from_id)

    def generate_thoughts(
        self,
        parent_id: str,
        k: int = 3,
        prompt_template: str = "با توجه به '{content}'، {k} گام فکر بعدی را تولید کن:"
    ) -> List[str]:
        """تولید k گره تفکر جدید از یک گره والد."""
        parent = self.nodes[parent_id]
        prompt = prompt_template.format(content=parent.content, k=k)

        # فراخوانی LLM برای تولید k ایده
        raw = self.llm(prompt)
        thoughts = raw.strip().split("\n")[:k]

        # ساختن گره‌های جدید
        new_nodes = []
        for thought in thoughts:
            node = GoTNode(
                content=thought.strip(),
                node_type=NodeType.THOUGHT,
                parent_ids={parent_id}
            )
            self.add_node(node)
            self.add_edge(parent_id, node.id)
            new_nodes.append(node)

        return new_nodes

    def aggregate(
        self,
        node_ids: List[str],
        method: AggregationMethod = AggregationMethod.MAJORITY_VOTE,
        weights: Optional[List[float]] = None
    ) -> GoTNode:
        """
        تجمیع چند گره در یک گره جدید.

        Args:
            node_ids: لیست id گره‌هایی که باید تجمیع شوند
            method: روش تجمیع
            weights: اوزان اختیاری برای WeightedSum

        Returns:
            گره تجمیع جدید
        """
        nodes_to_aggregate = [self.nodes[nid] for nid in node_ids if nid in self.nodes]

        if not nodes_to_aggregate:
            raise ValueError("No valid nodes to aggregate")

        if method == AggregationMethod.MAJORITY_VOTE:
            aggregated = self._majority_vote(nodes_to_aggregate)
        elif method == AggregationMethod.WEIGHTED_SUM:
            aggregated = self._weighted_sum(nodes_to_aggregate, weights)
        elif method == AggregationMethod.CRITICAL_PATH:
            aggregated = self._critical_path(nodes_to_aggregate)
        elif method == AggregationMethod.LLM_SYNTHESIS:
            aggregated = self._llm_synthesis(nodes_to_aggregate)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

        # ساختن گره تجمیع
        agg_node = GoTNode(
            content=aggregated,
            node_type=NodeType.AGGREGATION,
            parent_ids=set(node_ids)
        )
        self.add_node(agg_node)

        # اتصال گره‌های والد به گره تجمیع
        for nid in node_ids:
            self.add_edge(nid, agg_node.id)

        return agg_node

    def _majority_vote(self, nodes: List[GoTNode]) -> str:
        """رای اکثریت — محتوایی که بیشتر تکرار شده را برمی‌گرداند."""
        content_counts: Dict[str, int] = {}
        for node in nodes:
            content_counts[node.content] = content_counts.get(node.content, 0) + 1
        return max(content_counts, key=content_counts.get)

    def _weighted_sum(
        self, nodes: List[GoTNode], weights: Optional[List[float]] = None
    ) -> str:
        """تجمیع وزنی — اعداد را با وزن ترکیب می‌کند."""
        if not weights:
            weights = [node.weight for node in nodes]
        total_weight = sum(weights)
        weighted_values = []
        for node, w in zip(nodes, weights):
            try:
                val = float(node.content.strip())
                weighted_values.append(val * (w / total_weight))
            except ValueError:
                weighted_values.append(0)
        return f"{sum(weighted_values):.2f}"

    def _critical_path(self, nodes: List[GoTNode]) -> str:
        """مسیر بحرانی — گره با بالاترین ارزش را برمی‌گرداند."""
        best = max(nodes, key=lambda n: n.value)
        return f"[CRITICAL] {best.content}"

    def _llm_synthesis(self, nodes: List[GoTNode]) -> str:
        """تجمیع با LLM — از مدل می‌خواهد دیدگاه‌ها را ترکیب کند."""
        contents = "\n".join([f"- {n.content}" for n in nodes])
        prompt = (
            f"دیدگاه‌های زیر را در یک پاسخ منسجم ترکیب کن:\n\n"
            f"{contents}\n\n"
            f"پاسخ ترکیبی:"
        )
        return self.llm(prompt)

    def solve_parallel(self, question: str, n_paths: int = 3) -> GoTNode:
        """
        حل مسئله با رویکرد موازی GoT:
        ۱. تولید n مسیر موازی
        ۲. تجمیع نتایج
        ۳. استخراج پاسخ نهایی
        """
        # گره ورودی
        input_node = GoTNode(content=question, node_type=NodeType.INPUT)
        input_id = self.add_node(input_node)

        # تولید n مسیر موازی
        path_nodes = []
        for i in range(n_paths):
            child = GoTNode(
                content=f"Path {i+1}: Ai?",
                node_type=NodeType.THOUGHT,
                parent_ids={input_id}
            )
            child_id = self.add_node(child)
            self.add_edge(input_id, child_id)

            # عمیق‌تر رفتن در هر مسیر
            sub = GoTNode(
                content=f"Path {i+1}: Ai?",
                node_type=NodeType.THOUGHT,
                parent_ids={child_id}
            )
            sub_id = self.add_node(sub)
            self.add_edge(child_id, sub_id)
            path_nodes.append(sub)

        # تجمیع همه مسیرها
        agg = self.aggregate(
            [n.id for n in path_nodes],
            method=AggregationMethod.LLM_SYNTHESIS
        )

        # گره خروجی
        output = GoTNode(
            content=agg.content,
            node_type=NodeType.OUTPUT,
            parent_ids={agg.id}
        )
        output_id = self.add_node(output)
        self.add_edge(agg.id, output_id)

        return output

    def visualize(self) -> str:
        """خروجی متنی از ساختار گراف."""
        lines = ["Graph-of-Thought Structure:", "=" * 50]
        for nid, node in self.nodes.items():
            node_type = node.node_type.value
            parents = ", ".join(node.parent_ids) or "None"
            children = ", ".join(node.children_ids) or "None"
            lines.append(
                f"[{node_type}] {nid}: "
                f"'{node.content[:30]}...' | "
                f"Parents: [{parents}] | "
                f"Children: [{children}] | "
                f"Weight: {node.weight}"
            )
        return "\n".join(lines)

    def _default_llm(self, prompt: str) -> str:
        """LLM پیش‌فرض (مک)."""
        return (
            "Based on the analysis, here are some thoughts:\n"
            "1. First approach using direct computation\n"
            "2. Alternative approach using decomposition\n"
            "3. Verification through reverse reasoning"
        )


# ============================================================================
# مثال استفاده
# ============================================================================

if __name__ == "__main__":
    got = GraphOfThought()

    # حل یک مسئله با رویکرد موازی GoT
    print("=== حل مسئله با GoT ===")
    answer = got.solve_parallel(
        "اگر ۳ قلم کالا به قیمت ۱۵، ۲۲ و ۳۰ هزار تومان بخریم "
        "و ۲۰٪ تخفیف بگیریم، مجموع چقدر می‌شود؟",
        n_paths=3
    )
    print(f"پاسخ نهایی: {answer.content}")

    # نمایش ساختار گراف
    print("\n" + got.visualize())

    # نمایش آمار
    print(f"\nآمار گراف:")
    print(f"  تعداد کل گره‌ها: {len(got.nodes)}")
    print(f"  گره‌های ورودی: {sum(1 for n in got.nodes.values() if n.node_type == NodeType.INPUT)}")
    print(f"  گره‌های تفکر: {sum(1 for n in got.nodes.values() if n.node_type == NodeType.THOUGHT)}")
    print(f"  گره‌های تجمیع: {sum(1 for n in got.nodes.values() if n.node_type == NodeType.AGGREGATION)}")
    print(f"  گره‌های خروجی: {sum(1 for n in got.nodes.values() if n.node_type == NodeType.OUTPUT)}")
```

---

## ۶. Self-Consistency — خودسازگاری

**Self-Consistency** (Wang et al., 2022) یک روش **ensemble** بر روی CoT است. ایده: به جای یک مسیر استدلال، **چندین مسیر مختلف** نمونه‌گیری می‌کنیم و با رای‌گیری به پاسخ نهایی می‌رسیم.

```text
Self-Consistency Pipeline:

                    ┌──────────────┐
                    │    سوال      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
     │مسیر ۱   │     │مسیر ۲   │     │مسیر ۳   │
     │CoT      │     │CoT      │  ...│CoT      │
     └────┬────┘     └────┬────┘     └────┬────┘
          │                │                │
     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
     │پاسخ A   │     │پاسخ B   │     │پاسخ A   │
     └─────────┘     └─────────┘     └─────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    ┌──────────────┐
                    │   رای‌گیری   │
                    │ A: ۲ رأی     │
                    │ B: ۱ رأی     │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ پاسخ نهایی: A│
                    └──────────────┘
```

### ۶.۱ مکانیزم رای‌گیری

| روش رای‌گیری | توضیح | مزیت | عیب |
|-------------|-------|------|-----|
| **Majority Vote** | پاسخی که بیشترین تکرار را دارد | ساده و سریع | وزن پاسخ‌ها یکسان است |
| **Weighted Vote** | هر پاسخ بر اساس اطمینان مسیر وزن‌دهی می‌شود | دقیق‌تر | نیاز به تخمین اطمینان |
| **Normalized Weighted** | نرمال‌سازی احتمالاتی پاسخ‌ها | پایدارتر | محاسباتی‌تر |
| **Marginal** | جمع‌زنی احتمالات تمام مسیرها | از نظر آماری بهینه | گران‌تر |

**تأثیر تعداد مسیرها بر دقت (GSM8K):**

```text
دقت (%)
  ^
  |   ● (78%)
  |      ● (76%)
  |         ● (74%)
  |            ● (72%)
  |                ● (70%)
  +-------------------------------------▶ تعداد مسیرها
  1   2   3   4   5   6   7   8   9  10

  مشاهده: با ۵ مسیر، دقت به saturation می‌رسد.
  افزایش بیشتر بازده ناچیزی دارد.
```

### ۶.۲ پیاده‌سازی در پایتون

```python
"""
Self-Consistency Reasoning — پیاده‌سازی در پایتون
شامل نمونه‌گیری چند مسیر و رای‌گیری
"""

from typing import List, Dict, Callable, Optional
from collections import Counter
import random
import re
import math


# ============================================================================
# ۱. هسته Self-Consistency
# ============================================================================

class SelfConsistency:
    """
    Self-Consistency: تولید چند مسیر استدلال + رای‌گیری.

    Args:
        llm: تابع فراخوانی LLM (یک پرامپت می‌گیرد و متن برمی‌گرداند)
        num_paths: تعداد مسیرهای استدلال (پیشنهاد: ۵)
        temperature: دمای نمونه‌گیری (بالاتر = تنوع بیشتر)
        extract_answer_fn: تابع استخراج پاسخ از متن
    """

    def __init__(
        self,
        llm: Callable,
        num_paths: int = 5,
        temperature: float = 0.7,
        extract_answer_fn: Optional[Callable] = None,
    ):
        self.llm = llm
        self.num_paths = num_paths
        self.temperature = temperature
        self.extract_answer = extract_answer_fn or self._default_extract
        self.paths: List[Dict] = []

    def solve(self, question: str, cot_trigger: str = "Let's think step by step.") -> Dict:
        """
        حل مسئله با Self-Consistency.

        Returns:
            دیکشنری شامل پاسخ نهایی، توزیع رأی، و همه مسیرها
        """
        self.paths = []
        prompt = f"Q: {question}\nA: {cot_trigger}\n"

        for i in range(self.num_paths):
            # هر مسیر با دمای بالا نمونه‌گیری می‌شود
            # تا تنوع در استدلال ایجاد شود
            reasoning = self.llm(prompt, temperature=self.temperature)
            answer = self.extract_answer(reasoning)

            self.paths.append({
                "path_id": i + 1,
                "reasoning": reasoning,
                "answer": answer,
            })

        # رای‌گیری
        vote_result = self._majority_vote()
        # رای‌گیری وزنی (اختیاری)
        weighted_result = self._weighted_vote()

        return {
            "question": question,
            "final_answer": vote_result["answer"],
            "confidence": vote_result["confidence"],
            "vote_distribution": vote_result["distribution"],
            "weighted_answer": weighted_result["answer"],
            "num_paths": self.num_paths,
            "paths": self.paths,
        }

    def _majority_vote(self) -> Dict:
        """رای اکثریت ساده."""
        answers = [p["answer"] for p in self.paths]
        counter = Counter(answers)

        if not counter:
            return {"answer": "N/A", "confidence": 0.0, "distribution": {}}

        most_common = counter.most_common(1)[0]
        total = sum(counter.values())
        distribution = {
            ans: {
                "count": count,
                "percentage": round(count / total * 100, 1),
            }
            for ans, count in counter.most_common()
        }

        return {
            "answer": most_common[0],
            "confidence": round(most_common[1] / total, 3),
            "distribution": distribution,
        }

    def _weighted_vote(self) -> Dict:
        """
        رای وزنی — هر مسیر بر اساس طول استدلال (norm) وزن می‌گیرد.
        مسیرهای طولانی‌تر معمولاً دقیق‌ترند.
        """
        answer_weights: Dict[str, float] = {}
        for p in self.paths:
            weight = math.log(len(p["reasoning"]) + 1)
            answer_weights[p["answer"]] = (
                answer_weights.get(p["answer"], 0) + weight
            )

        if not answer_weights:
            return {"answer": "N/A"}

        best = max(answer_weights, key=answer_weights.get)
        return {"answer": best, "weights": answer_weights}

    def _default_extract(self, text: str) -> str:
        """استخراج پیش‌فرض پاسخ از متن استدلال."""
        patterns = [
            r"[Tt]he answer is (\d+)",
            r"[Tt]he answer is (.+?)[.\n]",
            r"[Ff]inal answer:?\s*(.+?)[\n.]",
            r"answer:?\s*(.+?)[\n.]",
            r"Therefore,?\s*(.+?)[.\n]",
            r"جواب\s*(.+?)[\n.]",
            r"پاسخ\s*(.+?)[\n.]",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return text.strip().split(".")[-1].strip()


# ============================================================================
# ۲. رای‌گیری پیشرفته
# ============================================================================

class AdvancedConsistency(SelfConsistency):
    """
    نسخه پیشرفته Self-Consistency با روش‌های رای‌گیری بیشتر.
    """

    def solve_with_all_methods(self, question: str) -> Dict:
        """حل مسئله با چهار روش رای‌گیری مختلف."""
        base_result = self.solve(question)

        additional = {
            "marginal_vote": self._marginal_vote(),
            "confidence_weighted": self._confidence_weighted_vote(),
        }

        return {**base_result, **additional}

    def _marginal_vote(self) -> Dict:
        """
        رای حاشیه‌ای — احتمال هر پاسخ را از تمام مسیرها جمع می‌زند.
        نیاز به log probabilities از LLM دارد.
        """
        # شبیه‌سازی: log probability فرضی
        answer_probs: Dict[str, float] = {}
        for p in self.paths:
            fake_log_prob = random.uniform(-5, -0.1)
            prob = math.exp(fake_log_prob)
            answer_probs[p["answer"]] = (
                answer_probs.get(p["answer"], 0) + prob
            )

        # نرمال‌سازی
        total = sum(answer_probs.values())
        answer_probs = {k: v / total for k, v in answer_probs.items()}

        best = max(answer_probs, key=answer_probs.get)
        return {"answer": best, "marginal_probs": answer_probs}

    def _confidence_weighted_vote(self) -> Dict:
        """
        رای وزنی با اطمینان — هر مسیر بر اساس خودارزیابی LLM وزن می‌گیرد.
        """
        answer_scores: Dict[str, float] = {}
        for p in self.paths:
            # شبیه‌سازی امتیاز اطمینان (در عمل از LLM گرفته شود)
            confidence = random.uniform(0.5, 1.0)
            answer_scores[p["answer"]] = (
                answer_scores.get(p["answer"], 0) + confidence
            )

        best = max(answer_scores, key=answer_scores.get)
        return {"answer": best, "confidence_scores": answer_scores}


# ============================================================================
# ۳. مثال استفاده
# ============================================================================

def mock_llm_with_temp(prompt: str, temperature: float = 0.7) -> str:
    """شبیه‌ساز LLM با دمای قابل تنظیم (برای تنوع در مسیرها)."""
    # با دمای بالاتر، پاسخ‌های متنوع‌تری شبیه‌سازی می‌شود
    variants = [
        "Let's think step by step. 15 + 22 + 30 = 67. 20% of 67 = 13.4. 67 - 13.4 = 53.6. The answer is 53.6.",
        "Step by step: total = 15 + 22 + 30 = 67. Discount = 67 × 0.2 = 13.4. Final = 67 - 13.4 = 53.6. Answer: 53.6.",
        "Total items: 15 + 22 + 30 = 67 thousand. 20 percent discount means pay 80%. 67 × 0.8 = 53.6. Therefore 53.6.",
        "First: 15+22+30 = 67. Then apply 20% off: 67 × (1-0.2) = 67 × 0.8 = 53.6. The answer is 53.6.",
        "I need to compute: sum = 67. 20% of 67 is 13.4. So the price after discount is 53.6. Final answer: 53.6.",
        "Wrong approach: 15 + 22 + 30 = 67. 50% off is 33.5. Wait that's not 20%. 20% off: 67 × 0.8 = 53.6. Answer is 53.6.",
        "15+22=37. 37+30=67. 20% of 67 = 13.4. So total after discount is 53.6 thousand. Answer: 53.6.",
    ]
    # با دمای بالا، تنوع بیشتر
    if temperature > 0.5:
        return random.choice(variants)
    else:
        return variants[0]


if __name__ == "__main__":
    question = (
        "سه قلم کالا به قیمت‌های ۱۵، ۲۲ و ۳۰ هزار تومان خریداری می‌کنیم. "
        "۲۰٪ تخفیف بگیریم، مبلغ نهایی چقدر است؟"
    )

    print("=== Self-Consistency ===")
    sc = SelfConsistency(
        llm=mock_llm_with_temp,
        num_paths=7,
        temperature=0.8
    )

    result = sc.solve(question)
    print(f"\nسوال: {result['question']}")
    print(f"تعداد مسیرها: {result['num_paths']}")
    print(f"\nتوزیع رأی:")
    for ans, data in result['vote_distribution'].items():
        print(f"  {ans}: {data['count']} رأی ({data['percentage']}%)")

    print(f"\nپاسخ نهایی (اکثریت): {result['final_answer']}")
    print(f"اطمینان: {result['confidence']:.1%}")
    print(f"پاسخ وزنی: {result['weighted_answer']}")

    # نمایش مسیرها
    print(f"\nهمه مسیرها:")
    for path in result['paths']:
        ans_display = path['answer'][:30]
        reas_display = path['reasoning'][:60]
        print(f"  مسیر {path['path_id']}: {reas_display}... → [{ans_display}]")
```

---

## ۷. ReAct — اشاره

الگوی **ReAct (Reasoning + Acting)** در فایل مجزای `01-Fundamentals/03-reasoning-and-planning.md` به تفصیل پوشش داده شده است. در اینجا تنها به مقایسه‌ی آن با الگوهای دیگر می‌پردازیم:

| ویژگی | CoT | ToT | GoT | ReAct |
|-------|-----|-----|-----|-------|
| **تعامل با محیط** | ❌ | ❌ | ❌ | ✅ |
| **فراخوانی ابزار** | ❌ | ❌ | ❌ | ✅ |
| **جستجوی فضای راه‌حل** | ❌ | ✅ (درختی) | ✅ (گرافی) | ❌ |
| **تجمیع چند مسیر** | ❌ | ✅ (انتخاب بهترین) | ✅ (ترکیب) | ❌ |
| **حلقه بازخورد** | ❌ | ❌ | ❌ | ✅ |
| **مناسب برای** | استدلال محض | مسائل جستجو | مسائل ترکیبی | عامل‌های عملیاتی |

---

## ۸. ماتریس تصمیم‌گیری — Decision Matrix

### ۸.۱ انتخاب الگوی مناسب بر اساس نوع مسئله

| نوع مسئله | مثال | الگوی پیشنهادی | دلیل |
|-----------|------|---------------|------|
| **محاسبات ریاضی ساده** | ۲۵ + ۱۷ = ؟ | CoT (Zero-shot) | کافی و کم‌هزینه |
| **مسائل ریاضی چندمرحله‌ای** | تخفیف زنجیره‌ای و مالیات | CoT (Few-shot) | نیاز به گام‌های شفاف |
| **استدلال منطقی** | اگر A > B و B > C آن‌گاه ... | CoT + Self-Consistency | نیاز به تأیید چندباره |
| **مسائل جستجو و برنامه‌ریزی** | مرتب‌سازی اعداد با کمترین جابه‌جایی | ToT (BFS) | فضای جستجوی محدود |
| **بازی‌های استراتژی** | حرکت بعدی در شطرنج | ToT (DFS) | عمق جستجوی زیاد |
| **تحلیل چندوجهی** | تحلیل SWOT + PESTEL یک شرکت | GoT | نیاز به ترکیب دیدگاه‌ها |
| **ترکیب اطلاعات** | خلاصه‌سازی چند سند | GoT + Self-Consistency | تجمیع منابع مختلف |
| **عامل تعاملی** | رزرو هتل با جستجوی وب | ReAct | نیاز به عمل در محیط |
| **کد نویسی و دیباگ** | رفع باگ در یک برنامه | CoT + Self-Consistency | بررسی چند سناریو |
| **تصمیم‌گیری گروهی** | انتخاب بهترین استراتژی بازاریابی | ToT + GoT | جستجو + تجمیع |

### ۸.۲ ماتریس هزینه-فایده

```text
هزینه (تعداد توکن) ▲
                    │
        ┌──────── GoT ────────┐
        │     (دقیق، گران)     │
        │                      │
   زیاد │    ToT (BFS/DFS)    │
        │    (متعادل)          │
        │                      │
   متوسط│  Self-Consistency   │
        │  (چندمسیره)          │
        │                      │
    کم  │  CoT (Zero/Few-shot)│
        │  (سریع، ارزان)       │
        │                      │
        └──────────────────────▶ دقت
             کم        زیاد
```

### ۸.۳ الگوی ترکیبی (Hybrid Patterns)

گاهی بهتر است چند الگو را ترکیب کرد:

```text
الگوی ترکیبی پیشنهادی برای مسائل پیچیده:

┌──────────────┐
│  CoT + ToT   │  استدلال اولیه با CoT، سپس جستجوی درختی برای عمیق‌تر شدن
├──────────────┤
│  CoT + Self- │  استدلال با CoT، تأیید با Self-Consistency
│  Consistency │
├──────────────┤
│  ToT + GoT   │  جستجوی درختی برای مسیرهای اصلی، سپس تجمیع گرافی
├──────────────┤
│  ReAct + ToT │  تعامل با محیط + جستجوی درختی در هر گام
└──────────────┘
```

---

## ۹. ادغام با Flow Engine HiveOS

الگوهای استدلال چندمرحله‌ای می‌توانند به‌عنوان **گره‌های processing** در Flow Engine HiveOS استفاده شوند.

### ۹.۱ ساختار پیشنهادی

```yaml
# HiveOS Flow DSL — استفاده از reasoning patterns در flow

name: "Advanced Research & Reasoning Flow"
description: "پژوهش پیشرفته با استدلال چندمرحله‌ای"
version: "0.2.0"

# پارامترهای استدلال
reasoning_config:
  default_pattern: "cot"        # الگوی پیش‌فرض
  fallback_pattern: "self-consistency"  # الگوی جایگزین
  max_tokens_reasoning: 2000    # سقف توکن برای استدلال
  temperature: 0.7              # دمای نمونه‌گیری

agents:
  # ============================================================
  # Agent 1: تحلیل اولیه با Zero-shot CoT
  # ============================================================
  - id: analyzer
    name: "تحلیلگر اولیه (CoT)"
    skills:
      - zero-shot-cot
      - prompt-engineering
    reasoning:
      pattern: "cot"
      mode: "zero-shot"
      trigger_phrase: "Let's think step by step in Persian."
    input: "user_query.md"
    output: "initial_analysis.md"

  # ============================================================
  # Agent 2: جستجوی درختی با ToT (برای مسائل پیچیده)
  # ============================================================
  - id: tree_searcher
    name: "جستجوگر درختی (ToT)"
    depends_on:
      - analyzer
    skills:
      - tree-of-thought
      - bfs-search
      - dfs-search
    reasoning:
      pattern: "tot"
      search_strategy: "bfs"     # bfs | dfs | beam
      max_depth: 5
      branch_factor: 3
      beam_width: 3
      prune_threshold: 0.3
      evaluation_method: "llm_self_eval"  # ارزیابی توسط خود LLM
    input_from:
      agent: analyzer
      files: [initial_analysis.md]
    output: "tree_search_results.md"

  # ============================================================
  # Agent 3: تجمیع گرافی با GoT
  # ============================================================
  - id: graph_synthesizer
    name: "تجمیع‌کننده گرافی (GoT)"
    depends_on:
      - tree_searcher
    skills:
      - graph-of-thought
      - aggregation
    reasoning:
      pattern: "got"
      aggregation_method: "llm_synthesis"  # ترکیب با LLM
      parallel_paths: 3
      node_types:
        - thought
        - aggregation
        - output
    input_from:
      agent: tree_searcher
      files: [tree_search_results.md]
    output: "synthesized_analysis.md"

  # ============================================================
  # Agent 4: تأیید با Self-Consistency
  # ============================================================
  - id: verifier
    name: "تأییدکننده (Self-Consistency)"
    depends_on:
      - graph_synthesizer
    skills:
      - self-consistency
      - majority-vote
    reasoning:
      pattern: "self-consistency"
      num_paths: 5
      temperature: 0.8
      vote_method: "majority"    # majority | weighted | marginal
      confidence_threshold: 0.7  # آستانه اطمینان
    input_from:
      agent: graph_synthesizer
      files: [synthesized_analysis.md]
    output: "verified_answer.md"
    on_low_confidence:
      action: "escalate_to_human"  # اگر اطمینان کم بود، به انسان ارجاع بده
      message: "اعتماد به پاسخ پایین است (%confidence%). لطفاً بررسی کنید."

  # ============================================================
  # Agent 5: خروجی نهایی
  # ============================================================
  - id: formatter
    name: "نهایی‌ساز"
    depends_on:
      - verifier
    skills:
      - markdown
      - report-generation
    output: "final_report.md"
```

### ۹.۲ نمودار جریان داده در HiveOS Flow

```text
جریان استدلال چندمرحله‌ای در HiveOS:

                    ┌─────────────────┐
                    │     سوال کاربر   │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Agent 1: تحلیلگر (CoT)      │
              │  ┌────────────────────────┐  │
              │  │ Zero-shot CoT          │  │
              │  │ "Let's think step by   │  │
              │  │  step"                 │  │
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             │ initial_analysis.md
                             ▼
              ┌──────────────────────────────┐
              │  Agent 2: جستجوگر (ToT)      │
              │  ┌────────────────────────┐  │
              │  │ BFS جستجوی درختی        │  │
              │  │ انشعاب ← هرس ← انتخاب   │  │
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             │ tree_search_results.md
                             ▼
              ┌──────────────────────────────┐
              │  Agent 3: تجمیع‌کننده (GoT)  │
              │  ┌────────────────────────┐  │
              │  │ تجمیع گرافی چند مسیر    │  │
              │  │ LLM Synthesis          │  │
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             │ synthesized_analysis.md
                             ▼
              ┌──────────────────────────────┐
              │  Agent 4: تأییدکننده (SC)   │
              │  ┌────────────────────────┐  │
              │  │ ۵ مسیر موازی ← رای‌گیری │  │
              │  │ اطمینان > ۰.۷؟         │━━│━ اگر نه → escalate
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             │ verified_answer.md
                             ▼
              ┌──────────────────────────────┐
              │  Agent 5: نهایی‌ساز          │
              │  ┌────────────────────────┐  │
              │  │ قالب‌بندی و خروجی      │  │
              │  │ Markdown Report        │  │
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             ▼
                    ┌─────────────────┐
                    │   پاسخ نهایی    │
                    └─────────────────┘
```

### ۹.۳ پیاده‌سازی گره استدلال در HiveOS

```python
"""
HiveOS Reasoning Node — ادغام الگوهای استدلال چندمرحله‌ای
در معماری HiveOS.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ReasoningPattern(str, Enum):
    COT = "cot"
    TOT = "tot"
    GOT = "got"
    SELF_CONSISTENCY = "self-consistency"


class ReasoningNode:
    """
    گره استدلال برای HiveOS Flow Engine.
    می‌تواند هر یک از الگوهای استدلال را اجرا کند.
    """

    def __init__(
        self,
        node_id: str,
        pattern: ReasoningPattern,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.pattern = pattern
        self.config = config or {}
        self.input_data: Optional[str] = None
        self.output_data: Optional[str] = None

    def set_input(self, data: str):
        """دریافت ورودی از گره قبلی flow."""
        self.input_data = data

    def execute(self) -> str:
        """اجرای گره استدلال."""
        if not self.input_data:
            raise ValueError(f"Node {self.node_id}: no input data")

        if self.pattern == ReasoningPattern.COT:
            return self._execute_cot()
        elif self.pattern == ReasoningPattern.TOT:
            return self._execute_tot()
        elif self.pattern == ReasoningPattern.GOT:
            return self._execute_got()
        elif self.pattern == ReasoningPattern.SELF_CONSISTENCY:
            return self._execute_self_consistency()
        else:
            raise ValueError(f"Unknown pattern: {self.pattern}")

    def _execute_cot(self) -> str:
        mode = self.config.get("mode", "zero-shot")
        trigger = self.config.get(
            "trigger_phrase",
            "Let's think step by step."
        )
        # در عمل: LLM call با trigger phrase
        return f"[CoT-{mode}] تحلیل {self.input_data[:50]}... با {trigger}"

    def _execute_tot(self) -> str:
        strategy = self.config.get("search_strategy", "bfs")
        max_depth = self.config.get("max_depth", 5)
        branch = self.config.get("branch_factor", 3)
        return (
            f"[ToT-{strategy}] جستجوی درختی با عمق {max_depth} "
            f"و انشعاب {branch} روی {self.input_data[:50]}..."
        )

    def _execute_got(self) -> str:
        agg_method = self.config.get("aggregation_method", "llm_synthesis")
        paths = self.config.get("parallel_paths", 3)
        return (
            f"[GoT-{agg_method}] تجمیع {paths} مسیر موازی "
            f"از {self.input_data[:50]}..."
        )

    def _execute_self_consistency(self) -> str:
        n_paths = self.config.get("num_paths", 5)
        vote = self.config.get("vote_method", "majority")
        return (
            f"[SelfConsistency-{vote}] {n_paths} مسیر موازی "
            f"با رای‌گیری روی {self.input_data[:50]}..."
        )

    def get_output(self) -> Optional[str]:
        return self.output_data


class ReasoningPipeline:
    """
    خط لوله استدلال در HiveOS — زنجیره‌ای از ReasoningNodeها.
    """

    def __init__(self):
        self.nodes: list[ReasoningNode] = []

    def add_node(self, node: ReasoningNode):
        self.nodes.append(node)

    def run(self, input_data: str) -> str:
        """اجرای کامل خط لوله استدلال."""
        current_input = input_data

        for node in self.nodes:
            print(f"  [HiveOS] اجرای گره: {node.node_id} ({node.pattern.value})")
            node.set_input(current_input)
            current_input = node.execute()
            node.output_data = current_input

        return current_input


# ============================================================================
# مثال: ساخت و اجرای یک خط لوله استدلال در HiveOS
# ============================================================================

if __name__ == "__main__":
    pipeline = ReasoningPipeline()

    # گام ۱: تحلیل اولیه با CoT
    pipeline.add_node(ReasoningNode(
        node_id="analyzer-01",
        pattern=ReasoningPattern.COT,
        config={"mode": "zero-shot", "trigger_phrase": "بیایید گام‌به‌گام فکر کنیم."}
    ))

    # گام ۲: جستجوی درختی با ToT
    pipeline.add_node(ReasoningNode(
        node_id="tree-search-01",
        pattern=ReasoningPattern.TOT,
        config={
            "search_strategy": "bfs",
            "max_depth": 4,
            "branch_factor": 3,
            "beam_width": 2,
        }
    ))

    # گام ۳: تجمیع با GoT
    pipeline.add_node(ReasoningNode(
        node_id="graph-synth-01",
        pattern=ReasoningPattern.GOT,
        config={
            "aggregation_method": "llm_synthesis",
            "parallel_paths": 3,
        }
    ))

    # گام ۴: تأیید با Self-Consistency
    pipeline.add_node(ReasoningNode(
        node_id="verifier-01",
        pattern=ReasoningPattern.SELF_CONSISTENCY,
        config={
            "num_paths": 5,
            "vote_method": "majority",
        }
    ))

    # اجرا
    print("HiveOS Reasoning Pipeline Execution:")
    print("=" * 50)
    result = pipeline.run(
        "تحلیل بازار فروش در سه ماهه اول و ارائه استراتژی بهینه"
    )
    print("=" * 50)
    print(f"نتیجه نهایی: {result}")
```

---

## ۱۰. جمع‌بندی و منابع

### ۱۰.۱ خلاصه

| الگو | ایده | مزیت اصلی | محدودیت اصلی |
|------|------|-----------|-------------|
| **CoT** | گام‌های میانی تفکر | ساده، مؤثر، کم‌هزینه | خطی، بدون بازگشت |
| **Self-Consistency** | چند مسیر + رای‌گیری | پایدار، مقاوم به خطا | هزینه بیشتر (N× CoT) |
| **ToT** | جستجوی درختی | کاوش فضای راه‌حل | پیچیدگی انفجاری در عرض |
| **GoT** | گراف تفکر + تجمیع | ترکیب دیدگاه‌ها | پیچیده‌ترین پیاده‌سازی |
| **ReAct** | تفکر ↔ عمل | تعامل با محیط | وابسته به کیفیت ابزارها |

### ۱۰.۲ راهنمای انتخاب سریع

```text
اگر مسئله ...
────────────────────────────────────────────────────────
... ریاضی ساده است                → Zero-shot CoT
... نیاز به دقت بالا دارد          → CoT + Self-Consistency
... فضای جستجو دارد               → ToT (BFS برای عریض، DFS برای عمیق)
... نیاز به ترکیب چند دیدگاه دارد   → GoT
... نیاز به تعامل با دنیای خارج دارد → ReAct
... خیلی پیچیده است               → ترکیب: CoT → ToT → GoT → SC
────────────────────────────────────────────────────────
```

### ۱۰.۳ منابع

| منبع | لینک |
|------|------|
| Chain-of-Thought Prompting (Wei et al., 2022) | [arXiv:2201.11903](https://arxiv.org/abs/2201.11903) |
| Self-Consistency (Wang et al., 2022) | [arXiv:2203.11171](https://arxiv.org/abs/2203.11171) |
| Auto-CoT (Zhang et al., 2022) | [arXiv:2210.03493](https://arxiv.org/abs/2210.03493) |
| Tree of Thoughts (Yao et al., 2023) | [arXiv:2305.10601](https://arxiv.org/abs/2305.10601) |
| Graph of Thoughts (Besta et al., 2023) | [arXiv:2308.09687](https://arxiv.org/abs/2308.09687) |
| ReAct (Yao et al., 2023) | [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) |
| HiveOS Flow DSL | `docs/02-Architecture/02-flow-dsl.md` |

---

> **نویسنده:** HiveOS Research Team — مستند الگوهای استدلال چندمرحله‌ای برای استفاده در معماری عامل‌های هوش مصنوعی
>
> **تاریخ:** July 2026
>
> **فایل‌های مرتبط:**
> - `01-Fundamentals/03-reasoning-and-planning.md` — ReAct, Plan-and-Execute, Function Calling
> - `04-Advanced-Patterns/01-memory-and-context.md` — حافظه و زمینه در عامل‌ها
> - `02-Architecture/02-flow-dsl.md` — مستندات Flow DSL HiveOS

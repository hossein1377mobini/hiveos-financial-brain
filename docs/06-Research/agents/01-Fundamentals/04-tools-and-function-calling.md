# ابزارها و فراخوانی تابع — Tools & Function Calling (مرور سریع)

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **نکته:** این فایل یک **مرور سریع** است. محتوای عمیق و مثال‌های کد در `01-Fundamentals/03-reasoning-and-planning.md` موجود است.

---

## ۱. مقدمه

**ابزارها (Tools)** پل ارتباطی بین LLM و جهان خارج هستند. بدون ابزار، یک LLM فقط می‌تواند متن تولید کند — با ابزار، می‌تواند **API فراخوانی کند، فایل بخواند، کد اجرا کند، جستجوی وب انجام دهد** و در دنیای واقعی اثر بگذارد.

این فایل یک نمای کلی از مفاهیم Tool Use و Function Calling ارائه می‌دهد. برای جزئیات فنی، پیاده‌سازی کد، و مثال‌های عملی به فایل اصلی مراجعه کنید:

📎 **فایل اصلی:** [`01-Fundamentals/03-reasoning-and-planning.md`](../01-Fundamentals/03-reasoning-and-planning.md)

---

## ۲. مفاهیم کلیدی

| مفهوم | توضیح مختصر | مستندات کامل |
|-------|------------|-------------|
| **Function Calling** | LLM خروجی JSON ساختاریافته برای فراخوانی تابع تولید می‌کند | بخش ۳ در `03-reasoning-and-planning.md` |
| **Tool Use** | هر قابلیت قابل فراخوانی که عامل می‌تواند استفاده کند (Search, API, Code, etc.) | بخش ۴ |
| **MCP (Model Context Protocol)** | پروتکل استاندارد ارتباط عامل با ابزارها | بخش ۴.۳ |
| **Tool Registration** | ثبت ابزار با اسکیما (نام، توضیحات، پارامترها) | بخش ۴.۲ |

---

## ۳. ارتباط با HiveOS

HiveOS از MCP برای ارتباط عامل‌ها با ابزارها استفاده می‌کند. هر Domain در HiveOS مجموعه‌ای از ابزارهای تخصصی خود را دارد:

```python
# HiveOS — هر Domain ابزارهای خود را ثبت می‌کند
from hiveos.domain import Domain

accounting_domain = Domain(
    name="accounting",
    tools=[
        FinancialStatementTool(),
        TaxCalculatorTool(),
        RatioAnalysisTool(),
        ReportGeneratorTool()
    ]
)
```

---

**👉 برای مطالعهٔ عمیق:** به `01-Fundamentals/03-reasoning-and-planning.md` مراجعه کنید که شامل مثال‌های کامل کد، دیاگرام، و مقایسه Function Calling vs ReAct vs Plan-and-Execute است.

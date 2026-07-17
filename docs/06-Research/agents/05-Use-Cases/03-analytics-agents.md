# عامل‌های تحلیلی — Analytics Agents (کاربردها و سناریوها)

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶

---

## ۱. مقدمه

**عامل‌های تحلیلی (Analytics Agents)** داده‌ها را تحلیل می‌کنند، الگوها را کشف می‌کنند و insight تولید می‌نمایند. این عامل‌ها ترکیبی از **تحلیل آماری سنتی** و **هوش مصنوعی** هستند.

### انواع Analytics Agents:

| نوع | وظیفه | مثال |
|-----|-------|------|
| **Data Analyst** | تحلیل داده‌های ساختاریافته | گزارش فروش ماهانه |
| **Financial Analyst** | تحلیل صورت‌های مالی | نسبت‌های نقدینگی و سودآوری |
| **Business Analyst** | تحلیل فرایندهای کسب‌وکار | شناسایی bottleneck |
| **Trend Analyst** | شناسایی روندها | پیش‌بینی فروش |
| **Risk Analyst** | تحلیل ریسک | امتیاز اعتباری مشتری |

---

## ۲. معماری Analytics Agent

```text
داده خام → [پاکسازی] → [تحلیل] → [تجسم] → [گزارش]
                │            │
                ▼            ▼
           ┌────────┐  ┌──────────┐
           │ پروفایل │  | Machine │
           │ داده   │  | Learning │
           └────────┘  └──────────┘
```

### ابزارهای رایج:

| ابزار | کاربرد |
|-------|--------|
| **Python/Pandas** | پردازش و تحلیل داده |
| **SQL** | پرس‌وجوی پایگاه داده |
| **Matplotlib/Plotly** | نمودار و تجسم |
| **scikit-learn** | مدل‌های پیش‌بینی |
| **Excel/CSV** | داده‌های ورودی/خروجی |

---

## ۳. سناریو: تحلیل فروش ماهانه

```python
# HiveOS Analytics Agent — تحلیل فروش
class SalesAnalyticsAgent:
    async def analyze(self, company_id: str, period: str) -> dict:
        # ۱. جمع‌آوری داده
        sales_data = await self.get_sales_data(company_id, period)
        
        # ۲. تحلیل
        total_revenue = sum(s["amount"] for s in sales_data)
        top_products = self.get_top_products(sales_data, n=5)
        growth_rate = self.calculate_growth(sales_data)
        
        # ۳. نتیجه
        return {
            "total_revenue": total_revenue,
            "top_products": top_products,
            "growth_rate": growth_rate,
            "recommendations": self.generate_recommendations(sales_data)
        }
```

---

## ۴. Analytics Agents در HiveOS

دامنهٔ حسابداری HiveOS شامل چندین Analytics Agent:

| Agent | تحلیل‌ها |
|-------|---------|
| **Financial Analyst** | نسبت‌های مالی، تحلیل صورت‌ها |
| **Tax Analyst** | محاسبه و تحلیل مالیات |
| **Cost Analyst** | تحلیل بهای تمام شده |
| **Budget Analyst** | تحلیل بودجه و انحرافات |

---

**فایل‌های مرتبط:**
- `docs/06-Research/accounting/_index.md`
- `src/hiveos/playground/playground.py`

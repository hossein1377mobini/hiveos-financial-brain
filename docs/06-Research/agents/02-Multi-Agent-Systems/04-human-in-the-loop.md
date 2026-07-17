# انسان در حلقه — Human-in-the-Loop (HITL) در سیستم‌های چندعاملی

> **نویسنده:** تیم مستندات HiveOS
> **تاریخ:** جولای ۲۰۲۶
> **منابع:** HiveOS Approval Gate Engine · LangGraph Human-in-the-Loop · Anthropic HITL Guidelines · Microsoft AutoGen HITL

---

## ۱. مقدمه: چرا انسان در حلقه؟

یکی از حیاتی‌ترین ویژگی‌های سیستم‌های عامل هوش مصنوعی (AI Agent Systems) **حضور انسان در حلقه (Human-in-the-Loop / HITL)** است. این یعنی در نقاط حساس فرایند، انسان می‌تواند تصمیم‌ها را **بررسی، تأیید، رد، یا اصلاح** کند.

### چرا HITL ضروری است؟

| دلیل | توضیح | مثال |
|------|-------|------|
| **تصمیم‌های پرخطر (High-Stakes)** | برخی تصمیم‌ها عواقب مالی یا قانونی دارند | تأیید تراکنش بانکی بالای ۱۰۰ میلیون تومان |
| **ابهام (Ambiguity)** | گاهی ورودی آنقدر نامشخص است که عامل نمی‌تواند تصمیم بگیرد | تشخیص نوع قرارداد از اسناد ناقص |
| **اخلاق و انصاف (Ethics & Fairness)** | اطمینان از عدم تبعیض یا تصمیم غیراخلاقی | بررسی رد درخواست وام مشتری |
| **یادگیری و اصلاح (Learning & Correction)** | انسان می‌تواند رفتار عامل را اصلاح کند | تصحیح یک اشتباه در تحلیل مالی |
| **اعتماد (Trust)** | کاربر باید به سیستم اعتماد کند | مشاهده و تأیید تدریجی خروجی‌ها |

> **تشبیه:** HITL مثل **سیستم ترمز دستی در ماشین‌های خودران** است — ماشین ۹۹٪ مواقع خودش رانندگی می‌کند، اما در شرایط بحرانی، انسان می‌تواند کنترل را به‌دست بگیرد.

---

## ۲. سطوح HITL — Human-in-the-Loop Levels

### ۲.۱ Human-in-the-Loop (فعال)

انسان **بخشی از فرایند تصمیم‌گیری است** و سیستم بدون تأیید او نمی‌تواند ادامه دهد.

```text
Agent: "پیشنهاد: پرداخت فاکتور ۵۰۰ میلیون تومان به شرکت X"
             │
             ▼
    ┌────────────────┐
    │  توقف (Interrupt) │
    │  منتظر تأیید انسان │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐      ┌──────────┐
    │    انسان        │─────▶│ تأیید    │
    │  (بررسی می‌کند)  │      │ رد       │
    └────────────────┘      │ اصلاح    │
                           └──────────┘
```

**زمان استفاده:** تراکنش‌های مالی، تصمیمات حقوقی، انتشار محتوا

### ۲.۲ Human-on-the-Loop (ناظر)

سیستم خودکار تصمیم می‌گیرد اما انسان می‌تواند **نظارت کند و در صورت لزوم مداخله نماید**.

```text
Agent: "پیشنهاد: ارسال ایمیل به ۱۰۰۰ مشتری"
             │
             ▼
    ┌────────────────┐
    │  اجرای خودکار   │ ← اگر انسان ظرف N ثانیه مداخله نکند
    │  با تأخیر      │
    └────────────────┘
             │
      ┌──────┴──────┐
      ▼              ▼
  ┌────────┐   ┌──────────┐
  │انسان وارد│   │اتمام خودکار│
  │می‌شود   │   │(پیش‌فرض)  │
  └────────┘   └──────────┘
```

**زمان استفاده:** ارسال‌های دسته‌جمعی، بروزرسانی‌های روتین

### ۲.۳ Human-in-the-Command (فرمانده)

سیستم فقط **پیشنهاد می‌دهد** و انسان تصمیم نهایی را می‌گیرد و اجرا می‌کند.

```text
Agent: "بر اساس تحلیل، توصیه می‌کنم سبد سهام را به صورت X تغییر دهیم."
             │
             ▼
    ┌────────────────┐
    │  پیشنهاد به    │
    │  انسان         │
    └────────────────┘
             │
             ▼
    ┌────────────────┐
    │    انسان       │───▶ تصمیم + اجرای دستی
    │  (تصمیم نهایی) │
    └────────────────┘
```

**زمان استفاده:** معاملات بورس، تغییرات استراتژیک

---

## ۳. الگوهای پیاده‌سازی HITL

### ۳.۱ Interrupt Pattern (قطع / توقف)

رایج‌ترین الگو. عامل در یک نقطهٔ مشخص از اجرا **می‌ایستد** و منتظر ورود انسان می‌ماند.

**پیاده‌سازی در LangGraph:**
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

class ApprovalState(TypedDict):
    request: str
    amount: float
    approved: Optional[bool] = None
    reason: str = ""

def check_approval_needed(state: ApprovalState):
    """اگر مبلغ بیش از ۱۰۰ میلیون باشد، نیاز به تأیید انسانی دارد"""
    if state["amount"] > 100_000_000:
        return "human_approval"
    return "auto_process"

def auto_process(state: ApprovalState):
    state["approved"] = True
    state["reason"] = "مبلغ زیر سقف خودکار"
    return state

# گراف با HITL
graph = StateGraph(ApprovalState)
graph.add_node("check", check_approval_needed)
graph.add_node("process", auto_process)
graph.add_node("human_approval", HumanApprovalNode)  # interrupt_before

graph.add_conditional_edges(
    "check",
    lambda s: "approve" if s["amount"] > 100_000_000 else "process"
)

# Compile با قابلیت中断
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_approval"]  # اینجا متوقف می‌شود
)

# اجرا تا نقطهٔ توقف
config = {"configurable": {"thread_id": "pay-123"}}
result = app.invoke({"request": "فاکتور 500 میلیونی", "amount": 500_000_000}, config)

# انسان بررسی می‌کند و تصمیم می‌گیرد
human_decision = {
    "approved": True,
    "reason": "تأیید شد — قرارداد مستند دارد"
}
app.update_state(config, human_decision)

# ادامهٔ اجرا از نقطهٔ توقف
result = app.invoke(None, config)
```

### ۳.۲ Escalation Pattern (بالا بردن سطح)

عامل ابتدا خودش تصمیم می‌گیرد، اگر نتوانست به **انسان ارجاع می‌دهد**:

```python
def try_resolve_automatically(query: str) -> tuple[bool, str]:
    """تلاش برای حل خودکار مشکل"""
    # جستجو در دانش‌نامه
    # اگر پاسخ قطعی بود → (True, answer)
    # اگر نامشخص بود → (False, "")
    pass

def escalate_to_human(
    query: str,
    agent_reasoning: str,
    suggested_actions: list[str]
) -> None:
    """ارجاع به انسان با زمینهٔ کامل"""
    ticket = {
        "priority": "high",
        "query": query,
        "context": agent_reasoning,
        "suggestions": suggested_actions
    }
    slack_notify("#escalations", ticket)
    return wait_for_human_response(ticket)
```

### ۳.۳ Approval Gate Pattern (دروازه تأیید)

مناسب برای workflowهایی که چندین نقطهٔ تأیید دارند:

```python
class ApprovalGate:
    """دروازهٔ تأیید — HiveOS از این الگو استفاده می‌کند"""
    
    def __init__(self, gate_id: str, required_approvers: int = 1):
        self.gate_id = gate_id
        self.status = "pending"  # pending | approved | rejected | expired
        self.required_approvers = required_approvers
        self.approvals: list[dict] = []
        self.created_at = datetime.now()
    
    async def request_approval(
        self,
        task_description: str,
        context: dict
    ) -> None:
        """ارسال درخواست تأیید به انسان"""
        notification = {
            "type": "approval_required",
            "gate_id": self.gate_id,
            "task": task_description,
            "context": context,
            "respond_by": self.created_at + timedelta(hours=24)
        }
        await notify_human(notification)
    
    async def approve(self, approver: str, reason: str = "") -> bool:
        """تأیید درخواست"""
        self.approvals.append({
            "approver": approver,
            "action": "approved",
            "reason": reason,
            "timestamp": datetime.now()
        })
        if len(self.approvals) >= self.required_approvers:
            self.status = "approved"
            return True
        return False
    
    async def reject(self, approver: str, reason: str) -> None:
        """رد درخواست"""
        self.status = "rejected"
        self.approvals.append({
            "approver": approver,
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.now()
        })
```

### ۳.۴ Review-Test Pattern (بررسی و آزمون)

ایده‌آل برای workflowهای تولید محتوا:

```text
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Agent    │───▶│ Reviewer │───▶│ Agent    │
│ (نویسنده)│    │ (انسان)  │    │ (اصلاح)  │
└──────────┘    └────┬─────┘    └──────────┘
                     │
                     │ رد
                     ▼
              ┌──────────┐
              │ بازنویسی  │
              └──────────┘
```

---

## ۴. HITL در HiveOS — دروازه‌های تأیید (Approval Gates)

HiveOS یک **موتور دروازه تأیید (Approval Gate Engine)** کامل دارد که در `src/hiveos/brain/approval_gate.py` پیاده‌سازی شده.

### معماری Approval Gate در HiveOS:

```python
# HiveOS Approval Gate Engine — کد واقعی
from hiveos.brain.approval_gate import ApprovalGateEngine

# ساخت دروازه
gate_engine = ApprovalGateEngine(storage_engine=storage)

# ایجاد دروازه جدید
gate = await gate_engine.create_gate(
    gate_type="payment_approval",
    title="تأیید پرداخت فاکتور",
    context={
        "vendor": "شرکت X",
        "amount": 500_000_000,
        "invoice_url": "https://.../invoice-123.pdf"
    },
    required_approvers=2,  # دو نفر باید تأیید کنند
    ttl_hours=48  # مهلت ۴۸ ساعته
)

# ارسال به انسان
await gate_engine.notify_approvers(gate.id)

# دریافت نتیجه
status = await gate_engine.get_gate_status(gate.id)
# status: "pending" | "approved" | "rejected" | "expired"

if status == "approved":
    await payment_workflow.continue_execution(gate.context)
elif status == "rejected":
    await payment_workflow.handle_rejection(gate)
```

### API دروازه‌های تأیید HiveOS:

| متد | توضیح |
|------|-------|
| `create_gate(type, title, context, ...)` | ایجاد دروازه با تمام جزئیات |
| `approve_gate(gate_id, user_id, reason)` | تأیید دروازه توسط یک کاربر |
| `reject_gate(gate_id, user_id, reason)` | رد دروازه |
| `get_gate_status(gate_id)` | دریافت وضعیت جاری |
| `list_pending_gates(user_id)` | لیست دروازه‌های منتظر تأیید یک کاربر |
| `get_gate_stats()` | آمار کلی (تأیید/رد/منقضی) |

---

## ۵. الگوهای اعلان (Notification Patterns)

ارسال به موقع درخواست تأیید به انسان حیاتی است:

| کانال | زمان مناسب | مثال |
|-------|-----------|------|
| **Push Notification** | درخواست فوری | تأیید پرداخت اضطراری |
| **Email** | غیر فوری | گزارش هفتگی نیازمند تأیید |
| **Slack/Telegram** | روزانه | درخواست‌های تأیید معمول |
| **Dashboard** | همه | مرکز کنترل متمرکز |

```python
# استراتژی اعلان چندکاناله در HiveOS
async def notify_human(gate: ApprovalGate) -> None:
    """ارسال اعلان به انسان از طریق کانال مناسب"""
    
    if gate.priority == "critical":
        # Push notification فوری
        await push_notify(
            user_id=gate.assigned_to,
            title=f"⚠️ تأیید فوری: {gate.title}",
            body=f"مبلغ: {gate.amount:,} تومان"
        )
    elif gate.priority == "normal":
        # پیام در دشبورد + اعلان نرم
        await dashboard.add_notification(gate)
        await slack_notify(
            channel="#approvals",
            text=f"📋 درخواست تأیید جدید: {gate.title}"
        )
```

---

## ۶. ملاحظات طراحی HITL

### ۶.۱ زمان‌بندی و انقضا (TTL)

```python
GATE_CONFIGS = {
    "payment_approval": {
        "ttl": timedelta(hours=24),
        "escalation": {
            "first_reminder": timedelta(hours=4),
            "second_reminder": timedelta(hours=12),
            "escalate_to_manager": timedelta(hours=20)
        },
        "auto_decision": "reject"  # پس از انقضا
    },
    "content_review": {
        "ttl": timedelta(days=3),
        "auto_decision": "approve"  # پیش‌فرض خوش‌بینانه
    }
}
```

### ۶.۲ زمینهٔ کافی به انسان (Context Richness)

هر درخواست تأیید باید **زمینهٔ کافی** برای تصمیم‌گیری در اختیار انسان بگذارد:

```python
approval_request = {
    "title": "تأیید پیشنهاد سرمایه‌گذاری",
    "summary": "سرمایه‌گذاری ۲ میلیارد تومانی در صندوق X با بازده پیش‌بینی ۲۵٪",
    "key_points": [
        "میانگین بازده ۳ ساله صندوق: ۲۲٪",
        "ریسک: متوسط",
        "مدت: ۶ ماه"
    ],
    "agent_reasoning": "... تحلیل کامل عامل ...",
    "alternatives": [
        {"option": "سپرده بانکی ۱۸٪", "risk": "کم"},
        {"option": "صندوق Y با ۲۰٪", "risk": "کم-متوسط"}
    ],
    "attachments": [
        "گزارش کامل تحلیل.pdf",
        "صورت‌های مالی صندوق.pdf"
    ]
}
```

### ۶.۳ استراتژی‌های Fallback

| سناریو | راهکار |
|--------|--------|
| **انسان پاسخ نداد** | اتوماتیک reject بعد از TTL |
| **انسان در دسترس نیست** | ارسال به جانشین (deputy) |
| **انسان تصمیم اشتباه گرفت** | لاگ + قابلیت بازگشت (undo) |
| **نیاز به تأیید چندنفره** | M-of-N approval (مثلاً ۲ از ۳) |

---

## ۷. HITL در فریمورک‌های محبوب

| فریمورک | مکانیزم HITL | نحوهٔ کار |
|---------|-------------|-----------|
| **LangGraph** | `interrupt_before` / `interrupt_after` | توقف در گره مشخص، منتظر ورود انسان، ادامه از همان نقطه |
| **CrewAI** | Callback سفارشی | توقف در انتهای هر وظیفه، منتظر تأیید انسان |
| **AutoGen** | `human_input_mode="ALWAYS"` | سطوح مختلف: NEVER, TERMINATE, ALWAYS |
| **OpenAI SDK** | Input/Output Guardrails | اعتبارسنجی قبل و بعد از اجرا |
| **HiveOS** | Approval Gate Engine | دروازه‌های قابل تعریف با M-of-N، TTL، اعلان چندکاناله |

---

## ۸. الگوهای پیشرفته HITL

### ۸.۱ تأیید تدریجی (Staged Approval)

وظایف بزرگ را به مراحل کوچک تقسیم کرده و هر مرحله جداگانه تأیید می‌شود:

```text
مرحله ۱: جمع‌آوری داده ──→ تأیید انسان ──→
مرحله ۲: تحلیل داده  ──→ تأیید انسان ──→
مرحله ۳: پیشنهاد نهایی ──→ تأیید انسان ──→ انتشار
```

### ۸.۲ Sampling-Based Review

در وظایف با خروجی زیاد (مثلاً ارسال ۱۰۰۰ ایمیل)، فقط **نمونه‌ای** از خروجی‌ها بررسی می‌شود:

```python
def sample_review(outputs: list[dict], sample_size: int = 10) -> None:
    """بررسی تصادفی نمونه‌ای از خروجی‌ها"""
    sample = random.sample(outputs, min(sample_size, len(outputs)))
    for item in sample:
        send_for_review(item)
    
    # اگر همهٔ نمونه‌ها تأیید شدند، کل خروجی تأیید می‌شود
    if all(item["reviewed"] == "approved" for item in sample):
        mark_all_approved(outputs)
```

### ۸.۳ Progressive Automation

با افزایش اعتماد سیستم، نیاز به HITL کاهش می‌یابد:

| فاز | سطح HITL | تصمیم‌گیری |
|-----|----------|------------|
| **فاز ۱: راه‌اندازی** | Human-in-the-Command | همهٔ تصمیمات با انسان |
| **فاز ۲: آزمایش** | Human-on-the-Loop | سیستم پیشنهاد می‌دهد، انسان تأیید می‌کند |
| **فاز ۳: اعتماد** | Human-in-the-Loop (critical) | فقط تصمیمات بحرانی نیاز به تأیید دارند |
| **فاز ۴: اتوماتیک** | Human-over-the-Loop | انسان dashboard را زیر نظر دارد |

---

## ۹. چالش‌ها و راهکارها

| چالش | تأثیر | راهکار |
|------|-------|--------|
| **تأخیر انسانی (Human Latency)** | کند شدن workflow | TTL + escalation + auto-decision |
| **خستگی انسانی (Alert Fatigue)** | بی‌توجهی به درخواست‌ها | هوشمند: فقط موارد واقعاً مهم را ارسال کن |
| **ابهام در زمینه (Context Ambiguity)** | تصمیم اشتباه | همیشه دلیل کامل + مستندات را همراه کن |
| **امنیت (Security)** | تصمیم‌گیری توسط فرد غیرمجاز | احراز هویت قوی + لاگ کامل |
| **قابلیت ردیابی (Auditability)** | عدم شفافیت | تمام تصمیمات + دلایل ذخیره شوند |

---

## ۱۰. جمع‌بندی

| # | نکته |
|---|------|
| ۱ | **HITL** تعادل بین **سرعت اتوماسیون** و **قضاوت انسانی** است |
| ۲ | **سه سطح:** Human-in-the-Loop (فعال)، Human-on-the-Loop (ناظر)، Human-in-the-Command (فرمانده) |
| ۳ | **چهار الگو:** Interrupt (قطع)، Escalation (ارجاع)، Approval Gate (دروازه)، Review-Test (بررسی) |
| ۴ | **زمینهٔ غنی** برای تصمیم‌گیری انسان حیاتی است — هیچ‌وقت بدون context درخواست تأیید نفرست |
| ۵ | **TTL و Escalation** را فراموش نکن — انسان ممکن است پاسخ ندهد |
| ۶ | **Progressive Automation** = با افزایش اعتماد، HITL را کاهش بده |
| ۷ | **HiveOS Approval Gate Engine** یک پیاده‌سازی کامل از الگوی دروازه تأیید است |
| ۸ | **همیشه لاگ کن** — چه کسی، کی، چرا تصمیم گرفت |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل‌های مرتبط:**
> - `src/hiveos/brain/approval_gate.py` — پیاده‌سازی اصلی
> - `docs/06-Research/agents/02-Multi-Agent-Systems/01-orchestration-patterns.md`

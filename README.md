# الشبح AlShabah

الشبح طبقة تخطيط فعل ويب لوكلاء الذكاء: تولد خطوات متصفح/CDP بصيغة dry-run ولا تنفذ فعلياً. الهدف أن تكون طبقة أمان قبل أي Playwright/CDP حقيقي.

## آلية العمل

1. `init-policy` ينشئ سياسة نطاقات مسموحة.
2. `plan` يحول مهمة إلى خطوات `goto/click/fill/submit/extract` مع `dry_run`.
3. `convert-bitext` يحول رسائل Bitext إلى مهام ويب.
4. `batch/stress` يقيسان التخطيط على آلاف المهام.

## تشغيل سريع

```powershell
python -m alshabah.cli init-policy
python -m alshabah.cli plan --task "contact support" --url https://carbonflows.store
python -m alshabah.cli convert-bitext
python -m alshabah.cli batch
```

## بيانات الاختبار

تعتمد على 12,000 رسالة Bitext التي جلبها `C:\Projects\almandoub` من الإنترنت.

## آخر نتائج

- الاختبارات الذاتية: 3/3 ناجحة.
- سياسة افتراضية: `carbonflows.store` و`example.com` فقط، dry-run مفعّل.
- Benchmark: 12,000 مهمة، allowed=12,000، blocked=0، errors=0، steps=25,712، p99=0.053ms.
- Stress: 36,000 مهمة، errors=0، steps=77,136، p99=0.048ms، peak memory=1.18MB.

## تحسينات إنتاجية 2026-07-04

- كل الخطة dry-run ولا تستدعي متصفحاً أو CDP فعلياً.
- سياسة النطاقات تمنع أي URL خارج allowlist قبل توليد الخطوات.
- المخرجات خطوات JSON قابلة لاحقاً للتمرير إلى Playwright بعد موافقة AEGIS.

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة تخطيط HTTP**: `python -m alshabah.cli serve` → `POST /api/plan {"task","url"}` يعيد خطوات dry-run بعد فحص allowlist النطاقات.
- **قرار أمني**: الخدمة لا تشغل متصفحاً أبداً — تخطط فقط؛ التنفيذ الحقيقي يمر عبر AEGIS لاحقاً.
- **السياسة تحمل مرة واحدة** عند الإقلاع (`ALSHABAH_POLICY`، افتراضي `config\policy.json`).
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics`.
- **تهيئة عبر البيئة**: متغيرات `ALSHABAH_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALSHABAH_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\alshabah.service.jsonl`.

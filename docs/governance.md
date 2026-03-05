# Governance & Compliance Notes (Demo)

هذا القسم موجود لإظهار الوعي المطلوب في الوصف الوظيفي: **حوكمة + أمن + امتثال داخل السعودية**.

## 1) Data Classification (مثال)
- **Public**: بيانات مجمّعة لا تعرّف أفراد.
- **Internal**: تفاصيل تشغيلية داخلية.
- **Confidential**: بيانات فردية/مركبات/مخالفات تتضمن معرّفات.
- **Restricted**: أي بيانات حساسة تخضع لضوابط أعلى (PII/موقع دقيق/سجلات رسمية).

## 2) Access Controls
- Role-based access (Viewer / Analyst / Admin).
- Least privilege + auditing.
- فصل بيئة التطوير عن الإنتاج.

## 3) Traceability / Lineage
- لكل سجل: `source_system`, `ingest_batch_id`, `record_hash`, `extracted_at_utc`.
- توثيق التعاريف + قاموس بيانات + خرائط التحويلات.

## 4) Analytics Guardrails
- فحوصات جودة (DQ Gates) قبل نشر أي لوحة أو نموذج.
- توثيق الافتراضات والقيود.
- فحوصات تحيز/انحراف للنموذج (Group metrics على الأقل) + مراجعة بشرية.

> في الإنتاج يتم ربط هذا مع سياسات الجهة الوطنية واللوائح ذات الصلة داخل المملكة.

## 5) Interview Positioning
- هذا المشروع **ديمو حوكمة وتحليلات** وليس أداة امتثال قانوني نهائية.
- الغرض هو إظهار البنية الصحيحة: traceability + quality gates + documented assumptions + controlled BI delivery.
- راجع أيضًا: `docs/saudi_compliance_reference.md`

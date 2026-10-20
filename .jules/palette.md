## 2023-10-20 - Standardizing Form A11y
**Learning:** React state-driven loading and error messages are invisible to screen readers unless explicitly marked. While visual cues (spinners, red text) exist, `aria-busy` and `role="alert"` are critical missing components in standard form implementations.
**Action:** Always verify that interactive buttons include `aria-busy` when disabled due to loading, and ensure dynamic error containers use `role="alert"` (or `aria-live`) for immediate screen reader announcement.

## 2024-10-08 - Accessible Error Messages
**Learning:** Dynamically rendered error message components (like API failure alerts) in React/Next.js are often missed by screen readers because they appear after the initial page load. Adding `role="alert"` directly to the container is required so assistive technologies announce them immediately.
**Action:** When creating form validation or API failure states, always add `role="alert"` (or `aria-live="assertive"`) to the container div where the error text will be displayed.

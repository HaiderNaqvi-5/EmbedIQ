## 2024-10-10 - Add role="alert" to error message containers
**Learning:** React state-driven error messages (like form validation errors or API failure states) are not announced by screen readers when they appear on the page unless they have an ARIA live region attribute.
**Action:** Always add `role="alert"` (or `aria-live="assertive"`) to the container div that renders `error` text states.

## 2024-05-19 - Standardize Form Error Accessibility
**Learning:** Next.js form error states in this app lack default ARIA roles, causing screen readers to miss dynamic error announcements on login, registration, and bot creation.
**Action:** When creating form validation or API failure states in React/Next.js components, always add `role="alert"` (or `aria-live="assertive"`) to the container div displaying the error text. Additionally, use `aria-busy={loading}` on form submit buttons to ensure assistive technologies correctly announce loading states.

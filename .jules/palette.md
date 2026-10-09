## 2023-10-26 - Missing ARIA roles on dynamic error states
**Learning:** Found a pattern where dynamically rendered form validation and API failure banners (like in login, register, and chat widgets) omitted `role="alert"`. This prevents screen readers from immediately announcing critical authentication or communication failures to users.
**Action:** Always verify that error message containers, especially those conditionally rendered via state (e.g. `{error && <div...>}`), include `role="alert"` or `aria-live="assertive"` so assistive technologies announce them upon appearance.

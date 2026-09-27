## 2024-05-17 - Button focus and aria labels
**Learning:** Adding redundant `aria-label`s to buttons whose internal text already completely describes the action is an accessibility anti-pattern. E.g., `aria-label="Sign in"` on a button containing `<span>Sign in</span>`.
**Action:** Before blindly adding `aria-label` to buttons, inspect the inner content. Only add `aria-label` if the action is unclear from text alone or it relies solely on icons.

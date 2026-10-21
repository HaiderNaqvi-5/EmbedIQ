## 2026-10-21 - Enhanced Dashboard Sidebar Navigation Accessibility
**Learning:** When building global navigation elements like sidebars, it is crucial to combine `aria-current="page"` on the active item for screen readers and `focus-visible` utility classes for clear keyboard navigation states. Both visually and semantically, this clarifies the current context and navigation hierarchy.
**Action:** Always add `aria-current={isActive ? 'page' : undefined}` to active navigation links and use `focus-visible` to apply keyboard-specific focus rings to all interactive navigation elements.

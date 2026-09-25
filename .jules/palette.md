## 2026-09-25 - Focus States and ARIA Current
**Learning:** The dashboard sidebar lacked proper keyboard focus indicators and an ARIA 'current' indicator for screen readers.
**Action:** Ensure all interactive elements (like custom '<button>' and '<Link>') use tailwind 'focus-visible:ring-2' and set 'aria-current="page"' on active navigation items.

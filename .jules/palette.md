## 2024-10-07 - Ensure consistent focus rings on interactive elements
**Learning:** Interactive elements mapped via arrays in Next.js (like navigation links in `layout.tsx`) often lack native focus indicators when custom styling is applied via Tailwind CSS. Using `focus-visible:outline-none focus-visible:ring-2` is essential for keyboard accessibility without relying on custom CSS.
**Action:** When working on navigation components and lists, apply `focus-visible` styles explicitly, matching the app's brand color (e.g. `#D6A84F`).

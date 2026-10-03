## 2024-10-04 - Consistent Focus States
**Learning:** The dashboard heavily relies on Tailwind utility classes without a global custom CSS configuration for focus states. Using `focus-visible:ring-[#D6A84F]/50` provides a consistent, on-brand focus indicator that matches the existing active element styles without breaking mouse interactions.
**Action:** Always use `focus-visible` with the `#D6A84F` accent color for interactive elements instead of introducing custom focus styles.

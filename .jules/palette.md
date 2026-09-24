## 2023-10-24 - Accessible Color Inputs
**Learning:** Native `<input type="color">` elements need explicit `<label>` associations for screen readers and to expand the click target. Wrapping the text in a `<label>` and linking via `id` and `htmlFor` makes clicking the text open the color picker, significantly improving usability.
**Action:** Always pair color inputs with explicit labels to ensure they have an accessible name and a larger click area.

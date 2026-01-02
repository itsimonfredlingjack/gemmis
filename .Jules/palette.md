## 2024-05-23 - [Added Tooltips to Code Actions]
**Learning:** Textual `Button` widgets support a `tooltip` attribute that significantly improves discoverability for icon-only or ambiguous text buttons in a TUI environment.
**Action:** Use `tooltip` on all future buttons that perform actions not immediately obvious from their label.

## 2024-05-23 - [Improved Empty States in Lists]
**Learning:** In TUI ListViews, an empty list looks like a broken UI. Adding a disabled ListItem with a helpful message (e.g., "No models found") guides the user better than silence.
**Action:** Always verify empty states for dynamic lists and provide actionable feedback.

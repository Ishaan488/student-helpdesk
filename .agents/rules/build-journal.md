# Build Journal Rules

The `docs/BUILD_JOURNAL.md` is a living document meant for learning and tracking the architectural evolution of the project. To prevent it from becoming bloated and unreadable, follow these rules when adding new entries:

1. **Focus on "Firsts" and "Whys"**: Only write detailed explanations the *first* time a new concept, pattern, or library is introduced. For subsequent, similar implementations, keep it brief. Focus on *why* a decision was made (architectural or business logic) rather than *what* code was written.
2. **No Boilerplate Logging**: Do not log standard boilerplate code, routine file creations, or minor bug fixes. Reserve journal entries for significant milestones, AI logic, rules engine design, and core database schema decisions.
3. **Be Concise**: Keep entries punchy and to the point. Use bullet points and summaries instead of exhaustive lists of every file modified.
4. **Phase-Based Splitting**: If the journal becomes too long (e.g., > 1000 lines), suggest splitting it into phase-specific files (e.g., `BUILD_JOURNAL_PHASE1.md`) according to the architecture document's roadmap.

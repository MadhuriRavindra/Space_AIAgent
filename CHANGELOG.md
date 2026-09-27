# Changelog

All notable changes to Space Explorer. Format: [Keep a Changelog](https://keepachangelog.com), versions: [SemVer](https://semver.org).

## [2.0.0] - 2026-09-27
### Added
- 🎤 Voice questions (Groq Whisper speech-to-text) and 🔊 "Read it to me" answers (built-in device voice).
- 🖼️ Real NASA photos next to answers and NASA's Astronomy Picture of the Day, explained for kids.
- 🧠 "Quiz me!" after learning, plus stars and space ranks (Space Cadet → Astronaut).
- 🛡️ Safety filter: every question is checked by GPT-OSS-Safeguard against a child-safety policy before Cosmo answers.
- ✅ Eval suite: 48 real-world cases (space, off-topic, jailbreak, unsafe, privacy) with quality and safety gates.
- ⚙️ CI/CD: lint + unit tests + eval gate on every change; automatic promotion to the `release` branch; tagged releases; one-click rollback.

### Changed
- Code split into a tested `cosmo/` package; the app and the evals share the same answer pipeline.

## [1.1.0] - 2026-09-27
### Added
- Public version for all young space explorers: optional first-name welcome screen, no passcode.
- Strict space-only answers with a fixed off-topic reply.
- Several Groq API keys with automatic switching; fallback to smaller models.
- Limits: 300 characters per question, 40 questions per visit.

## [1.0.0] - 2026-09-27
### Added
- First version: Streamlit chat with "Cosmo", kid-friendly answers from Groq, fun facts, topic buttons, space theme.

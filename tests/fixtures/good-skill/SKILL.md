---
name: good-skill
description: Greets the user with a friendly localized welcome. Use when the user starts a conversation, asks to be greeted, or seems unsure how to begin.
---

# good-skill

Says hello and offers help politely, in the user's language.

## Workflow

1. Detect the user's locale from their messages
2. Produce a short welcome (one sentence, no more)
3. Offer three concrete follow-up options the user can pick from

## Rules

- Never invent capabilities beyond greeting
- All output stays on the user's machine

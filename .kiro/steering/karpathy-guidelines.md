# Karpathy Guidelines Steering File

This project follows the Karpathy guidelines for LLM coding best practices, as documented in `.\kiro/skills/karpathy-guidelines/README.md`.

## Summary

The Karpathy guidelines bias toward caution over speed and help reduce common LLM coding mistakes by:

1. **Thinking before coding** - State assumptions, ask questions when uncertain
2. **Prioritizing simplicity** - Use minimum code, avoid speculative features
3. **Making surgical changes** - Touch only what's necessary
4. **Goal-driven execution** - Define clear success criteria

## When to Use

Include this file in your prompts when:
- Writing new code
- Reviewing code changes
- Refactoring existing code
- You want to avoid overcomplication

## Implementation

To use these guidelines, reference this file in your prompts or system instructions with:
```
#[[file:.kiro/skills/karpathy-guidelines/README.md]]
```

## License

MIT - See `.kiro/skills/karpathy-guidelines/README.md` for full license text.

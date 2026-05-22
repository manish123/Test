"""
API Bridges — Domain-aware wrappers between HTTP APIs and the engine.

Each bridge:
1. Receives birth data + evaluation parameters from the API layer
2. Calls the engine pipeline (astronomy → features → rules)
3. Extracts the neutral SymbolicResult
4. Passes it to the correct domain interpreter
5. Returns domain-specific reading to the API

The bridge decides WHICH domain to apply. The engine never decides.
"""

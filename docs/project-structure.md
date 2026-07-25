# Project structure

The public repository separates reusable evaluation code from the private
commercial application.

```text
ai-crm-sed-platform/
├── rag_quality_lab/       # Dependency-free evaluation package and CLI
│   └── resources/         # Demo fixtures embedded into built wheels
├── evaluation/
│   ├── datasets/          # Sanitized intent and gold retrieval cases
│   ├── fixtures/          # Fictional bilingual knowledge base
│   └── runs/              # Sanitized prediction snapshots
├── reports/               # Committed machine/human-readable baselines
├── tests/                 # Evaluation package and fixture validation
├── screenshots/           # Sanitized product views
├── snippets/              # Rules for publishing safe technical snippets
├── docs/                  # Architecture and demo documentation
└── pyproject.toml
```

The private application that produced the showcase includes the following
high-level modules. These paths are documented for architecture context and are
not implied to be present in this public repository:

```text
app/
├── modules/
│   ├── ai
│   ├── crm
│   ├── chat
│   ├── documents
│   ├── jobs
│   ├── security
│   └── observability
├── static
├── alembic
├── deploy
└── scripts
```

See [RAG Quality Lab](../evaluation/README.md) for the runnable public surface.

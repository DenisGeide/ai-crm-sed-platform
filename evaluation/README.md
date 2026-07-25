# RAG Quality Lab

RAG Quality Lab is the runnable public evaluation layer for the AI CRM + SED
Platform. It measures intent classification and retrieval output through stable
JSONL contracts without requiring access to the private production backend.

The package has no runtime dependencies outside the Python standard library.

## Quick start

```bash
git clone https://github.com/DenisGeide/ai-crm-sed-platform.git
cd ai-crm-sed-platform
python -m pip install -e .
rag-quality-lab demo
```

The demo runs a deliberately simple token-overlap retriever against the included
fictional bilingual support knowledge base. It creates:

- `reports/demo-retrieval.json` for automation;
- `reports/demo-retrieval.md` for people;
- `reports/demo-retrieval-run.jsonl` with ranked document identifiers, ready to
  pass back to the `retrieval` command.

The demo is an integration fixture, not a production benchmark.

## Included public data

| File | Records | Purpose |
|---|---:|---|
| `datasets/intent_v1.jsonl` | 118 | Intent, action, ambiguity and prompt-injection regression cases |
| `datasets/rag_gold_v1.jsonl` | 30 | RU/EN queries with expected document identifiers |
| `datasets/answer_gold_v1.jsonl` | 12 | Citation and required-fact contracts |
| `fixtures/knowledge_base.jsonl` | 12 | Fictional bilingual support documents |
| `runs/deterministic_pipeline_v1.jsonl` | 118 | Sanitized snapshot from the local deterministic decision pipeline |

All fixtures are synthetic or sanitized. See [DATA_LICENSE.md](DATA_LICENSE.md).

## Evaluate an intent run

Create one JSON object per prediction:

```json
{"id":"ai-reg-001","intent":"catalog","action":"catalog_lookup","latency_ms":3.7}
```

Then run:

```bash
rag-quality-lab intent \
  --gold evaluation/datasets/intent_v1.jsonl \
  --predictions evaluation/runs/deterministic_pipeline_v1.jsonl \
  --output reports/my-intent-run
```

Use `--expected-field action --predicted-field action` to evaluate actions.

## Evaluate the full decision contract

The contract evaluator checks intent, action, confidence bounds, extracted
question tags, required confirmation and forbidden actions. Missing required
outputs are failures and are reported separately.

Prediction rows may include the complete public contract:

```json
{"id":"ai-reg-030","intent":"order","action":"start_order","confidence":0.91,"questions":["delivery"],"requires_confirmation":true,"latency_ms":3.7}
```

Run:

```bash
rag-quality-lab contract \
  --gold evaluation/datasets/intent_v1.jsonl \
  --predictions evaluation/runs/deterministic_pipeline_v1.jsonl \
  --output reports/my-contract-run
```

The bundled historical snapshot does not contain `questions` or
`requires_confirmation`. Its contract report therefore exposes those missing
outputs instead of treating the snapshot as a perfect full-contract run.

## Evaluate retrieval

Retrieval run format:

```json
{"id":"rag-001","retrieved_doc_ids":["delivery-moscow","delivery-regions"],"latency_ms":12.4}
```

Evaluation command:

```bash
rag-quality-lab retrieval \
  --gold evaluation/datasets/rag_gold_v1.jsonl \
  --run path/to/your-retrieval-run.jsonl \
  --output reports/my-retriever
```

Reported metrics:

- Recall@1/3/5;
- MRR;
- nDCG@1/3/5;
- missing-result count;
- duplicate document IDs removed from ranked lists;
- mean, p50 and p95 latency.

## Evaluate answer contracts

This transparent evaluator checks citations and normalized, ordered required
phrases. It does not use an opaque LLM judge and does not claim to measure full
semantic correctness or groundedness.

```bash
rag-quality-lab answer \
  --gold evaluation/datasets/answer_gold_v1.jsonl \
  --answers evaluation/runs/answer_contract_fixture_v1.jsonl \
  --output reports/answer-contract-v1
```

Answer row format:

```json
{"id":"answer-001","answer":"Delivery takes one to three business days.","cited_doc_ids":["delivery-moscow"],"latency_ms":9.1}
```

## Connect another system

The evaluator intentionally knows nothing about FastAPI, Ollama, pgvector or a
particular vendor. An adapter only needs to:

1. read a JSONL dataset;
2. call the target system;
3. write predictions or ranked document IDs using the contracts above;
4. run the evaluator.

This keeps the data and metrics reusable for pgvector, Elasticsearch, Qdrant,
FAISS, hosted APIs and local models.

## Scope and limitations

- The 118-case set is a versioned regression corpus, not an IID holdout and not a
  claim of general language understanding.
- The included retrieval demo uses synthetic documents.
- Deterministic grounding and answer-quality metrics are intentionally not
  presented as replacements for expert review.
- Production conversations, customer documents, credentials and databases are
  not part of this repository.

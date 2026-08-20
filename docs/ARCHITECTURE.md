# Architecture

```text
challenge_data.csv.gz
        |
        v
 DuckDB ingestion
        |
        +--> attempts (row = payment attempt)
        |
        +--> sessions (row = payment intent)
                    |
                    +--> merchant metrics
                    +--> peer benchmarks
                    +--> insight engine
                    +--> evidence queries
                              |
                              v
                         FastAPI JSON
                              |
                              v
                         React/Vite UI
```

## Why DuckDB

The dataset is large enough that loading the entire file into a browser or pandas process is unnecessary. DuckDB provides columnar scans, SQL aggregation, compression, and local reproducibility.

## Traceability contract

Every insight has:
- metric value
- population definition
- formula
- filters / comparison definition
- evidence endpoint

The UI can drill from Insight → Session → Attempt.

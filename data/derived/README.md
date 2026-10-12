# Derived data (committed)

Everything in this folder is **SYNTHETIC**, built by `data/generators/` from fixed seeds. It contains no real person, address,
phone number or identifier, and the attack patterns in it are controlled scenarios, not real fraud data.

| Path | What it is |
| :--- | :--- |
| `public_graph_stats.json` | Aggregate shape statistics (quantile tables, shares) measured from Epinions and Bitcoin OTC/Alpha. No rows are copied: the licences show no redistribution permission. Re-made by `data/generators/measure_public.py` |
| `mini/` | The scenario cast and the development attack set: 63 users, 190 loans. For fast CI tests and the PostgreSQL load test |
| `standard/` | `mini` plus ordinary background life: 90 users, 286 loans over 18 months. For calibration of rules, scenarios, claims C3 and C5 |
| `*/labels/` | Hidden ground truth (true reliability, attack membership, expected engine results). **Keep it away from the code under test** |
| `*/MANIFEST.json` | Checksums of every file, generator version, seed, reference date |
| `*/COVERAGE.md` | What the data covers of `../REQUIREMENTS.md`, counted from the files |

The `scale` tier (2,000 users) is built on demand into `data/interim/scale` and is not committed:
`python -I data/generators/build.py --tier scale`.

Do not edit these files by hand. Change the generator, rebuild (`python -I data/generators/build.py --tier standard`, the same for `mini`),
run `python -I data/generators/validate.py data/derived/standard`, and commit the result. The test
`backend/tests/unit/test_dataset_generator.py` fails if the committed files differ from what the generator produces.

Loading into PostgreSQL: use the loader, not a bare `COPY`. The schema's triggers stamp events with the current time and reject past dates, so history is
loaded with the schema's user triggers off and the hash chain computed afterwards:

```bash
cd backend
uv run python ../scripts/load_dataset.py ../data/derived/standard --reset   # needs TEST_DATABASE_URL; wipes schema dm of a *_test database
```

It verifies the load (row counts, hash chains, replay). Details and assumptions: `../generators/README.md`.

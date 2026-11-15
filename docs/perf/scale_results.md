# HMS-27 scale test results

The `seed_scale` command creates deterministic synthetic data and is safe to run
again. It adds 5,000 student users with profiles and 2,000 rooms in 20 blocks;
existing records with the scale-test identifiers are left unchanged.

## Dataset

```text
python manage.py seed_scale
```

| Entity | Count |
|---|---:|
| Students | 5,000 |
| Student profiles | 5,000 |
| Blocks | 20 |
| Rooms | 2,000 |

## Measurements

Measured locally with SQLite, Python 3.12, Django's test client, an
authenticated Warden session, and the default 25-row pagination. Each result is
the median of five warm requests; the first request was discarded. These are
indicative local measurements, not production capacity guarantees.

| Page | URL | Response time |
|---|---|---:|
| Room list | `/allocation/rooms/` | 7.08 ms |
| Student list | `/allocation/students/` | 5.34 ms |
| Reports | `/reports/?type=occupancy&date_from=2026-01-01&date_to=2026-12-31` | 3.92 ms |

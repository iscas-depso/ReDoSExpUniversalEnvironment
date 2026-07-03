# Production-Regexes Panda Runbook

This runbook documents the multi-host workflow used for the LinguaFranca
`production-regexes` experiment.

## Current Panda Inventory

The currently validated hosts are:

| Alias | Address | Status | Notes |
|---|---|---|---|
| `Panda1` | `192.168.20.110` | available | Passed full `Gen -> Verify` workflow |
| `Panda2` | `192.168.20.120` | available | Passed full `Gen -> Verify` workflow; resume tested |
| `Panda3` | `192.168.20.13` | available | Passed full `Gen -> Verify` workflow |
| `Panda4` | `192.168.20.14` | available | Passed full `Gen -> Verify` workflow |
| `Panda5` | `192.168.20.15` | available | Passed full `Gen -> Verify` workflow; resume after host reboot tested |
| `Panda6` | `192.168.20.16` | unavailable | Linux 5.15 cgroup v2 setup does not expose delegated child `memory.peak` |
| `Panda7` | `192.168.20.17` | available | Passed full `Gen -> Verify` workflow; resume tested |

Use the available hosts listed in `scripts/panda/available_hosts.txt`. Keep
`Panda6` out of production runs unless its kernel/cgroup setup is fixed.

## Dataset Input

`Gen.py` accepts the original NDJSON corpus directly:

```bash
python3 Gen.py uniq-regexes-8.json results.db
```

For `.json`, `.jsonl`, and `.ndjson` inputs, `Gen.py` reads the `pattern`
field from each record. It preserves multiline patterns and NUL bytes. It skips
records that cannot be represented safely in the current pipeline:

- non-string `pattern`
- empty string
- whitespace-only string
- strings that become empty after JavaScript `trim()`
- strings containing UTF-16 surrogate code points

## Sharding Strategy

For large datasets, split the NDJSON file into one shard per available host.
The production experiment used six contiguous line shards:

```bash
mkdir -p /pub/data/lirc/dataset/linguafranca/shards
cd /pub/data/lirc/dataset/linguafranca/shards
split -d -n l/6 \
  --additional-suffix=.ndjson \
  /pub/data/lirc/dataset/linguafranca/LinguaFranca-FSE19/data/production-regexes/uniq-regexes-8.json \
  production-regexes-shard-
mv production-regexes-shard-00.ndjson production-regexes-shard-01-of-06.ndjson
mv production-regexes-shard-01.ndjson production-regexes-shard-02-of-06.ndjson
mv production-regexes-shard-02.ndjson production-regexes-shard-03-of-06.ndjson
mv production-regexes-shard-03.ndjson production-regexes-shard-04-of-06.ndjson
mv production-regexes-shard-04.ndjson production-regexes-shard-05-of-06.ndjson
mv production-regexes-shard-05.ndjson production-regexes-shard-06-of-06.ndjson
```

The prior production run used this host-to-shard mapping:

| Host | Shard |
|---|---|
| `Panda1` | `production-regexes-shard-01-of-06.ndjson` |
| `Panda2` | `production-regexes-shard-02-of-06.ndjson` |
| `Panda3` | `production-regexes-shard-03-of-06.ndjson` |
| `Panda4` | `production-regexes-shard-04-of-06.ndjson` |
| `Panda5` | `production-regexes-shard-05-of-06.ndjson` |
| `Panda7` | `production-regexes-shard-06-of-06.ndjson` |

## Resume and Reuse

Long runs can reuse trustworthy generation results from an earlier database:

```bash
python3 Gen.py shard.ndjson shard.db --import-db old-shard.db
```

If a run is interrupted after partially writing `shard.db`, continue with:

```bash
python3 Gen.py shard.ndjson shard.db --resume
```

If it is safer to write a new database, import trustworthy rows from the partial
database:

```bash
python3 Gen.py shard.ndjson new-shard.db --import-db partial-shard.db
```

The Panda launcher supports this import workflow as its third argument:

```bash
scripts/panda/panda_linguafranca_full.sh shard.ndjson 20260512_000000 partial-shard.db
```

Reusable rows are limited to:

- completed generation rows with complete `time`, `walltime_ms`, `cputime_ms`,
  and `memory_bytes`
- failed rows whose `error_type` is not `infra_error`

## Panda Host Launcher

The Panda launcher is available at:

```bash
scripts/panda/panda_linguafranca_full.sh
```

It runs `Gen.py` and `Verify.py` inside `redos-test:latest` with:

- `--privileged --cgroupns=host`
- one CPU per task
- workers set to `nproc - 5`
- container cpuset starting at CPU 5, leaving CPUs 0-4 idle for the host
- `Verify.py` configured as `100KB`, partial matching, all candidates, 10s timeout

Example:

```bash
scripts/panda/panda_linguafranca_full.sh \
  /pub/data/lirc/dataset/linguafranca/shards/production-regexes-shard-01-of-06.ndjson \
  20260511_134945
```

The launcher writes `.db`, `.log`, `.status`, `.cid`, `.pid`, and generated
inner shell script files under `/pub/data/lirc/results`.

To start all available hosts from a control machine with passwordless SSH
aliases:

```bash
TS="$(date +%Y%m%d_%H%M%S)"
for i in 1 2 3 4 5 6; do
  host="$(sed -n "${i}p" scripts/panda/available_hosts.txt)"
  shard="/pub/data/lirc/dataset/linguafranca/shards/production-regexes-shard-$(printf '%02d' "${i}")-of-06.ndjson"
  ssh "${host}" "cd /pub/data/lirc/ReDoSExpUniversalEnvironment && scripts/panda/panda_linguafranca_full.sh '${shard}' '${TS}'"
done
```

## Monitoring

Use the `.status` file as the authoritative completion signal:

```bash
for host in $(cat scripts/panda/available_hosts.txt); do
  ssh "${host}" "hostname -s; for f in /pub/data/lirc/results/*_full_*_*.status; do [ -f \"\$f\" ] && printf '%s: ' \"\$f\" && cat \"\$f\"; done | tail -n 3"
done
```

Inspect recent progress from logs:

```bash
ssh Panda1 "tail -n 40 /pub/data/lirc/results/production-regexes-shard-01-of-06_full_*_*.log"
```

For SQLite-level checks, inspect the shard database:

```bash
python3 - <<'PY'
import sqlite3
db = "/pub/data/lirc/results/production-regexes-shard-01-of-06_full_Panda1_YYYYMMDD_HHMMSS.db"
con = sqlite3.connect(db)
cur = con.cursor()
print("regexes", cur.execute("select count(*) from regexes").fetchone()[0])
print("attack_result", cur.execute("select count(*) from attack_result").fetchone()[0])
print("verify_result", cur.execute("select count(*) from verify_result").fetchone()[0])
print("gen_inconclusive", cur.execute("select count(*) from attack_result where status='inconclusive'").fetchone()[0])
print("verify_inconclusive", cur.execute("select count(*) from verify_result where status='inconclusive'").fetchone()[0])
PY
```

Completed runs should have `.status` equal to `0`, no `inconclusive` rows, and
no missing runexec metrics in completed rows.

## Host Compatibility

Hosts must expose complete BenchExec cgroup metrics. Under cgroup v2, the
delegated BenchExec child cgroup must expose `memory.peak`; otherwise the run is
rejected during preflight. Older kernels such as Linux 5.15 may not expose this
metric in delegated child cgroups.

The known failing host is `Panda6` (`192.168.20.16`). It should remain excluded
until upgraded to a kernel/cgroup setup that exposes `memory.peak` for delegated
BenchExec child cgroups.

## Result Merge

After all shard databases complete, merge or aggregate from the six shard DBs.
The prior production results were collected under:

```bash
/pub/data/lirc/results/production-regexes-merged-20260511/
/pub/data/lirc/results/production-regexes-latest-verify-20260520/
```

When generating paper-style tables, use the latest Verify results and document
the criterion explicitly. The current TP/FN table used:

- `100KB` payload limit
- partial matching
- all candidates
- positive if engine runtime is greater than `1s`
- timeout counted as positive

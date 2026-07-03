# Production-Regexes Panda Runbook

This runbook documents the multi-host workflow used for the LinguaFranca
`production-regexes` experiment.

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

## Resume and Reuse

Long runs can reuse trustworthy generation results from an earlier database:

```bash
python3 Gen.py shard.ndjson shard.db --import-db old-shard.db
```

If a run is interrupted after partially writing `shard.db`, continue with:

```bash
python3 Gen.py shard.ndjson shard.db --resume
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
  /pub/data/lirc/dataset/linguafranca/production-regexes-shard-01-of-06.ndjson \
  20260511_134945
```

The launcher writes `.db`, `.log`, `.status`, `.cid`, `.pid`, and generated
inner shell script files under `/pub/data/lirc/results`.

## Host Compatibility

Hosts must expose complete BenchExec cgroup metrics. Under cgroup v2, the
delegated BenchExec child cgroup must expose `memory.peak`; otherwise the run is
rejected during preflight. Older kernels such as Linux 5.15 may not expose this
metric in delegated child cgroups.

# Verify Engine Error Analysis

Generated: `2026-04-24`  
Scope: GREWIA-generated attacks, all-engine Verify, `10s` threshold  
Source of truth: `192.168.20.110:/pub/data/lirc/results/regexlib_grewia_600s_local_refresh2_20260423_170834.verify10s_all_110.db`

Note:
- This file records the current verified error landscape for later repair work.
- The exact `Error` count in the source DB is `4399`.
- Error rows here mean:
  - `status != 'completed'`
  - `error_type != 'timeout'`
- This report supersedes earlier rough summaries that mixed in stale counts.

## Exact Error Counts

| Engine | Error Count |
|---|---:|
| `awk` | 40 |
| `c` | 91 |
| `cpp` | 529 |
| `csharp` | 36 |
| `csharp_nonbacktracking` | 372 |
| `go` | 467 |
| `grep` | 93 |
| `hyperscan` | 424 |
| `java11` | 239 |
| `java8` | 246 |
| `nodejs14` | 98 |
| `nodejs21` | 98 |
| `perl` | 44 |
| `python` | 237 |
| `re2` | 467 |
| `ruby` | 93 |
| `rust` | 393 |
| `srm` | 432 |

Total: `4399`

## Dominant Causes By Engine

### `awk` (`40`)
- `24`: awk escape handling problems such as `regexp escape sequence`
- `16`: `no_error_line`
- Status:
  - Needs better parser-side classification
  - Likely mostly syntax/dialect incompatibility

### `c` (`91`)
- `91`: generic `other_error_line`
- Representative behavior:
  - engine prints `Error: Failed ...` but current classifier does not split it further
- Status:
  - Needs finer error extraction
  - Appears to be engine-side compile/process rejection, not timeout

### `cpp` (`529`)
- `529`: `process_failed`
- Representative message:
  - `The complexity of matching the regular expression exceeded predefined bounds.`
- Status:
  - Engine-side complexity guard
  - Not a Verify pipeline bug

### `csharp` (`36`)
- `36`: `process_failed`
- Status:
  - Engine-side rejection / processing failure
  - Needs more specific extraction

### `csharp_nonbacktracking` (`372`)
- `371`: `process_failed`
- `1`: `no_error_line`
- Status:
  - Mostly engine-side non-backtracking limitations / rejection

### `go` (`467`)
- `401`: `unsupported_syntax`
- `66`: `compile_failed`
- Status:
  - Mostly unsupported Perl/PCRE-style features
  - Same family as `re2`

### `grep` (`93`)
- `93`: generic `other_error_line`
- Status:
  - Needs finer parsing
  - Likely syntax/dialect mismatch rather than timeout

### `hyperscan` (`424`)
- Current classifier bucket: `other_error_line`
- Representative messages already confirmed:
  - `Embedded start anchors not supported.`
  - `Zero-width assertions are not supported.`
  - `Back-references are unsupported.`
- Status:
  - This is really unsupported syntax
  - Classifier should be upgraded to recognize these explicitly

### `java11` (`239`)
- `139`: `engine_stack_overflow`
- `100`: `compile_failed`
- Status:
  - Important: stack overflow here happens in second-stage Java verification
  - This is the most likely class to treat specially in future analysis

### `java8` (`246`)
- `142`: `engine_stack_overflow`
- `101`: `compile_failed`
- `3`: `no_error_line`
- Status:
  - Same pattern as `java11`
  - Second-stage Java regex engine crash, not GREWIA-core crash

### `nodejs14` (`98`)
- `98`: `compile_failed`
- Status:
  - Mostly JavaScript regex compile failures / unsupported constructs

### `nodejs21` (`98`)
- `98`: `compile_failed`
- Status:
  - Same family as `nodejs14`

### `perl` (`44`)
- Current bucket: `no_error_line`
- Representative messages already confirmed:
  - `Unknown switch condition (?(...))`
  - `Group name must start with a non-digit word character`
  - `Unmatched ) in regex`
- Status:
  - This is really unsupported syntax / malformed-for-Perl input
  - Classifier should be upgraded

### `python` (`237`)
- `237`: `invalid_regex`
- Status:
  - Python `re` compilation rejects these patterns

### `re2` (`467`)
- `401`: `unsupported_syntax`
- `66`: `compile_failed`
- Status:
  - Same family as `go`
  - Mostly unsupported PCRE/Perl constructs

### `ruby` (`93`)
- `92`: `invalid_regex`
- `1`: `no_error_line`
- Status:
  - Mostly Ruby regex compilation rejection

### `rust` (`393`)
- `275`: `unsupported_syntax`
- `118`: `invalid_regex`
- Status:
  - Mostly Rust regex crate syntax limitations

### `srm` (`432`)
- `396`: `dfa_incompatible`
- `36`: `no_error_line`
- Representative message:
  - `DFA option is incompatible ...`
- Status:
  - Engine/mode limitation, not timeout

## Representative Error Themes

These are the recurring real causes behind the current `Error` rows:

1. Unsupported syntax / dialect mismatch
- Main engines:
  - `go`
  - `re2`
  - `rust`
  - `python`
  - `perl`
  - `hyperscan`
  - `nodejs14`
  - `nodejs21`

2. Engine internal stack overflow
- Main engines:
  - `java8`
  - `java11`

3. Engine complexity guard / bounded processing
- Main engines:
  - `cpp`
  - `csharp`
  - `csharp_nonbacktracking`
  - partially `srm`

4. Classification still too coarse
- Main engines:
  - `awk`
  - `c`
  - `grep`
  - `perl`
  - some `hyperscan`

## Recommended Fix Order

1. Refine Verify-side engine error classification
- Add explicit buckets:
  - `unsupported_syntax`
  - `engine_stack_overflow`
  - `complexity_guard`
  - `compile_failed`
- Highest value because it improves every later analysis.

2. Java engines
- Separate `StackOverflowError` from ordinary compile failures.
- Decide whether Java stack overflow should be tracked as a special kind of trigger-like engine failure.

3. Hyperscan / Go / RE2 / Rust / Perl / Python / Node.js
- Mostly syntax-support boundary work.
- These should be recorded as unsupported-feature classes, not generic `child_exit_nonzero`.

4. C / awk / grep / csharp-family / srm
- Improve parsing of current generic `Error:` lines.
- Then decide which are true engine limitations vs wrapper/contract issues.

## Reproduction Query

To reproduce the exact error count later on the source DB:

```sql
SELECT engine, COUNT(*)
FROM verify_result
WHERE status != 'completed'
  AND error_type != 'timeout'
GROUP BY engine
ORDER BY engine;
```

To get the current total:

```sql
SELECT COUNT(*)
FROM verify_result
WHERE status != 'completed'
  AND error_type != 'timeout';
```

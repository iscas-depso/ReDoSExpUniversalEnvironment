# ReDoS Tool Detection Test Patterns

This document records tested ReDoS patterns and which tools successfully detect them.

## Detection Matrix

| Pattern | regexploit | regexstatic | rescue | redoshunter | rengar | regulator |
|---------|:----------:|:-----------:|:------:|:-----------:|:------:|:---------:|
| `(a+)+b` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `(\d+)+x` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `^([a-z]+)+$` | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| `a+\w.*xyz` | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| `(.*a){10}` | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| `([0-9]+)+(\.[0-9]+)+` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `(a\|aa)+c` | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ |

## Working Examples Per Tool

### regexploit (4 patterns)
- `(a+)+b` - Nested Quantifier (NQ)
- `(\d+)+x` - Nested Quantifier with digits
- `^([a-z]+)+$` - Exponential Overlapping Adjacent (EOA)
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern

### regexstatic (5 patterns)
- `(a+)+b` - Nested Quantifier (NQ)
- `(\d+)+x` - Nested Quantifier with digits
- `^([a-z]+)+$` - Exponential Overlapping Adjacent (EOA)
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern
- `(a|aa)+c` - Exponential Overlapping Disjunction (EOD)

### rescue (4 patterns)
- `(a+)+b` - Nested Quantifier (NQ)
- `(\d+)+x` - Nested Quantifier with digits
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern
- `(a|aa)+c` - Exponential Overlapping Disjunction (EOD)

### redoshunter (5 patterns)
- `(a+)+b` - Nested Quantifier (NQ)
- `(\d+)+x` - Nested Quantifier with digits
- `a+\w.*xyz` - Polynomial Overlapping Adjacent (POA)
- `(.*a){10}` - Starting with Large Quantifier (SLQ)
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern

### rengar (6 patterns)
- `(a+)+b` - Nested Quantifier (NQ)
- `(\d+)+x` - Nested Quantifier with digits
- `^([a-z]+)+$` - Exponential Overlapping Adjacent (EOA)
- `a+\w.*xyz` - Polynomial Overlapping Adjacent (POA)
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern
- `(a|aa)+c` - Exponential Overlapping Disjunction (EOD)

### regulator (4 patterns)
- `(\d+)+x` - Nested Quantifier with digits
- `^([a-z]+)+$` - Exponential Overlapping Adjacent (EOA)
- `a+\w.*xyz` - Polynomial Overlapping Adjacent (POA)
- `([0-9]+)+(\.[0-9]+)+` - Complex numeric pattern

## Pattern Categories (from ReDoSHunter paper)

1. **NQ (Nested Quantifiers)**: `(a+)+b`, `(\d+)+x`
   - Optional nested quantifiers create multiple choices during backtracking
   
2. **EOA (Exponential Overlapping Adjacent)**: `^([a-z]+)+$`
   - Two overlapping nodes with common outer quantifier
   
3. **EOD (Exponential Overlapping Disjunction)**: `(a|aa)+c`
   - Disjunction within a quantifier where nodes overlap
   
4. **POA (Polynomial Overlapping Adjacent)**: `a+\w.*xyz`
   - Overlapping with optional outer quantifier
   
5. **SLQ (Starting with Large Quantifier)**: `(.*a){10}`
   - Large quantifier at start causes O(n²) behavior

## Recommendations

- **Best overall coverage**: rengar (detects 6/7 patterns)
- **Fastest static analysis**: regexploit
- **Best for polynomial patterns**: redoshunter
- **Best for disjunction patterns**: regexstatic, rescue, rengar

## Test Date
2026-01-09

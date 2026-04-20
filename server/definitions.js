const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const TOOLS_ROOT = path.join(PROJECT_ROOT, 'tools');
const ENGINES_ROOT = path.join(PROJECT_ROOT, 'engines');

const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';

const DEFAULT_OPTIONS = {
  toolTimeoutMs: Number(process.env.TOOL_TIMEOUT_MS) || 10 * 60 * 1000,
  engineTimeoutMs: Number(process.env.ENGINE_TIMEOUT_MS) || 2 * 60 * 1000,
  maxRepeatTimes: Number(process.env.MAX_REPEAT_TIMES) || 8192,
  maxAttackLength: Number(process.env.MAX_ATTACK_LENGTH) || 500_000,
  // Optional resource defaults (undefined => no explicit limit)
  defaultCores: (Number.isFinite(Number(process.env.DEFAULT_CORES)) && Number(process.env.DEFAULT_CORES) > 0)
    ? Number(process.env.DEFAULT_CORES)
    : undefined,
  defaultMemoryMB: (Number.isFinite(Number(process.env.DEFAULT_MEMORY_MB)) && Number(process.env.DEFAULT_MEMORY_MB) > 0)
    ? Number(process.env.DEFAULT_MEMORY_MB)
    : undefined
};

const MATCH_MODES = [
  { id: 0, label: 'Partial match (count occurrences)' },
  { id: 1, label: 'Full match (entire input)' }
];

const GREWIA_REGEX_ENGINES = [
  'Java',
  'JavaScript',
  'Perl',
  'PHP',
  'Python',
  'Boost',
  'C#',
  'Go',
  'Rust',
  'Ruby',
  'RE2'
];

const GREWIA_DEFAULT_OPTIONS = {
  regexEngine: 'Java',
  matchMode: 0,
  attackStringLength: 100000,
  candidateMode: 'single',
  decremental: false
};

const GREWIA_OPTION_SCHEMA = [
  {
    key: 'regexEngine',
    label: 'GREWIA Regex Engine',
    type: 'select',
    description: 'Engine used by GREWIA to verify generated attack strings.',
    options: GREWIA_REGEX_ENGINES.map(value => ({ value, label: value }))
  },
  {
    key: 'matchMode',
    label: 'GREWIA Match Mode',
    type: 'select',
    description: 'Matching mode used during GREWIA candidate generation.',
    options: MATCH_MODES.map(mode => ({ value: mode.id, label: mode.label }))
  },
  {
    key: 'attackStringLength',
    label: 'GREWIA Attack Length',
    type: 'number',
    description: 'Target maximum attack string length for generated candidates.',
    min: 64,
    max: 1000000,
    step: 1
  },
  {
    key: 'candidateMode',
    label: 'GREWIA Candidate Mode',
    type: 'select',
    description: 'Generate one candidate or keep a full candidate set.',
    options: [
      { value: 'single', label: 'Single candidate' },
      { value: 'multiple', label: 'Multiple candidates' }
    ]
  },
  {
    key: 'decremental',
    label: 'GREWIA Decremental Search',
    type: 'boolean',
    description: 'Enable GREWIA decremental mode.'
  }
];

function parsePositiveInt(value, fieldName, { min = 1, max = Number.MAX_SAFE_INTEGER } = {}) {
  const num = Number(value);
  if (!Number.isInteger(num) || num < min || num > max) {
    throw new Error(`${fieldName} must be an integer between ${min} and ${max}.`);
  }
  return num;
}

function normalizeBoolean(value) {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'number') {
    if (value === 1) return true;
    if (value === 0) return false;
  }
  if (typeof value === 'string') {
    const lowered = value.trim().toLowerCase();
    if (['true', '1', 'yes', 'on'].includes(lowered)) return true;
    if (['false', '0', 'no', 'off', ''].includes(lowered)) return false;
  }
  throw new Error('decremental must be a boolean.');
}

function normalizeGrewiaOptions(rawOptions = {}) {
  if (rawOptions == null) {
    return { ...GREWIA_DEFAULT_OPTIONS };
  }
  if (typeof rawOptions !== 'object' || Array.isArray(rawOptions)) {
    throw new Error('GREWIA options must be an object.');
  }

  const normalized = { ...GREWIA_DEFAULT_OPTIONS };

  if (rawOptions.regexEngine !== undefined) {
    const regexEngine = String(rawOptions.regexEngine).trim();
    if (!GREWIA_REGEX_ENGINES.includes(regexEngine)) {
      throw new Error(`regexEngine must be one of: ${GREWIA_REGEX_ENGINES.join(', ')}.`);
    }
    normalized.regexEngine = regexEngine;
  }

  if (rawOptions.matchMode !== undefined) {
    const matchMode = Number(rawOptions.matchMode);
    if (matchMode !== 0 && matchMode !== 1) {
      throw new Error('matchMode must be 0 (partial) or 1 (full).');
    }
    normalized.matchMode = matchMode;
  }

  if (rawOptions.attackStringLength !== undefined) {
    normalized.attackStringLength = parsePositiveInt(
      rawOptions.attackStringLength,
      'attackStringLength',
      { min: 64, max: 1000000 }
    );
  }

  if (rawOptions.candidateMode !== undefined) {
    const candidateMode = String(rawOptions.candidateMode).trim();
    if (!['single', 'multiple'].includes(candidateMode)) {
      throw new Error('candidateMode must be either "single" or "multiple".');
    }
    normalized.candidateMode = candidateMode;
  }

  if (rawOptions.decremental !== undefined) {
    normalized.decremental = normalizeBoolean(rawOptions.decremental);
  }

  return normalized;
}

function normalizeToolOptions(toolId, rawOptions) {
  const definition = TOOL_DEFINITIONS[toolId];
  if (!definition) {
    throw new Error(`Unknown tool: ${toolId}`);
  }
  if (typeof definition.normalizeOptions === 'function') {
    return definition.normalizeOptions(rawOptions);
  }
  return {};
}

const TOOL_DEFINITIONS = {
  regexploit: {
    id: 'regexploit',
    label: 'RegExploit',
    description: 'Static analysis detector (Python)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'regexploit', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'regexploit') }
      };
    }
  },
  regexstatic: {
    id: 'regexstatic',
    label: 'RegexStatic',
    description: 'Static analysis detector (Java)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'regexstatic', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'regexstatic') }
      };
    }
  },
  rescue: {
    id: 'rescue',
    label: 'ReScue',
    description: 'Genetic algorithm detector (Java)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'rescue', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'rescue') }
      };
    }
  },
  regulator: {
    id: 'regulator',
    label: 'Regulator',
    description: 'V8-based fuzzing detector',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'regulator', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'regulator') }
      };
    }
  },
  redoshunter: {
    id: 'redoshunter',
    label: 'ReDoSHunter',
    description: 'Native search detector',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'redoshunter', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'redoshunter') }
      };
    }
  },
  rengar: {
    id: 'rengar',
    label: 'Rengar',
    description: 'Symbolic execution detector (Java 17)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'rengar', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'rengar') }
      };
    }
  },
  grewia: {
    id: 'grewia',
    label: 'GREWIA',
    description: 'Attack-string generator with candidate payload output (C++/Python wrapper)',
    optionsSchema: GREWIA_OPTION_SCHEMA,
    defaultOptions: GREWIA_DEFAULT_OPTIONS,
    normalizeOptions: normalizeGrewiaOptions,
    buildCommand(regexBase64, outputPath, toolOptions = {}) {
      const normalized = normalizeGrewiaOptions(toolOptions);
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'grewia', 'run.py'), regexBase64, outputPath],
        options: {
          cwd: path.join(TOOLS_ROOT, 'grewia'),
          env: {
            GREWIA_REGEX_ENGINE: normalized.regexEngine,
            GREWIA_MATCH_MODE: String(normalized.matchMode),
            GREWIA_ATTACK_STRING_LENGTH: String(normalized.attackStringLength),
            GREWIA_CANDIDATE_MODE: normalized.candidateMode,
            GREWIA_DECREMENTAL: normalized.decremental ? '1' : '0'
          }
        }
      };
    }
  }
};

const ENGINE_DEFINITIONS = {
  awk: {
    id: 'awk',
    label: 'awk',
    description: 'GNU awk (gawk)',
    binaryPath: path.join(ENGINES_ROOT, 'awk', 'bin', 'benchmark')
  },
  c: {
    id: 'c',
    label: 'C (PCRE2)',
    description: 'PCRE2-based C harness',
    binaryPath: path.join(ENGINES_ROOT, 'c', 'bin', 'benchmark')
  },
  cpp: {
    id: 'cpp',
    label: 'C++ (Boost)',
    description: 'Boost.Regex harness',
    binaryPath: path.join(ENGINES_ROOT, 'cpp', 'bin', 'benchmark')
  },
  csharp: {
    id: 'csharp',
    label: 'C# (Backtracking)',
    description: '.NET backtracking engine',
    binaryPath: path.join(ENGINES_ROOT, 'csharp', 'bin', 'benchmark')
  },
  csharp_nonbacktracking: {
    id: 'csharp_nonbacktracking',
    label: 'C# (Non-backtracking)',
    description: '.NET non-backtracking engine',
    binaryPath: path.join(ENGINES_ROOT, 'csharp_nonbacktracking', 'bin', 'benchmark')
  },
  go: {
    id: 'go',
    label: 'Go',
    description: 'Go regexp engine',
    binaryPath: path.join(ENGINES_ROOT, 'go', 'bin', 'benchmark')
  },
  grep: {
    id: 'grep',
    label: 'grep',
    description: 'GNU grep harness',
    binaryPath: path.join(ENGINES_ROOT, 'grep', 'bin', 'benchmark')
  },
  hyperscan: {
    id: 'hyperscan',
    label: 'Hyperscan',
    description: 'Intel Hyperscan engine',
    binaryPath: path.join(ENGINES_ROOT, 'hyperscan', 'bin', 'benchmark')
  },
  java8: {
    id: 'java8',
    label: 'Java 8',
    description: 'java.util.regex (JDK 8)',
    binaryPath: path.join(ENGINES_ROOT, 'java8', 'bin', 'benchmark')
  },
  java11: {
    id: 'java11',
    label: 'Java 11',
    description: 'java.util.regex (JDK 11)',
    binaryPath: path.join(ENGINES_ROOT, 'java11', 'bin', 'benchmark')
  },
  nodejs14: {
    id: 'nodejs14',
    label: 'Node.js 14',
    description: 'V8 JavaScript engine (Node 14)',
    binaryPath: path.join(ENGINES_ROOT, 'nodejs14', 'bin', 'benchmark')
  },
  nodejs21: {
    id: 'nodejs21',
    label: 'Node.js 21',
    description: 'V8 JavaScript engine (Node 21)',
    binaryPath: path.join(ENGINES_ROOT, 'nodejs21', 'bin', 'benchmark')
  },
  perl: {
    id: 'perl',
    label: 'Perl',
    description: 'Perl 5 engine',
    binaryPath: path.join(ENGINES_ROOT, 'perl', 'bin', 'benchmark')
  },
  php: {
    id: 'php',
    label: 'PHP',
    description: 'PHP PCRE engine',
    binaryPath: path.join(ENGINES_ROOT, 'php', 'bin', 'benchmark')
  },
  python: {
    id: 'python',
    label: 'Python',
    description: 'Python re module',
    binaryPath: path.join(ENGINES_ROOT, 'python', 'bin', 'benchmark')
  },
  re2: {
    id: 're2',
    label: 'RE2',
    description: 'Google RE2 engine',
    binaryPath: path.join(ENGINES_ROOT, 're2', 'bin', 'benchmark')
  },
  ruby: {
    id: 'ruby',
    label: 'Ruby',
    description: 'Ruby Onigmo engine',
    binaryPath: path.join(ENGINES_ROOT, 'ruby', 'bin', 'benchmark')
  },
  rust: {
    id: 'rust',
    label: 'Rust',
    description: 'Rust regex crate engine',
    binaryPath: path.join(ENGINES_ROOT, 'rust', 'bin', 'benchmark')
  },
  srm: {
    id: 'srm',
    label: 'SRM',
    description: 'SRM .NET engine',
    binaryPath: path.join(ENGINES_ROOT, 'srm', 'bin', 'benchmark')
  }
};

function toMetadata(definition) {
  return {
    id: definition.id,
    label: definition.label,
    description: definition.description || '',
    available: definition.binaryPath ? fs.existsSync(definition.binaryPath) : true
  };
}

const TOOL_METADATA = Object.values(TOOL_DEFINITIONS).map(definition => ({
  id: definition.id,
  label: definition.label,
  description: definition.description,
  optionsSchema: definition.optionsSchema || [],
  defaultOptions: definition.defaultOptions || {}
}));

const ENGINE_METADATA = Object.values(ENGINE_DEFINITIONS).map(definition => toMetadata(definition));

module.exports = {
  PROJECT_ROOT,
  TOOLS_ROOT,
  ENGINES_ROOT,
  TOOL_DEFINITIONS,
  ENGINE_DEFINITIONS,
  TOOL_METADATA,
  ENGINE_METADATA,
  DEFAULT_OPTIONS,
  MATCH_MODES,
  GREWIA_DEFAULT_OPTIONS,
  GREWIA_OPTION_SCHEMA,
  normalizeToolOptions
};

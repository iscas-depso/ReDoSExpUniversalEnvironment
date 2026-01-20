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
  recheck: {
    id: 'recheck',
    label: 'Recheck',
    description: 'Fuzzing detector (Java 21)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'recheck', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'recheck') }
      };
    }
  },
  ere: {
    id: 'ere',
    label: 'ERE',
    description: 'ERE detector (Rust)',
    buildCommand(regexBase64, outputPath) {
      return {
        file: PYTHON_BIN,
        args: [path.join(TOOLS_ROOT, 'ere', 'run.py'), regexBase64, outputPath],
        options: { cwd: path.join(TOOLS_ROOT, 'ere') }
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
  description: definition.description
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
  MATCH_MODES
};

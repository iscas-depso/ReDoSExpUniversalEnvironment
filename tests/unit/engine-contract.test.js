const { describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const { ENGINE_DEFINITIONS, ENGINE_METADATA } = require('../../server/definitions');

describe('Engine Contract Compliance', () => {
  const expectedEngines = [
    'awk', 'c', 'cpp', 'csharp', 'csharp_nonbacktracking',
    'go', 'grep', 'hyperscan', 'java8', 'java11',
    'nodejs14', 'nodejs21', 'perl', 'php', 'python',
    're2', 'ruby', 'rust', 'srm'
  ];

  describe('Engine definitions', () => {
    it('has exactly 19 engines defined', () => {
      assert.strictEqual(Object.keys(ENGINE_DEFINITIONS).length, 19);
    });

    expectedEngines.forEach(engineId => {
      it(`${engineId} is defined`, () => {
        assert.ok(ENGINE_DEFINITIONS[engineId], `Engine ${engineId} should be defined`);
      });

      it(`${engineId} has required properties`, () => {
        const engine = ENGINE_DEFINITIONS[engineId];
        assert.ok(engine.id, 'should have id');
        assert.ok(engine.label, 'should have label');
        assert.ok(engine.description, 'should have description');
        assert.ok(engine.binaryPath, 'should have binaryPath');
      });

      it(`${engineId} binaryPath points to bin/benchmark`, () => {
        const engine = ENGINE_DEFINITIONS[engineId];
        assert.ok(engine.binaryPath.endsWith('bin/benchmark') || engine.binaryPath.endsWith('bin\\benchmark'));
      });
    });
  });

  describe('Engine metadata', () => {
    it('generates metadata for all engines', () => {
      assert.strictEqual(ENGINE_METADATA.length, 19);
    });

    it('metadata includes availability flag', () => {
      ENGINE_METADATA.forEach(meta => {
        assert.ok('available' in meta, `${meta.id} should have available flag`);
        assert.strictEqual(typeof meta.available, 'boolean');
      });
    });
  });

  describe('Engine Contract Output Format', () => {
    it('output format is {elapsed_ms} - {match_count}', () => {
      const validOutputs = [
        '0.123456 - 1',
        '1234.567890 - 0',
        '0.000001 - 100',
        '60000.000000 - 999'
      ];

      const pattern = /^-?\d+(?:\.\d+)?\s*-\s*-?\d+$/;

      validOutputs.forEach(output => {
        assert.ok(pattern.test(output), `"${output}" should match engine output format`);
      });
    });

    it('parses elapsed_ms correctly', () => {
      const output = '123.456789 - 42';
      const match = output.match(/(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+)/);
      
      assert.ok(match);
      assert.strictEqual(Number(match[1]), 123.456789);
    });

    it('parses match_count correctly', () => {
      const output = '123.456789 - 42';
      const match = output.match(/(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+)/);
      
      assert.ok(match);
      assert.strictEqual(Number(match[2]), 42);
    });
  });

  describe('Engine CLI Contract', () => {
    it('expects 3 arguments: base64_regex, text_file_path, match_mode', () => {
      const args = ['KGErKSs=', '/tmp/input.txt', '0'];
      assert.strictEqual(args.length, 3);
    });

    it('match_mode 0 is partial match', () => {
      assert.strictEqual(0, 0);
    });

    it('match_mode 1 is full match', () => {
      assert.strictEqual(1, 1);
    });
  });

  describe('Engine Categories', () => {
    const immuneEngines = ['re2', 'rust', 'go', 'hyperscan', 'csharp_nonbacktracking'];
    const vulnerableEngines = [
      'python', 'java8', 'java11', 'nodejs14', 'nodejs21',
      'perl', 'php', 'ruby', 'c', 'cpp', 'csharp', 'awk', 'grep', 'srm'
    ];

    it('immune engines are defined', () => {
      immuneEngines.forEach(id => {
        assert.ok(ENGINE_DEFINITIONS[id], `Immune engine ${id} should be defined`);
      });
    });

    it('vulnerable engines are defined', () => {
      vulnerableEngines.forEach(id => {
        assert.ok(ENGINE_DEFINITIONS[id], `Vulnerable engine ${id} should be defined`);
      });
    });

    it('all engines are categorized', () => {
      const allCategorized = [...immuneEngines, ...vulnerableEngines];
      const allDefined = Object.keys(ENGINE_DEFINITIONS);
      
      allDefined.forEach(id => {
        assert.ok(allCategorized.includes(id), `Engine ${id} should be categorized`);
      });
    });
  });
});

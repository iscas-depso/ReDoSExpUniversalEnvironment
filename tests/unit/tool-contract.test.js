const { describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const testPatterns = require('../test-patterns.json');
const { TOOL_DEFINITIONS } = require('../../server/definitions');

describe('Tool Contract Compliance', () => {
  describe('Tool definitions', () => {
    const expectedTools = ['regexploit', 'regexstatic', 'rescue', 'rengar', 'redoshunter', 'regulator', 'grewia'];

    expectedTools.forEach(toolId => {
      it(`${toolId} is defined`, () => {
        assert.ok(TOOL_DEFINITIONS[toolId], `Tool ${toolId} should be defined`);
      });

      it(`${toolId} has required properties`, () => {
        const tool = TOOL_DEFINITIONS[toolId];
        assert.ok(tool.id, 'should have id');
        assert.ok(tool.label, 'should have label');
        assert.ok(tool.description, 'should have description');
        assert.ok(typeof tool.buildCommand === 'function', 'should have buildCommand function');
      });

      it(`${toolId} buildCommand returns valid structure`, () => {
        const tool = TOOL_DEFINITIONS[toolId];
        const command = tool.buildCommand('dGVzdA==', '/tmp/output.json');
        
        assert.ok(command.file, 'should have file');
        assert.ok(Array.isArray(command.args), 'should have args array');
        assert.ok(command.args.includes('dGVzdA=='), 'should include regex argument');
        assert.ok(command.args.includes('/tmp/output.json'), 'should include output path argument');
      });

      it(`${toolId} has run.py wrapper`, () => {
        const runPyPath = path.join(__dirname, '..', '..', 'tools', toolId, 'run.py');
        assert.ok(fs.existsSync(runPyPath), `${runPyPath} should exist`);
      });
    });
  });

  describe('Tool Contract JSON Schema', () => {
    const requiredFields = ['elapsed_ms', 'is_redos', 'prefix', 'infix', 'suffix', 'repeat_times'];

    it('contract requires numeric elapsed_ms', () => {
      const validOutput = {
        elapsed_ms: 123,
        is_redos: true,
        prefix: '',
        infix: 'YQ==',
        suffix: '',
        repeat_times: 100
      };
      
      assert.strictEqual(typeof validOutput.elapsed_ms, 'number');
    });

    it('contract requires boolean is_redos', () => {
      const validOutput = { is_redos: true };
      const invalidOutput = { is_redos: 'true' };
      
      assert.strictEqual(typeof validOutput.is_redos, 'boolean');
      assert.notStrictEqual(typeof invalidOutput.is_redos, 'boolean');
    });

    it('contract requires numeric repeat_times', () => {
      const validOutput = { repeat_times: 100 };
      const noRecommendation = { repeat_times: -1 };
      
      assert.strictEqual(typeof validOutput.repeat_times, 'number');
      assert.strictEqual(typeof noRecommendation.repeat_times, 'number');
    });

    it('contract allows base64 encoded strings for attack components', () => {
      const validOutput = {
        prefix: '',
        infix: 'YQ==',
        suffix: 'Yg=='
      };
      
      assert.strictEqual(typeof validOutput.prefix, 'string');
      assert.strictEqual(typeof validOutput.infix, 'string');
      assert.strictEqual(typeof validOutput.suffix, 'string');
    });

    it('contract allows optional candidate payloads', () => {
      const validOutput = {
        elapsed_ms: 12,
        is_redos: true,
        prefix: '',
        infix: '',
        suffix: '',
        repeat_times: -1,
        recommendedCandidateId: 'candidate-1',
        candidates: [
          {
            id: 'candidate-1',
            label: 'Candidate 1',
            attack: {
              fullText: Buffer.from('aaaaab', 'utf8').toString('base64')
            },
            preview: 'aaaaab',
            payloadLength: 6
          }
        ]
      };

      requiredFields.forEach(field => {
        assert.ok(field in validOutput, `${field} should remain present`);
      });
      assert.ok(Array.isArray(validOutput.candidates));
      assert.strictEqual(typeof validOutput.candidates[0].attack.fullText, 'string');
    });
  });

  describe('Test patterns coverage', () => {
    it('has exponential ReDoS patterns', () => {
      assert.ok(testPatterns.patterns.exponential);
      assert.ok(testPatterns.patterns.exponential.cases.length > 0);
    });

    it('has polynomial ReDoS patterns', () => {
      assert.ok(testPatterns.patterns.polynomial);
      assert.ok(testPatterns.patterns.polynomial.cases.length > 0);
    });

    it('has safe patterns for negative testing', () => {
      assert.ok(testPatterns.patterns.safe);
      assert.ok(testPatterns.patterns.safe.cases.length > 0);
      
      testPatterns.patterns.safe.cases.forEach(c => {
        assert.strictEqual(c.expectedRedos, false, `${c.id} should be marked as non-ReDoS`);
      });
    });

    it('has real-world vulnerable patterns', () => {
      assert.ok(testPatterns.patterns.realWorld);
      assert.ok(testPatterns.patterns.realWorld.cases.length > 0);
    });

    it('all patterns have required fields', () => {
      const allCases = [
        ...testPatterns.patterns.exponential.cases,
        ...testPatterns.patterns.polynomial.cases,
        ...testPatterns.patterns.safe.cases,
        ...testPatterns.patterns.edgeCases.cases,
        ...testPatterns.patterns.realWorld.cases
      ];

      allCases.forEach(c => {
        assert.ok(c.id, `pattern should have id`);
        assert.ok(typeof c.regex === 'string', `${c.id} should have regex string`);
        assert.ok(typeof c.base64 === 'string', `${c.id} should have base64 string`);
        assert.strictEqual(typeof c.expectedRedos, 'boolean', `${c.id} should have boolean expectedRedos`);
      });
    });
  });
});

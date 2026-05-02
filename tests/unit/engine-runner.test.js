const { describe, it } = require('node:test');
const assert = require('node:assert');

const {
  buildAttackPayload,
  parseRunexecMetrics,
  selectEffectiveTime,
  buildEngineExecutionError
} = require('../../server/engine-runner');

describe('engine-runner', () => {
  describe('runexec timing helpers', () => {
    it('extracts runexec walltime, cputime, and memory metrics', () => {
      const metrics = parseRunexecMetrics({
        walltime: '10.238402326591313s',
        cputime: '9.855355s',
        memory: '6676480B'
      });

      assert.strictEqual(metrics.walltimeMs, 10238.402326591313);
      assert.strictEqual(metrics.cputimeMs, 9855.355);
      assert.strictEqual(metrics.memoryBytes, 6676480);
    });

    it('falls back to runexec walltime when engine output is missing', () => {
      const timing = selectEffectiveTime(null, {
        walltime: '10.238402326591313s',
        cputime: '9.855355s',
        memory: '6676480B'
      });

      assert.strictEqual(timing.time, 10238.402326591313);
      assert.strictEqual(timing.timeSource, 'runexec_walltime');
      assert.strictEqual(timing.cputimeMs, 9855.355);
      assert.strictEqual(timing.memoryBytes, 6676480);
    });

    it('handles null runexec metadata without throwing', () => {
      const timing = selectEffectiveTime({ elapsedMs: 12.5 }, null);

      assert.strictEqual(timing.time, 12.5);
      assert.strictEqual(timing.timeSource, 'engine');
      assert.strictEqual(timing.walltimeMs, null);
      assert.strictEqual(timing.cputimeMs, null);
      assert.strictEqual(timing.memoryBytes, null);
    });

    it('marks fatal exception output as tool_exception', () => {
      const error = buildEngineExecutionError('fatal', {
        stdout: 'Exception in thread "main" java.lang.StackOverflowError',
        stderr: '',
        parsedOutput: null,
        runexecParsed: { returnValue: 0, terminationReason: null }
      });

      assert.strictEqual(error.type, 'tool_exception');
    });
  });

  describe('buildAttackPayload', () => {
    it('builds payload from base64 encoded components', () => {
      const attack = {
        prefix: Buffer.from('pre').toString('base64'),
        infix: Buffer.from('a').toString('base64'),
        suffix: Buffer.from('suf').toString('base64'),
        repeat_times: 3
      };
      
      const { attackText, payloadInfo } = buildAttackPayload(attack, {});
      
      assert.strictEqual(attackText, 'preaaasuf');
      assert.strictEqual(payloadInfo.prefixLength, 3);
      assert.strictEqual(payloadInfo.infixLength, 1);
      assert.strictEqual(payloadInfo.suffixLength, 3);
      assert.strictEqual(payloadInfo.appliedRepeat, 3);
    });

    it('handles empty components', () => {
      const attack = {
        prefix: '',
        infix: Buffer.from('x').toString('base64'),
        suffix: '',
        repeat_times: 5
      };
      
      const { attackText } = buildAttackPayload(attack, {});
      
      assert.strictEqual(attackText, 'xxxxx');
    });

    it('respects repeatOverride option', () => {
      const attack = {
        prefix: '',
        infix: Buffer.from('a').toString('base64'),
        suffix: '',
        repeat_times: 100
      };
      
      const { attackText, payloadInfo } = buildAttackPayload(attack, { repeatOverride: 3 });
      
      assert.strictEqual(attackText, 'aaa');
      assert.strictEqual(payloadInfo.appliedRepeat, 3);
    });

    it('truncates payload exceeding maxAttackLength', () => {
      const attack = {
        prefix: '',
        infix: Buffer.from('ab').toString('base64'),
        suffix: '',
        repeat_times: 1000
      };
      
      const { attackText, payloadInfo } = buildAttackPayload(attack, { maxAttackLength: 100 });
      
      assert.ok(attackText.length <= 100);
      assert.strictEqual(payloadInfo.truncated, true);
    });

    it('respects maxRepeatTimes limit', () => {
      const attack = {
        prefix: '',
        infix: Buffer.from('a').toString('base64'),
        suffix: '',
        repeat_times: 100000
      };
      
      const { payloadInfo } = buildAttackPayload(attack, { maxRepeatTimes: 100 });
      
      assert.ok(payloadInfo.appliedRepeat <= 100);
    });

    it('handles missing attack components gracefully', () => {
      const attack = {};
      
      const { attackText } = buildAttackPayload(attack, {});
      
      assert.strictEqual(attackText, '');
    });

    it('handles invalid base64 gracefully', () => {
      const attack = {
        prefix: 'not-valid-base64!!!',
        infix: Buffer.from('a').toString('base64'),
        suffix: ''
      };
      
      const { attackText } = buildAttackPayload(attack, {});
      
      assert.ok(typeof attackText === 'string');
    });

    it('supports different repeat_times key formats', () => {
      const attack1 = {
        infix: Buffer.from('a').toString('base64'),
        repeat_times: 5
      };
      const attack2 = {
        infix: Buffer.from('a').toString('base64'),
        repeatTimes: 5
      };
      const attack3 = {
        infix: Buffer.from('a').toString('base64'),
        repeat: 5
      };
      
      const r1 = buildAttackPayload(attack1, {});
      const r2 = buildAttackPayload(attack2, {});
      const r3 = buildAttackPayload(attack3, {});
      
      assert.strictEqual(r1.payloadInfo.appliedRepeat, 5);
      assert.strictEqual(r2.payloadInfo.appliedRepeat, 5);
      assert.strictEqual(r3.payloadInfo.appliedRepeat, 5);
    });

    it('passes through fullText payloads without pattern expansion', () => {
      const attack = {
        fullText: Buffer.from('aaaaab', 'utf8').toString('base64')
      };

      const { attackText, payloadInfo } = buildAttackPayload(attack, { repeatOverride: 99 });

      assert.strictEqual(attackText, 'aaaaab');
      assert.strictEqual(payloadInfo.mode, 'fullText');
      assert.strictEqual(payloadInfo.payloadLength, 6);
    });
  });
});

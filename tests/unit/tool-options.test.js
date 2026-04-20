const { describe, it } = require('node:test');
const assert = require('node:assert');

const { normalizeToolOptions } = require('../../server/definitions');

describe('Tool options normalization', () => {
  it('returns empty options for tools without custom config', () => {
    assert.deepStrictEqual(normalizeToolOptions('regexploit', undefined), {});
  });

  it('returns GREWIA defaults when no options are provided', () => {
    const normalized = normalizeToolOptions('grewia', undefined);

    assert.deepStrictEqual(normalized, {
      regexEngine: 'Java',
      matchMode: 0,
      attackStringLength: 100000,
      candidateMode: 'single',
      decremental: false
    });
  });

  it('normalizes valid GREWIA options', () => {
    const normalized = normalizeToolOptions('grewia', {
      regexEngine: 'Python',
      matchMode: 1,
      attackStringLength: 4096,
      candidateMode: 'multiple',
      decremental: 'true'
    });

    assert.deepStrictEqual(normalized, {
      regexEngine: 'Python',
      matchMode: 1,
      attackStringLength: 4096,
      candidateMode: 'multiple',
      decremental: true
    });
  });

  it('rejects invalid GREWIA options', () => {
    assert.throws(
      () => normalizeToolOptions('grewia', { regexEngine: 'PCRE2' }),
      /regexEngine/
    );
    assert.throws(
      () => normalizeToolOptions('grewia', { candidateMode: 'all' }),
      /candidateMode/
    );
  });
});

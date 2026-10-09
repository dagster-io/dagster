import {lintRunsSearch} from '../lintRunsSearch';

describe('lintRunsSearch', () => {
  it('accepts a valid search', () => {
    expect(lintRunsSearch('job:my_job and (status:failure or status:canceled)')).toEqual([]);
  });

  it('reports unknown attributes with the shared message', () => {
    expect(lintRunsSearch('foo:bar')).toEqual([
      {message: 'Unsupported attribute: "foo"', from: 0, to: 3},
    ]);
  });

  it('accepts blank text, which clears the search', () => {
    expect(lintRunsSearch('   ')).toEqual([]);
  });

  it('accepts leading whitespace and points errors past it', () => {
    expect(lintRunsSearch(' \tjob:a')).toEqual([]);
    // An incomplete-quote token would otherwise absorb the leading spaces.
    expect(lintRunsSearch('  "foo"')).toEqual([
      {message: 'Add an attribute, for example job:my_job', from: 2, to: 7},
    ]);
    expect(lintRunsSearch('  job:a job:b')).toEqual([
      {
        message: "mismatched input 'job' expecting <EOF>",
        offendingSymbol: 'job',
        from: 8,
        to: Infinity,
      },
    ]);
  });

  it('reports a syntax error for an unquoted value with special characters', () => {
    expect(lintRunsSearch('id:abc-123')).not.toEqual([]);
  });

  it('reports runs search rules once the syntax is valid', () => {
    expect(lintRunsSearch('id:a or job:b')).toEqual([
      {message: 'or only combines IDs or statuses', from: 0, to: 13},
    ]);
  });

  it('keeps syntax errors for other malformed searches', () => {
    expect(lintRunsSearch('job:a job:b')).not.toEqual([]);
  });

  it('reports an unknown attribute after an emoji at its position in the text', () => {
    expect(lintRunsSearch('tag:"😀"=x and foo:a')).toEqual([
      {message: 'Unsupported attribute: "foo"', from: 15, to: 18},
    ]);
  });

  it('reports an unknown attribute once when a syntax error covers its later uses', () => {
    expect(lintRunsSearch('key:a key:b')).toEqual([
      {
        message: "mismatched input 'key' expecting <EOF>",
        offendingSymbol: 'key',
        from: 6,
        to: Infinity,
      },
      {message: 'Unsupported attribute: "key"', from: 0, to: 3},
    ]);
  });

  it('places later terms after characters the lexer drops', () => {
    expect(lintRunsSearch('job:a \\\\ x:b')).toEqual([
      {
        message: "mismatched input 'x' expecting <EOF>",
        offendingSymbol: 'x',
        from: 9,
        to: Infinity,
      },
    ]);
  });
});

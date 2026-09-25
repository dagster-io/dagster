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
});

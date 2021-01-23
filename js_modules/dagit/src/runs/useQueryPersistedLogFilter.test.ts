import {
  DefaultQuerystring,
  decodeRunPageFilters,
  encodeRunPageFilters,
} from 'src/runs/useQueryPersistedLogFilter';

describe('encodeRunPageFilters', () => {
  it('serializes log levels, ', () => {
    expect(
      encodeRunPageFilters({
        hideNonMatches: true,
        focusedTime: 1611430148147,
        logQuery: [
          {token: 'step', value: 'bar'},
          {token: 'query', value: 'foo*'},
        ],
        levels: {ERROR: true, CRITICAL: true},
        sinceTime: 0,
      }),
    ).toEqual({
      focusedTime: 1611430148147,
      hideNonMatches: 'true',
      levels: 'critical|error',
      logs: 'step:bar|query:foo*',
    });
  });
});

describe('decodeRunPageFilters', () => {
  describe('`logs` extraction', () => {
    it('extracts a `step` from params', () => {
      const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'step:foo'});
      expect(logQuery).toMatchObject([{token: 'step', value: 'foo'}]);
    });

    it('extracts a `type` from params', () => {
      const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'type:bar'});
      expect(logQuery).toMatchObject([{token: 'type', value: 'bar'}]);
    });

    describe('`query` extraction', () => {
      it('extracts a single `steps` value from params', () => {
        const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'query:foo'});
        expect(logQuery).toMatchObject([{token: 'query', value: 'foo'}]);
      });

      it('extracts a complex `steps` from params', () => {
        const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'query:++foo++'});
        expect(logQuery).toMatchObject([{token: 'query', value: '++foo++'}]);
      });

      it('extracts a `steps` list from params', () => {
        const {logQuery} = decodeRunPageFilters({
          ...DefaultQuerystring,
          logs: 'query:foo, bar, baz',
        });
        expect(logQuery).toMatchObject([{token: 'query', value: 'foo, bar, baz'}]);
      });
    });

    describe('multiple extractions', () => {
      it('extracts `query` and `step`', () => {
        const {logQuery} = decodeRunPageFilters({
          ...DefaultQuerystring,
          logs: 'query:bar++|step:foo',
        });
        expect(logQuery).toMatchObject([
          {token: 'query', value: 'bar++'},
          {token: 'step', value: 'foo'},
        ]);
      });

      it('extracts `query` with commas, and `step`', () => {
        const {logQuery} = decodeRunPageFilters({
          ...DefaultQuerystring,
          logs: 'query:bar1,bar2|step:foo',
        });
        expect(logQuery).toMatchObject([
          {token: 'query', value: 'bar1,bar2'},
          {token: 'step', value: 'foo'},
        ]);
      });

      it('extracts `query` with commas, and free text', () => {
        const {logQuery} = decodeRunPageFilters({
          ...DefaultQuerystring,
          logs: 'query:bar1,bar2|foo',
        });
        expect(logQuery).toMatchObject([{token: 'query', value: 'bar1,bar2'}, {value: 'foo'}]);
      });

      it('extracts `query` and `levels`', () => {
        const {levels, logQuery} = decodeRunPageFilters({
          ...DefaultQuerystring,
          logs: 'query:bar1,bar2',
          levels: 'error|warning',
        });
        expect(logQuery).toMatchObject([{token: 'query', value: 'bar1,bar2'}]);
        expect(levels).toMatchObject({ERROR: true, WARNING: true});
      });
    });
  });

  describe('`levels` extraction', () => {
    it('extracts `levels` from params', () => {
      const {levels} = decodeRunPageFilters({...DefaultQuerystring, levels: 'error'});
      expect(levels).toMatchObject({ERROR: true});
    });

    it('extracts multiple `levels` from params', () => {
      const {levels} = decodeRunPageFilters({...DefaultQuerystring, levels: 'error|warning'});
      expect(levels).toMatchObject({ERROR: true, WARNING: true});
    });

    it('ignores invalid `levels`', () => {
      const {levels} = decodeRunPageFilters({...DefaultQuerystring, levels: 'error|foo'});
      expect(levels).toMatchObject({ERROR: true});
    });

    it('sets default levels if none specified', () => {
      const {levels} = decodeRunPageFilters({...DefaultQuerystring, query: 'type:foo'});
      expect(levels).toMatchObject({
        INFO: true,
        WARNING: true,
        ERROR: true,
        CRITICAL: true,
        EVENT: true,
      });
    });
  });

  describe('free text `logs` extraction', () => {
    it('extracts free text from params', () => {
      const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'foobarbaz'});
      expect(logQuery).toMatchObject([{value: 'foobarbaz'}]);
    });

    it('treats unknown tokens as free text', () => {
      const {logQuery} = decodeRunPageFilters({...DefaultQuerystring, logs: 'foo:barbaz'});
      expect(logQuery).toMatchObject([{value: 'foo:barbaz'}]);
    });
  });
});

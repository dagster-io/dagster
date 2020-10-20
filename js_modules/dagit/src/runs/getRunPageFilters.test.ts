import {getRunPageFilters} from 'src/runs/getRunPageFilters';

describe('getRunPageFilters', () => {
  describe('`steps` extraction', () => {
    it('extracts a single `steps` value from params', () => {
      const query = 'steps=foo';
      const {stepQuery} = getRunPageFilters(query);
      expect(stepQuery).toBe('foo');
    });

    it('extracts a complex `steps` from params', () => {
      const query = `steps=${encodeURIComponent('++foo++')}`;
      const {stepQuery} = getRunPageFilters(query);
      expect(stepQuery).toBe('++foo++');
    });

    it('extracts a `steps` list from params', () => {
      const query = `steps=${encodeURIComponent('foo, bar, baz')}`;
      const {stepQuery} = getRunPageFilters(query);
      expect(stepQuery).toBe('foo, bar, baz');
    });
  });

  describe('`logs` extraction', () => {
    it('extracts a `step` from params', () => {
      const query = 'logs=step:foo';
      const {logQuery} = getRunPageFilters(query);
      expect(logQuery).toMatchObject([{token: 'step', value: 'foo'}]);
    });

    it('extracts a `type` from params', () => {
      const query = 'logs=type:bar';
      const {logQuery} = getRunPageFilters(query);
      expect(logQuery).toMatchObject([{token: 'type', value: 'bar'}]);
    });

    describe('`query` extraction', () => {
      it('extracts a single `steps` value from params', () => {
        const query = 'logs=query:foo';
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([{token: 'query', value: 'foo'}]);
      });

      it('extracts a complex `steps` from params', () => {
        const query = `logs=${encodeURIComponent('query:++foo++')}`;
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([{token: 'query', value: '++foo++'}]);
      });

      it('extracts a `steps` list from params', () => {
        const query = `logs=${encodeURIComponent('query:foo, bar, baz')}`;
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([{token: 'query', value: 'foo, bar, baz'}]);
      });
    });

    describe('multiple extractions', () => {
      it('extracts `query` and `step`', () => {
        const query = `logs=${encodeURIComponent('query:bar++')}&logs=step:foo`;
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([
          {token: 'query', value: 'bar++'},
          {token: 'step', value: 'foo'},
        ]);
      });

      it('extracts `query` with commas, and `step`', () => {
        const query = `logs=${encodeURIComponent('query:bar1,bar2')}&logs=step:foo`;
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([
          {token: 'query', value: 'bar1,bar2'},
          {token: 'step', value: 'foo'},
        ]);
      });

      it('extracts `query` with commas, and free text', () => {
        const query = `logs=${encodeURIComponent('query:bar1,bar2')}&logs=foo`;
        const {logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([{token: 'query', value: 'bar1,bar2'}, {value: 'foo'}]);
      });

      it('extracts `query` and `levels`', () => {
        const query = `logs=${encodeURIComponent('query:bar1,bar2')}&levels=error&levels=warning`;
        const {levels, logQuery} = getRunPageFilters(query);
        expect(logQuery).toMatchObject([{token: 'query', value: 'bar1,bar2'}]);
        expect(levels).toMatchObject({ERROR: true, WARNING: true});
      });
    });
  });

  describe('`levels` extraction', () => {
    it('extracts `levels` from params', () => {
      const query = 'levels=error';
      const {levels} = getRunPageFilters(query);
      expect(levels).toMatchObject({ERROR: true});
    });

    it('extracts multiple `levels` from params', () => {
      const query = 'levels=error&levels=warning';
      const {levels} = getRunPageFilters(query);
      expect(levels).toMatchObject({ERROR: true, WARNING: true});
    });

    it('ignores invalid `levels`', () => {
      const query = 'levels=error&levels=foo';
      const {levels} = getRunPageFilters(query);
      expect(levels).toMatchObject({ERROR: true});
    });

    it('sets default levels if none specified', () => {
      const query = 'query=type:foo';
      const {levels} = getRunPageFilters(query);
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
      const query = 'logs=foobarbaz';
      const {logQuery} = getRunPageFilters(query);
      expect(logQuery).toMatchObject([{value: 'foobarbaz'}]);
    });

    it('treats unknown tokens as free text', () => {
      const query = 'logs=foo:barbaz';
      const {logQuery} = getRunPageFilters(query);
      expect(logQuery).toMatchObject([{value: 'foo:barbaz'}]);
    });
  });
});

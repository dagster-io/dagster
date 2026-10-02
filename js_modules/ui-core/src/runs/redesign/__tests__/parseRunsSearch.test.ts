import {tokensAsStringArray} from '@dagster-io/ui-components';

import {parseRunsSearch} from '../parseRunsSearch';

const getTokenStrings = (text: string) => {
  const {tokens} = parseRunsSearch(text);
  return tokens ? tokensAsStringArray(tokens) : null;
};

const getFirstError = (text: string) => parseRunsSearch(text).errors[0];

describe('parseRunsSearch', () => {
  it.each([
    {text: '', tokens: []},
    {text: '   ', tokens: []},
    {text: 'id:abc123', tokens: ['id:abc123']},
    {
      text: 'id:"8d3e6c1a-4f2b-4c3d-9e8f-0a1b2c3d4e5f"',
      tokens: ['id:8d3e6c1a-4f2b-4c3d-9e8f-0a1b2c3d4e5f'],
    },
    {text: 'status:failure', tokens: ['status:FAILURE']},
    {text: 'job:my_job', tokens: ['job:my_job']},
    {text: 'snapshot_id:abc', tokens: ['snapshotId:abc']},
    {text: 'created_after:1700000000', tokens: ['created_date_after:1700000000']},
    {text: 'created_before:"1700000000.25"', tokens: ['created_date_before:1700000000.25']},
    {
      text: 'code_location:"repo@location"',
      tokens: ['tag:.dagster/repository=repo@location'],
    },
    {text: 'sensor:my_sensor', tokens: ['tag:dagster/sensor_name=my_sensor']},
    {text: 'schedule:daily', tokens: ['tag:dagster/schedule_name=daily']},
    {text: 'user:"a@b.com"', tokens: ['tag:user=a@b.com']},
    {text: 'backfill:abcdef', tokens: ['tag:dagster/backfill=abcdef']},
    {text: 'partition:"2024-01-01"', tokens: ['tag:dagster/partition=2024-01-01']},
    {text: 'tag:team=data', tokens: ['tag:team=data']},
    {text: 'tag:"dagster/auto_materialize"=true', tokens: ['tag:dagster/auto_materialize=true']},
    {text: 'job:"and"', tokens: ['job:and']},
    {text: 'job:"a*"', tokens: ['job:a*']},
    {text: 'id:a or id:b', tokens: ['id:a', 'id:b']},
    {text: 'id:a, id:b', tokens: ['id:a', 'id:b']},
    {text: '(status:failure or status:canceled)', tokens: ['status:FAILURE', 'status:CANCELED']},
    {text: '(id:a or id:b) or id:c', tokens: ['id:a', 'id:b', 'id:c']},
    {text: 'id:a and id:a', tokens: ['id:a']},
    {text: 'sensor:s and tag:dagster/sensor_name=s', tokens: ['tag:dagster/sensor_name=s']},
    {
      text: 'tag:team=data and job:my_job and (status:failure or status:canceled) and id:a',
      tokens: ['id:a', 'status:FAILURE', 'status:CANCELED', 'job:my_job', 'tag:team=data'],
    },
  ])('parses $text', ({text, tokens}) => {
    expect(getTokenStrings(text)).toEqual(tokens);
  });

  it.each([
    {
      text: 'job:a job:b',
      message: 'Check the search syntax, for example job:my_job and status:failure',
    },
    {text: 'my_job', message: 'Add an attribute, for example job:my_job'},
    {text: 'foo:bar', message: 'Unsupported attribute: "foo"'},
    {text: 'not job:a', message: "not isn't supported in runs search"},
    {text: 'not', message: "not isn't supported in runs search"},
    {text: 'id:', message: 'Add a value after id:'},
    {text: 'job:""', message: 'Add a value after job:'},
    {text: 'tag:', message: 'tag needs key=value, for example tag:team=data'},
    {text: 'tag:team', message: 'tag needs key=value, for example tag:team=data'},
    {text: 'tag:team=', message: 'tag needs key=value, for example tag:team=data'},
    {text: 'tag:team="a=b"', message: "Tag keys and values can't contain ="},
    {text: 'user:"a=b"', message: "user values can't contain ="},
    {text: 'job:a=b', message: 'Only tag takes key=value, for example tag:team=data'},
    {text: 'job:a and', message: 'Add a search term after and'},
    {text: 'id:a or', message: 'Add a search term after or'},
    {text: '(id:a', message: 'Finish the search before applying it'},
    {text: 'id:a,', message: 'Finish the search before applying it'},
    {text: 'id:"abc', message: 'Close the quote around this value'},
    {text: '+job:a', message: "Traversal (+) isn't supported in runs search"},
    {text: 'sinks(job:a)', message: "Functions aren't supported in runs search"},
    {text: 'job:<null>', message: "<null> isn't supported in runs search"},
    {text: 'job:*a*', message: "Wildcards (*) aren't supported in runs search"},
    {text: '*', message: "Wildcards (*) aren't supported in runs search"},
    {text: 'status:bogus', message: 'Unknown status: bogus'},
    {text: 'created_after:soon', message: 'created_after needs a Unix timestamp in seconds'},
    {text: 'id:a and id:b', message: 'Use or to match any of several IDs'},
    {text: '(id:a or id:b) and (id:a or id:c)', message: 'Use or to match any of several IDs'},
    {text: 'job:a and job:b', message: 'Only one job per search'},
    {text: 'job:a or job:b', message: 'Only one job per search'},
    {text: 'sensor:a and tag:dagster/sensor_name=b', message: 'Only one sensor per search'},
    {text: 'tag:team=a and tag:team=b', message: 'Only one value per tag key'},
    {text: 'id:a or status:failure', message: 'or only combines IDs or statuses'},
    {text: '(id:a and job:b) or id:c', message: 'or only combines IDs or statuses'},
  ])('rejects $text', ({text, message}) => {
    expect(parseRunsSearch(text)).toEqual({
      tokens: null,
      errors: expect.arrayContaining([expect.objectContaining({message})]),
    });
  });

  it.each(['id:abc-123', 'user:a@b.com', 'tag:team=a-b'])(
    'rejects the unquoted special characters in %s',
    (text) => {
      expect(parseRunsSearch(text)).toEqual({
        tokens: null,
        errors: [
          {
            message: 'Check the search syntax, for example job:my_job and status:failure',
            from: 0,
            to: text.length,
          },
        ],
      });
    },
  );

  it('points errors at the offending term', () => {
    expect(getFirstError('job:a and job:b')).toEqual({
      message: 'Only one job per search',
      from: 10,
      to: 15,
    });
    expect(getFirstError('job:a and foo:bar and id:x')).toEqual({
      message: 'Unsupported attribute: "foo"',
      from: 10,
      to: 17,
    });
  });
});

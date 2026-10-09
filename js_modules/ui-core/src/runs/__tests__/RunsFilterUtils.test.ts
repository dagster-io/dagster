import {RunStatus} from '../../graphql/types';
import {DagsterTag} from '../RunTag';
import {runsFilterForCodeLocation} from '../RunsFilterUtils';

describe('runsFilterForCodeLocation', () => {
  it('returns the filter unchanged when no code location is selected', () => {
    const filter = {statuses: [RunStatus.FAILURE]};
    expect(runsFilterForCodeLocation(filter, null)).toBe(filter);
  });

  it('adds the code location tag to a filter without tags', () => {
    expect(runsFilterForCodeLocation({statuses: [RunStatus.FAILURE]}, 'my_location')).toEqual({
      statuses: [RunStatus.FAILURE],
      tags: [{key: DagsterTag.CodeLocation, value: 'my_location'}],
    });
  });

  it('keeps existing tags', () => {
    expect(runsFilterForCodeLocation({tags: [{key: 'team', value: 'data'}]}, 'loc')).toEqual({
      tags: [
        {key: 'team', value: 'data'},
        {key: DagsterTag.CodeLocation, value: 'loc'},
      ],
    });
  });
});

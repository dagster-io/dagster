import {RunStatus, buildMaterializationEvent, buildRun} from '../../graphql/types';
import {shouldDisplayRunFailure} from '../Utils';

describe('shouldDisplayRunFailure', () => {
  it('should return false if the latest materialization is from the latest run', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '1', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300346000`}),
      ),
    ).toEqual(false);
  });
  it('should return false if the latest materialization is newer than the failure (manually reported event case)', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '1', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: undefined, timestamp: `1674400000000`}),
      ),
    ).toEqual(false);
  });
  it('should return false if the run succeeded', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '2', status: RunStatus.SUCCESS, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300346000`}),
      ),
    ).toEqual(false);
  });
  it('should return true if the latest run status is failed and other conditions are not met', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '2', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300000000`}),
      ),
    ).toEqual(true);
  });
});

import {labelForRequestedMaterializationsAndJobRuns} from '../InstigationUtils';

describe('labelForRequestedMaterializationsAndJobRuns', () => {
  it('shows only materializations when no job runs were requested', () => {
    expect(labelForRequestedMaterializationsAndJobRuns(0, 0)).toBe('0 materializations requested');
    expect(labelForRequestedMaterializationsAndJobRuns(1, 0)).toBe('1 materialization requested');
    expect(labelForRequestedMaterializationsAndJobRuns(4, 0)).toBe('4 materializations requested');
  });

  it('shows only job runs when no materializations were requested', () => {
    expect(labelForRequestedMaterializationsAndJobRuns(0, 1)).toBe('1 job run requested');
    expect(labelForRequestedMaterializationsAndJobRuns(0, 3)).toBe('3 job runs requested');
  });

  it('shows both when a tick requested materializations and job runs', () => {
    expect(labelForRequestedMaterializationsAndJobRuns(2, 1)).toBe(
      '2 materializations, 1 job run requested',
    );
    expect(labelForRequestedMaterializationsAndJobRuns(1, 2)).toBe(
      '1 materialization, 2 job runs requested',
    );
  });
});

import {buildAutoMaterializeAssetEvaluationRecord} from '../../../graphql/types';
import {getEvaluationsWithEmptyAdded} from '../getEvaluationsWithEmptyAdded';
import {AutoMaterializeEvaluationRecordItemFragment} from '../types/GetEvaluationsQuery.types';

describe('getEvaluationsWithEmptyAdded', () => {
  it('should return an empty array if isLoading is true', () => {
    const evaluations = [
      buildAutoMaterializeAssetEvaluationRecord({
        id: '3',
        evaluationId: 3,
        numRequested: 1,
        numSkipped: 0,
        numDiscarded: 0,
        timestamp: Date.now() / 1000 - 60 * 5,
        rulesWithRuleEvaluations: [],
      }),
      buildAutoMaterializeAssetEvaluationRecord({
        id: '2',
        evaluationId: 2,
        numRequested: 1,
        numSkipped: 0,
        numDiscarded: 0,
        timestamp: Date.now() / 1000 - 60 * 4,
        rulesWithRuleEvaluations: [],
      }),
    ];

    const actual = getEvaluationsWithEmptyAdded({
      evaluations,
      currentEvaluationId: 3,
      isFirstPage: false,
      isLastPage: false,
      isLoading: true,
    });

    expect(actual).toEqual([]);
  });

  it('should return "no conditions met" before NOW if no evaluations yet', () => {
    const evaluations: AutoMaterializeEvaluationRecordItemFragment[] = [];

    const actual = getEvaluationsWithEmptyAdded({
      evaluations,
      currentEvaluationId: null,
      isFirstPage: true,
      isLastPage: true,
      isLoading: false,
    });

    expect(actual).toEqual([
      {
        __typename: 'no_conditions_met',
        evaluationId: 1,
        amount: 1,
        startTimestamp: 0,
        endTimestamp: 'now',
      },
    ]);
  });

  it('should return "no conditions met" before [time] if no evaluations yet', () => {
    const evaluations: AutoMaterializeEvaluationRecordItemFragment[] = [];

    const actual = getEvaluationsWithEmptyAdded({
      evaluations,
      currentEvaluationId: null,
      isFirstPage: true,
      isLastPage: true,
      isLoading: false,
    });

    expect(actual).toEqual([
      {
        __typename: 'no_conditions_met',
        evaluationId: 1,
        amount: 1,
        startTimestamp: 0,
        endTimestamp: 'now',
      },
    ]);
  });

  it(
    'should return a skipped entry on top if its the first page and the currentEvaluationId is greater' +
      "than the last evaluation's ID + at the bottom if its the last page and the last evaluation ID is not 1",
    () => {
      const evaluations = [
        buildAutoMaterializeAssetEvaluationRecord({
          id: '3',
          evaluationId: 3,
          numRequested: 1,
          numSkipped: 0,
          numDiscarded: 0,
          timestamp: Date.now() / 1000 - 60 * 4,
          rulesWithRuleEvaluations: [],
        }),
        buildAutoMaterializeAssetEvaluationRecord({
          id: '2',
          evaluationId: 2,
          numRequested: 1,
          numSkipped: 0,
          numDiscarded: 0,
          timestamp: Date.now() / 1000 - 60 * 5,
          rulesWithRuleEvaluations: [],
        }),
      ];

      const actual = getEvaluationsWithEmptyAdded({
        evaluations,
        currentEvaluationId: 10,
        isFirstPage: true,
        isLastPage: true,
        isLoading: false,
      });

      expect(actual).toEqual([
        {
          __typename: 'no_conditions_met',
          evaluationId: 10,
          amount: 7,
          startTimestamp: evaluations[0]!.timestamp + 60,
          endTimestamp: 'now',
        },
        ...evaluations,
        {
          __typename: 'no_conditions_met',
          evaluationId: 1,
          amount: 1,
          endTimestamp: evaluations[1]!.timestamp - 60,
          startTimestamp: 0,
        },
      ]);
    },
  );

  it('should return a skipped entry in between if records skip an evaluation ID', () => {
    const evaluations = [
      buildAutoMaterializeAssetEvaluationRecord({
        id: '3',
        evaluationId: 3,
        numRequested: 1,
        numSkipped: 0,
        numDiscarded: 0,
        timestamp: Date.now() / 1000 - 60 * 4,
        rulesWithRuleEvaluations: [],
      }),
      buildAutoMaterializeAssetEvaluationRecord({
        id: '1',
        evaluationId: 1,
        numRequested: 1,
        numSkipped: 0,
        numDiscarded: 0,
        timestamp: Date.now() / 1000 - 60 * 5,
        rulesWithRuleEvaluations: [],
      }),
    ];

    const actual = getEvaluationsWithEmptyAdded({
      evaluations,
      currentEvaluationId: 3,
      isFirstPage: true,
      isLastPage: true,
      isLoading: false,
    });

    expect(actual).toEqual([
      evaluations[0],
      {
        __typename: 'no_conditions_met',
        evaluationId: 2,
        amount: 1,
        endTimestamp: evaluations[0]!.timestamp - 60,
        startTimestamp: evaluations[1]!.timestamp + 60,
      },
      evaluations[1],
      {
        __typename: 'no_conditions_met',
        evaluationId: 0,
        amount: 0,
        endTimestamp: evaluations[1]!.timestamp - 60,
        startTimestamp: 0,
      },
    ]);
  });
});

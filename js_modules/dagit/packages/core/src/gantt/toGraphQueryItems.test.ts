import {IStepMetadata, IStepState} from '../runs/RunMetadataProvider';
import {StepKind} from '../types/globalTypes';

import {toGraphQueryItems} from './toGraphQueryItems';

const STATE_SUCCESS: IStepMetadata = {
  state: IStepState.SUCCEEDED,
  attempts: [],
  markers: [],
  transitions: [],
};

describe('toGraphQueryItems', () => {
  it('basic conversion', () => {
    expect(
      toGraphQueryItems(
        {
          __typename: 'ExecutionPlan',
          steps: [
            {
              __typename: 'ExecutionStep',
              key: 'a',
              kind: StepKind.COMPUTE,
              inputs: [],
            },
            {
              __typename: 'ExecutionStep',
              key: 'b[?]',
              kind: StepKind.UNRESOLVED_MAPPED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'a',
                      kind: StepKind.COMPUTE,
                    },
                  ],
                },
              ],
            },
          ],
        },
        {a: STATE_SUCCESS, 'b[1]': STATE_SUCCESS},
      ),
    ).toEqual([
      {
        inputs: [],
        name: 'a',
        outputs: [{dependedBy: [{solid: {name: 'b[1]'}}, {solid: {name: 'b[?]'}}]}],
      },
      {inputs: [{dependsOn: [{solid: {name: 'a'}}]}], name: 'b[1]', outputs: []},
      {inputs: [{dependsOn: [{solid: {name: 'a'}}]}], name: 'b[?]', outputs: []},
    ]);
  });

  it('mirrors sub-graphs of planned dynamic steps for each runtime key', () => {
    expect(
      toGraphQueryItems(
        {
          __typename: 'ExecutionPlan',
          steps: [
            {
              __typename: 'ExecutionStep',
              key: 'a',
              kind: StepKind.COMPUTE,
              inputs: [],
            },
            {
              __typename: 'ExecutionStep',
              key: 'b[?]',
              kind: StepKind.UNRESOLVED_MAPPED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'a',
                      kind: StepKind.COMPUTE,
                    },
                  ],
                },
              ],
            },
            {
              __typename: 'ExecutionStep',
              key: 'c[?]',
              kind: StepKind.UNRESOLVED_MAPPED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'b[?]',
                      kind: StepKind.UNRESOLVED_MAPPED,
                    },
                  ],
                },
              ],
            },
          ],
        },
        {a: STATE_SUCCESS, 'b[1]': STATE_SUCCESS, 'b[2]': STATE_SUCCESS, 'c[1]': STATE_SUCCESS},
      ),
    ).toEqual([
      {
        inputs: [],
        name: 'a',
        outputs: [
          {
            dependedBy: [
              {
                solid: {
                  name: 'b[1]',
                },
              },
              {
                solid: {
                  name: 'b[2]',
                },
              },
              {
                solid: {
                  name: 'b[?]',
                },
              },
            ],
          },
        ],
      },
      {
        inputs: [
          {
            dependsOn: [
              {
                solid: {
                  name: 'a',
                },
              },
            ],
          },
        ],
        name: 'b[1]',
        outputs: [
          {
            dependedBy: [
              {
                solid: {
                  name: 'c[1]',
                },
              },
            ],
          },
        ],
      },
      {
        inputs: [
          {
            dependsOn: [
              {
                solid: {
                  name: 'a',
                },
              },
            ],
          },
        ],
        name: 'b[2]',
        outputs: [],
      },
      {
        inputs: [
          {
            dependsOn: [
              {
                solid: {
                  name: 'a',
                },
              },
            ],
          },
        ],
        name: 'b[?]',
        outputs: [
          {
            dependedBy: [
              {
                solid: {
                  name: 'c[?]',
                },
              },
            ],
          },
        ],
      },
      {
        inputs: [
          {
            dependsOn: [
              {
                solid: {
                  name: 'b[1]',
                },
              },
            ],
          },
        ],
        name: 'c[1]',
        outputs: [],
      },
      {
        inputs: [
          {
            dependsOn: [
              {
                solid: {
                  name: 'b[?]',
                },
              },
            ],
          },
        ],
        name: 'c[?]',
        outputs: [],
      },
    ]);
  });
});

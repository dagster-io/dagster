import {toGraphQueryItems} from 'src/gantt/toGraphQueryItems';
import {StepKind} from 'src/types/globalTypes';

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
              key: 'b',
              kind: StepKind.UNRESOLVED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'a',
                      kind: StepKind.COMPUTE,
                      outputs: [
                        {
                          __typename: 'ExecutionStepOutput',
                          name: 'result',
                          type: {
                            __typename: 'RegularDagsterType',
                            name: 'Any',
                          },
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
          artifactsPersisted: false,
        },
        ['a', 'b'],
      ),
    ).toEqual([
      {inputs: [], name: 'a', outputs: [{dependedBy: [{solid: {name: 'b'}}]}]},
      {inputs: [{dependsOn: [{solid: {name: 'a'}}]}], name: 'b', outputs: []},
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
              kind: StepKind.UNRESOLVED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'a',
                      kind: StepKind.COMPUTE,
                      outputs: [
                        {
                          __typename: 'ExecutionStepOutput',
                          name: 'result',
                          type: {
                            __typename: 'RegularDagsterType',
                            name: 'Any',
                          },
                        },
                      ],
                    },
                  ],
                },
              ],
            },
            {
              __typename: 'ExecutionStep',
              key: 'c[?]',
              kind: StepKind.UNRESOLVED,
              inputs: [
                {
                  __typename: 'ExecutionStepInput',
                  dependsOn: [
                    {
                      __typename: 'ExecutionStep',
                      key: 'b[?]',
                      kind: StepKind.UNRESOLVED,
                      outputs: [
                        {
                          __typename: 'ExecutionStepOutput',
                          name: 'result',
                          type: {
                            __typename: 'RegularDagsterType',
                            name: 'Any',
                          },
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
          artifactsPersisted: false,
        },
        ['a', 'b[1]', 'b[2]', 'c[1]'],
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
                  name: 'b[1]',
                },
              },
            ],
          },
        ],
        name: 'c[1]',
        outputs: [],
      },
    ]);
  });
});

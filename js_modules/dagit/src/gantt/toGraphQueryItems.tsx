import {gql} from '@apollo/client';

import {IGanttNode} from 'src/gantt/Constants';
import {invocationsOfPlannedDynamicStep, replacePlannedIndex} from 'src/gantt/DynamicStepSupport';
import {ExecutionPlanToGraphFragment} from 'src/gantt/types/ExecutionPlanToGraphFragment';
import {StepKind} from 'src/types/globalTypes';

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm or rendered
 * into the Gannt visualization or the SVG DAG visualization. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 *
 * Pass runtimeStepKeys to duplicate dynamic step sub-trees for each occurrence of
 * the step key found at runtime.
 */
export const toGraphQueryItems = (
  plan: ExecutionPlanToGraphFragment,
  runtimeStepKeys: string[],
) => {
  const nodeTable: {[key: string]: IGanttNode} = {};
  const keyExpansionMap: {[key: string]: string[]} = {};

  for (const step of plan.steps) {
    if (step.kind === StepKind.UNRESOLVED) {
      const runtime = invocationsOfPlannedDynamicStep(step.key, runtimeStepKeys);
      keyExpansionMap[step.key] = runtime;
      for (const k of runtime) {
        nodeTable[k] = {
          name: k,
          inputs: [],
          outputs: [],
        };
      }
    } else {
      nodeTable[step.key] = {
        name: step.key,
        inputs: [],
        outputs: [],
      };
    }
  }

  for (const step of plan.steps) {
    for (const input of step.inputs) {
      const keys = keyExpansionMap[step.key] ? keyExpansionMap[step.key] : [step.key];
      for (const key of keys) {
        nodeTable[key].inputs.push({
          dependsOn: input.dependsOn.map((d) => ({
            solid: {
              name: d.kind === StepKind.UNRESOLVED ? replacePlannedIndex(d.key, key) : d.key,
            },
          })),
        });

        for (const upstream of input.dependsOn) {
          const upstreamKey =
            upstream.kind === StepKind.UNRESOLVED
              ? replacePlannedIndex(upstream.key, key)
              : upstream.key;
          let output = nodeTable[upstreamKey].outputs[0];
          if (!output) {
            output = {
              dependedBy: [],
            };
            nodeTable[upstreamKey].outputs.push(output);
          }
          output.dependedBy.push({
            solid: {name: key},
          });
        }
      }
    }
  }

  return Object.values(nodeTable);
};

export const EXECUTION_PLAN_TO_GRAPH_FRAGMENT = gql`
  fragment ExecutionPlanToGraphFragment on ExecutionPlan {
    steps {
      key
      kind
    }
    steps {
      key
      kind
      inputs {
        dependsOn {
          key
          kind
          outputs {
            name
            type {
              name
            }
          }
        }
      }
    }
    artifactsPersisted
  }
`;

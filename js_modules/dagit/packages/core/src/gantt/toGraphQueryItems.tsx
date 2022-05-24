import {gql} from '@apollo/client';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {IStepMetadata, IStepState} from '../runs/RunMetadataProvider';
import {StepKind} from '../types/globalTypes';

import {invocationsOfPlannedDynamicStep, replacePlannedIndex} from './DynamicStepSupport';
import {ExecutionPlanToGraphFragment} from './types/ExecutionPlanToGraphFragment';

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
  runtimeStepMetadata: {[key: string]: IStepMetadata},
) => {
  // Step 1: Find unresolved steps in the initial plan and build a mapping
  // of their unresolved names to their resolved step keys, eg:
  // "multiply_input[*]" => ["multiply_input[1]", "multiply_input[2]"]
  const keyExpansionMap: {[key: string]: string[]} = {};
  const runtimeStepKeys = Object.keys(runtimeStepMetadata);

  for (const step of plan.steps) {
    if (step.kind === StepKind.UNRESOLVED_MAPPED) {
      const keys = invocationsOfPlannedDynamicStep(step.key, runtimeStepKeys);

      // If the upstream steps have NOT succeeded, it's expected that there are zero runtime step keys
      // matching the dynamic step. Until upstream steps run, we should show the [*] placeholder item
      // in the runtime graph (rather than just showing nothing.)
      const invocationsHappened = step.inputs.every((i) =>
        i.dependsOn.every((s) => IStepState.SUCCEEDED === runtimeStepMetadata[s.key]?.state),
      );
      if (!invocationsHappened && keys.length === 0) {
        keyExpansionMap[step.key] = [step.key];
        continue;
      }
      // The order matters here: add the planned dynamic step at the end, so when displaying the gantt
      // chart, we can ignore planned dynamic step if any of its invocation exists (i.e. hide the
      // unresolved node if any resolved node exists).
      keyExpansionMap[step.key] = [...keys, step.key];
    }
  }

  // Step 2: Create a graph node for each resolved step without any inputs or outputs.
  const nodeTable: {[key: string]: GraphQueryItem} = {};
  for (const step of plan.steps) {
    const stepRuntimeKeys = keyExpansionMap[step.key] ? keyExpansionMap[step.key] : [step.key];
    for (const key of stepRuntimeKeys) {
      nodeTable[key] = {
        name: key,
        inputs: [],
        outputs: [],
      };
    }
  }

  // Step 3: For each step in the original plan, visit each input and create inputs/outputs
  // in our Gantt Node result set.
  for (const step of plan.steps) {
    const stepRuntimeKeys = keyExpansionMap[step.key] ? keyExpansionMap[step.key] : [step.key];
    for (const key of stepRuntimeKeys) {
      for (const input of step.inputs) {
        // Add the input to our node in the result set
        const nodeInput: GraphQueryItem['inputs'][0] = {dependsOn: []};
        nodeTable[key].inputs.push(nodeInput);

        // For each upstream step in the plan, map it to upstream nodes in the runtime graph
        // and attach inputs / outputs to our result graph.
        for (const upstream of input.dependsOn) {
          let upstreamKeys = [];
          if (step.kind === StepKind.UNRESOLVED_COLLECT) {
            // If we are a collect, there may be N runtime keys fanning in to this input,
            // fetch the keys if they exist or fall back to the sigle upstream step case.
            upstreamKeys = keyExpansionMap[upstream.key] || [upstream.key];
          } else {
            // If the input was coming from an unresolved mapped step and WE are not a collector,
            // assume our own dynamic key index applies to the upstream mapped step as well.
            upstreamKeys = [
              upstream.kind === StepKind.UNRESOLVED_MAPPED
                ? replacePlannedIndex(upstream.key, key)
                : upstream.key,
            ];
          }

          for (const upstreamKey of upstreamKeys) {
            if (!nodeTable[upstreamKey]) {
              continue;
            }
            nodeInput.dependsOn.push({solid: {name: upstreamKey}});
            let upstreamOutput: GraphQueryItem['outputs'][0] = nodeTable[upstreamKey].outputs[0];
            if (!upstreamOutput) {
              upstreamOutput = {dependedBy: []};
              nodeTable[upstreamKey].outputs.push(upstreamOutput);
            }
            upstreamOutput.dependedBy.push({
              solid: {name: key},
            });
          }
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
      inputs {
        dependsOn {
          key
          kind
        }
      }
    }
  }
`;

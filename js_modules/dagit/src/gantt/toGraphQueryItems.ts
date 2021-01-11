import {IGanttNode} from 'src/gantt/Constants';
import {GanttChartExecutionPlanFragment} from 'src/gantt/types/GanttChartExecutionPlanFragment';

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 */
export const toGraphQueryItems = (
  plan: GanttChartExecutionPlanFragment,
  runtimeStepKeys: string[],
) => {
  const nodeTable: {[key: string]: IGanttNode} = {};
  const keyExpansionMap: {[key: string]: string[]} = {};

  for (const step of plan.steps) {
    if (step.key.includes('[?]')) {
      const runtime = runtimeStepKeys.filter((k) => k.startsWith(step.key.replace('?]', '')));
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

  const replacingIndexWithSame = (key: string, keyWithIndex: string) => {
    if (key.includes('[?]') && keyWithIndex.endsWith(']')) {
      return key.replace('[?]', keyWithIndex.match(/(\[.*\])/)![1]);
    }
    return key;
  };

  for (const step of plan.steps) {
    for (const input of step.inputs) {
      const keys = keyExpansionMap[step.key] ? keyExpansionMap[step.key] : [step.key];
      for (const key of keys) {
        nodeTable[key].inputs.push({
          dependsOn: input.dependsOn.map((d) => ({
            solid: {
              name: replacingIndexWithSame(d.key, key),
            },
          })),
        });

        for (const upstream of input.dependsOn) {
          const upstreamKey = replacingIndexWithSame(upstream.key, key);
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

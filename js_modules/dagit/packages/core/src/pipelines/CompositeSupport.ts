import {GraphExplorerSolidHandleFragment} from './types/GraphExplorerSolidHandleFragment';

function explodeComposite(
  handles: GraphExplorerSolidHandleFragment[],
  composite: GraphExplorerSolidHandleFragment,
) {
  if (composite.solid.definition.__typename !== 'CompositeSolidDefinition') {
    throw new Error('explodeComposite takes a composite handle.');
  }

  // Find all the solid handles that are within this composite and prefix their
  // names with the composite container's name, giving them names that should
  // match their handleID. (Note: We can't assign them their real handleIDs
  // because we'd have to dig through `handles` to find each solid based on it's
  // name + parentHandleID and then get it's handleID - dependsOn, etc. provide
  // Solid references not SolidHandle references.)
  const nested = handles.filter((h) => h.handleID === `${composite.handleID}.${h.solid.name}`);
  nested.forEach((n) => {
    n.solid.name = n.handleID;
    n.solid.inputs.forEach((i) => {
      i.dependsOn.forEach((d) => {
        d.solid.name = `${composite.handleID}.${d.solid.name}`;
      });
    });
    n.solid.outputs.forEach((i) => {
      i.dependedBy.forEach((d) => {
        d.solid.name = `${composite.handleID}.${d.solid.name}`;
      });
    });
  });

  composite.solid.definition.inputMappings.forEach((inmap) => {
    // For each input mapping on the composite, find the referenced parts of the graph:
    // The composite input, mapped (interior) solid and interior solid input.
    //
    const compositeInput = composite.solid.inputs.find(
      (i) => i.definition.name === inmap.definition.name,
    );
    if (!compositeInput) {
      console.warn(`CompositeSupport: No composite input matching ${inmap.definition.name}`);
      return;
    }

    const interiorTargetName = `${composite.solid.name}.${inmap.mappedInput.solid.name}`;
    const [interiorTarget] = handles.filter((h) => h.handleID === interiorTargetName);
    if (!interiorTarget) {
      console.warn(`CompositeSupport: No interior solid matching ${interiorTargetName}`);
      return;
    }
    const interiorTargetInput = interiorTarget.solid.inputs.find(
      (i) => i.definition.name === inmap.mappedInput.definition.name,
    );
    if (!interiorTargetInput) {
      console.warn(
        `CompositeSupport: No interior solid input matching ${inmap.mappedInput.definition.name}`,
      );
      return;
    }

    // Ok! We need to update the input.dependsOn AND the output.dependedBy
    // (both references to the relationship) to ensure correct graph rendering.

    // Change #1: Give the interior solid input (the target of the input mapping)
    // the "dependsOn" of the composite input, effectively "applying" the mapping.
    interiorTargetInput.dependsOn.push(...compositeInput.dependsOn);

    // Change #2: Find handles on the graph that were bound to this composite input
    // and change their output.dependedBy[] to point to the interior solid.
    handles.forEach((h) =>
      h.solid.outputs.forEach((i) => {
        i.dependedBy.forEach((dep) => {
          if (
            dep.solid.name === composite.solid.name &&
            dep.definition.name === compositeInput.definition.name
          ) {
            dep.solid.name = interiorTargetName;
            dep.definition.name = interiorTargetInput.definition.name;
          }
        });
      }),
    );
  });

  // Repeat the code above for outputs - this is just different enough that it's
  // not worth abstracting to re-use code...

  composite.solid.definition.outputMappings.forEach((outmap) => {
    const compositeOutput = composite.solid.outputs.find(
      (i) => i.definition.name === outmap.definition.name,
    );
    if (!compositeOutput) {
      console.warn(`CompositeSupport: No composite input matching ${outmap.definition.name}`);
      return;
    }
    const interiorTargetName = `${composite.solid.name}.${outmap.mappedOutput.solid.name}`;
    const [interiorTarget] = handles.filter((h) => h.handleID === interiorTargetName);
    if (!interiorTarget) {
      console.warn(`CompositeSupport: No interior solid matching ${interiorTargetName}`);
      return;
    }
    const interiorTargetOutput = interiorTarget.solid.outputs.find(
      (i) => i.definition.name === outmap.mappedOutput.definition.name,
    );
    if (!interiorTargetOutput) {
      console.warn(
        `CompositeSupport: No interior solid output matching ${outmap.mappedOutput.definition.name}`,
      );
      return;
    }
    // Change #1: Give the interior solid output (the target of the output mapping)
    // the "dependedBy" of the composite output, effectively "applying" the mapping.
    interiorTargetOutput.dependedBy.push(...compositeOutput.dependedBy);

    // Change #2: Find handles on the graph that were bound to this composite output
    // and change their input.dependsOn[] to point to the interior solid.
    handles.forEach((h) =>
      h.solid.inputs.forEach((i) => {
        i.dependsOn.forEach((dep) => {
          if (
            dep.solid.name === composite.solid.name &&
            dep.definition.name === compositeOutput.definition.name
          ) {
            dep.solid.name = interiorTargetName;
            dep.definition.name = interiorTargetOutput.definition.name;
          }
        });
      }),
    );
  });

  // Return the interior solids that replace the composite in the graph
  return nested;
}

/**
 * Given a solid handle graph, returns a new solid handle graph with all of the
 * composites recursively replaced with their interior solids. Interior solids
 * are given their handle names ("composite.inner") to avoid name collisions.
 *
 * @param handles All the SolidHandles in the pipeline (NOT just current layer)
 */
export function explodeCompositesInHandleGraph(handles: GraphExplorerSolidHandleFragment[]) {
  // Clone the entire graph so we can modify solid names in-place
  handles = JSON.parse(JSON.stringify(handles));

  // Reset the output to just the solids in the top layer of the graph
  const results = handles.filter((h) => !h.handleID.includes('.'));

  // Find composites in the output and replace the composite with it's content
  // solids (renaming the content solids to include the composite's handle and
  // linking them to the other solids via the composite's input/output mappings)
  while (true) {
    const idx = results.findIndex(
      (h) => h.solid.definition.__typename === 'CompositeSolidDefinition',
    );
    if (idx === -1) {
      break;
    }
    results.splice(idx, 1, ...explodeComposite(handles, results[idx]));
  }

  return results;
}

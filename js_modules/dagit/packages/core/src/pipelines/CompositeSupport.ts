import {PipelineExplorerSolidHandleFragment} from './types/PipelineExplorerSolidHandleFragment';

function explodeComposite(
  handles: PipelineExplorerSolidHandleFragment[],
  handle: PipelineExplorerSolidHandleFragment,
) {
  if (handle.solid.definition.__typename !== 'CompositeSolidDefinition') {
    throw new Error('explodeComposite takes a composite handle.');
  }

  // Replace all references to this composite's inputs in other solid defitions
  // with the interior target of the input mappings
  handle.solid.definition.inputMappings.forEach((inmap) => {
    const solidName = `${handle.solid.name}.${inmap.mappedInput.solid.name}`;
    handles.forEach((h) =>
      h.solid.outputs.forEach((i) => {
        i.dependedBy.forEach((dep) => {
          if (
            dep.definition.name === inmap.definition.name &&
            dep.solid.name === handle.solid.name
          ) {
            dep.solid.name = solidName;
            dep.definition.name = inmap.mappedInput.definition.name;
          }
        });
      }),
    );
  });

  // Replace all references to this composite's outputs in other solid defitions
  // with the interior target of the output mappings
  handle.solid.definition.outputMappings.forEach((outmap) => {
    const solidName = `${handle.solid.name}.${outmap.mappedOutput.solid.name}`;
    handles.forEach((h) =>
      h.solid.inputs.forEach((i) => {
        i.dependsOn.forEach((dep) => {
          if (
            dep.definition.name === outmap.definition.name &&
            dep.solid.name === handle.solid.name
          ) {
            dep.solid.name = solidName;
            dep.definition.name = outmap.mappedOutput.definition.name;
          }
        });
      }),
    );
  });

  // Find all the solid handles that are within this composite and prefix their
  // names with the composite container's name, giving them names that should
  // match their handleID. (Note: We can't assign them their real handleIDs
  // because we'd have to dig through `handles` to find each solid based on it's
  // name + parentHandleID and then get it's handleID - dependsOn, etc. provide
  // Solid references not SolidHandle references.)
  const nested = handles.filter((h) => h.handleID === `${handle.handleID}.${h.solid.name}`);
  nested.forEach((n) => {
    n.solid.name = n.handleID;
    n.solid.inputs.forEach((i) => {
      i.dependsOn.forEach((d) => {
        d.solid.name = `${handle.handleID}.${d.solid.name}`;
      });
    });
    n.solid.outputs.forEach((i) => {
      i.dependedBy.forEach((d) => {
        d.solid.name = `${handle.handleID}.${d.solid.name}`;
      });
    });
  });

  // Find all the input dependencies of a composite solid and transfer them to their mapped interior
  // target solids
  handle.solid.definition.inputMappings.forEach((inmap) => {
    handle.solid.inputs.forEach((input) => {
      const solidName = `${handle.solid.name}.${inmap.mappedInput.solid.name}`;
      const [interiorTarget] = handles.filter((h) => h.handleID === solidName);
      if (!interiorTarget) {
        return;
      }
      const matchingInput = interiorTarget.solid.inputs.find(
        (i) => i.definition.name === input.definition.name,
      );
      if (!matchingInput) {
        return;
      }
      matchingInput.dependsOn = matchingInput.dependsOn.concat(input.dependsOn);
    });
  });

  // Find all the output dependencies of a composite solid and transfer them to their mapped interior
  // target solids
  handle.solid.definition.outputMappings.forEach((outmap) => {
    handle.solid.outputs.forEach((output) => {
      const solidName = `${handle.solid.name}.${outmap.mappedOutput.solid.name}`;
      const [interiorTarget] = handles.filter((h) => h.handleID === solidName);
      if (!interiorTarget) {
        return;
      }
      const matchingOutput = interiorTarget.solid.outputs.find(
        (i) => i.definition.name === output.definition.name,
      );
      if (!matchingOutput) {
        return;
      }
      matchingOutput.dependedBy = matchingOutput.dependedBy.concat(output.dependedBy);
    });
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
export function explodeCompositesInHandleGraph(handles: PipelineExplorerSolidHandleFragment[]) {
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

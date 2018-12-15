// TODO: type typeData with graphql fragments
// This is not production quality code. This
// is meant to demonstrate to @bengotow what
// the algorithm for this looks like and how it interacts
// with the incoming graphql (See TYPE_RENDER_QUERY in test_graphql.py)
// Ben will add structure to allow for richer UIs than just a plain string
export function printType(typeData: any): string {
  const innerTypeLookup = {};
  for (const innerTypeData of typeData.innerTypes) {
    innerTypeLookup[innerTypeData.name] = innerTypeData;
  }

  return printRecurse(typeData, innerTypeLookup, "");
}

function printRecurse(typeData: any, typeLookup: any, indent: string): string {
  if (typeData.isDict) {
    let buildString = "{\n";
    const newIndent = indent + "  ";
    for (const fieldData of typeData.fields) {
      buildString += newIndent + fieldData.name;

      if (fieldData.isOptional) {
        buildString += "?";
      }
      const name = fieldData.type.name;
      buildString +=
        ": " + printRecurse(typeLookup[name], typeLookup, newIndent) + "\n";
    }
    buildString += indent + "}";
    return buildString;
  } else if (typeData.isList) {
    const innerType = typeData.innerTypes[0].name;
    return "[" + printRecurse(typeLookup[innerType], typeLookup, indent) + "]";
  } else if (typeData.isNullable) {
    const innerType = typeData.innerTypes[0].name;
    return printRecurse(typeLookup[innerType], typeLookup, indent) + "?";
  } else {
    return typeData.name;
  }
}

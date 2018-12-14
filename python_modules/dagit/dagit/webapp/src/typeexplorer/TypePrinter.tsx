// TODO: type typeData with graphql fragments
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

      buildString +=
        ": " +
        printRecurse(typeLookup[fieldData.type.name], typeLookup, newIndent) +
        "\n";
    }
    buildString += indent + "}";
    return buildString;
  } else if (typeData.isList) {
    return (
      "[" +
      printRecurse(
        typeLookup[typeData.innerTypes[0].name],
        typeLookup,
        indent
      ) +
      "]"
    );
  } else if (typeData.isNullable) {
    return (
      printRecurse(
        typeLookup[typeData.innerTypes[0].name],
        typeLookup,
        indent
      ) + "?"
    );
  } else {
    return typeData.name;
  }
}

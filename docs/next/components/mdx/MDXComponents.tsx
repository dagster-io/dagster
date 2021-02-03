// This file contains components used by MDX files. It is important to be careful when changing these,
// because these components need to be backwards compatible. If you need to udpate a component with a
// breaking change, rename the existing component across the codebase and save a copy.

// For example, if you need to update `PyObject`, rename the existing component to `PyObjectLegacy`
// and update all existing usage of it

import React, { useContext } from "react";

import VersionedLink from "../VersionedLink";
import data from "../../content/api/searchindex.json";

export const SearchIndexContext = React.createContext(null);

const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  displayText?: string;
}> = ({ module, object, displayText }) => {
  const value = useContext(SearchIndexContext);
  if (!value) {
    return null;
  }

  const objects = value.objects as any;
  const moduleObjects = objects[module];
  const objectData = moduleObjects && moduleObjects[object];

  if (!moduleObjects || !objectData) {
    // TODO: broken link
    // https://github.com/dagster-io/dagster/issues/2939
    return (
      <a className="no-underline hover:underline" href="#">
        <code className="bg-red-100 p-1">{displayText || object}</code>
      </a>
    );
  }

  const fileIndex = objectData[0];
  // TODO: refer to all anchors available in apidocs
  // https://github.com/dagster-io/dagster/issues/3568
  const doc = data.docnames[fileIndex];
  const link = doc.replace("sections/api/apidocs/", "/_apidocs/");

  return (
    <VersionedLink href={link + "#" + module + "." + object}>
      <a className="no-underline hover:underline">
        <code className="bg-blue-100 p-1">{displayText || object}</code>
      </a>
    </VersionedLink>
  );
};

export default {
  PyObject,
  VersionedLink,
};

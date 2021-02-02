// This file contains components used by MDX files. It is important to be careful when changing these,
// because these components need to be backwards compatible. If you need to udpate a component with a
// breaking change, rename the existing component across the codebase and save a copy.

// For example, if you need to update `PyObject`, rename the existing component to `PyObjectLegacy`
// and update all existing usage of it

import { useState } from "react";
import VersionedLink from "./VersionedLink";
import data from "../content/api/searchindex.json";
import React, { useContext } from "react";

const ExampleComponent = () => {
  return <span className="text-red-400 font-bold">Hello!</span>;
};

const AlertComponent = ({ children }) => {
  return <div className="flex bg-yellow-200 items-center">{children}</div>;
};

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

const Counter = () => {
  const [count, setCount] = useState(0);

  return (
    <div className="flex items-center space-x-4">
      <div>{count}</div>
      <div>
        <button
          className="p-4 bg-green-100"
          onClick={() => setCount(count + 1)}
        >
          +
        </button>
        <button className="p-4 bg-red-100" onClick={() => setCount(count - 1)}>
          -
        </button>
      </div>
    </div>
  );
};
const Example = ({ children }) => {
  return <div className="bg-gray-200 px-8 py-4">{children}</div>;
};

export default {
  ExampleComponent,
  AlertComponent,
  PyObject,
  Counter,
  Example,
  VersionedLink,
};

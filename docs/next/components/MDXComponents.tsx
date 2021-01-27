// This file contains components used by MDX files. It is important to be careful when changing these,
// because these components need to be backwards compatible. If you need to udpate a component with a
// breaking change, rename the existing component across the codebase and save a copy.

// For example, if you need to update `PyObject`, rename the existing component to `PyObjectLegacy`
// and update all existing usage of it

import { useState } from "react";

const ExampleComponent = () => {
  return <span className="text-red-400 font-bold">Hello!</span>;
};

const AlertComponent = ({ children }) => {
  return <div className="flex bg-yellow-200 items-center">{children}</div>;
};

const PyObject = ({ object, displayText }) => {
  return (
    <a className="no-underline hover:underline" href="#">
      <code className="bg-blue-100 p-1">{displayText || object}</code>
    </a>
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

export default {
  ExampleComponent,
  AlertComponent,
  PyObject,
  Counter,
};

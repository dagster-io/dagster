import React from "react";
import { createContext, useEffect, useContext, useState } from "react";
import { useStaticQuery, graphql, navigate } from "gatsby";

import { useLocalStorage } from "utils/localStorage";
import { version, all } from "~dagster-info";

const ctx = createContext({
  version: {
    all,
    current: version,
    last: version
  }
});

export const VersionProvider = ({ children }) => {
  const storage = useLocalStorage("currentVersion");
  const [current, setCurrentState] = useState(storage.get());

  const data = useStaticQuery(graphql`
    query VersionQuery {
      version: dagsterVersion
      allVersions: allDagsterVersion
    }
  `);

  const setCurrent = version => {
    setCurrentState(version);
    navigate(`${version}/install/install`);
  };

  useEffect(() => {
    storage.set(current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current]);

  return (
    <ctx.Provider
      value={{
        setCurrent,
        version: {
          current: current || data.version || version,
          all: data.allVersions,
          last: data.version
        }
      }}
    >
      {children}
    </ctx.Provider>
  );
};

export const useVersion = () => {
  return useContext(ctx);
};

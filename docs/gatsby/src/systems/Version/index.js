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
  const storageCurrent = storage.get();

  const data = useStaticQuery(graphql`
    query VersionQuery {
      version: dagsterVersion
      allVersions: allDagsterVersion
    }
  `);

  const setCurrent = version => {
    setCurrentState(version);
    // FIXME: This should navigate to the current page in the given version
    navigate(`${version}/install`);
  };

  const [current, setCurrentState] = useState(
    storageCurrent === "null" ||
      storageCurrent === "undefined" ||
      storageCurrent === null ||
      storageCurrent === undefined
      ? data.version || version
      : storageCurrent
  );

  useEffect(() => {
    storage.set(current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current]);

  const providerValue = {
    setCurrent,
    version: {
      current: current,
      all: data.allVersions,
      last: data.version
    }
  };

  return <ctx.Provider value={providerValue}>{children}</ctx.Provider>;
};

export const useVersion = () => {
  return useContext(ctx);
};

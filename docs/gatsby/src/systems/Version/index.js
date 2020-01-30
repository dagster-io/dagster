import React from "react";
import { createContext, useEffect, useContext, useState } from "react";
import { useStaticQuery, graphql, navigate } from "gatsby";

import { useLocalStorage } from "utils/localStorage";

const ctx = createContext();

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
          current:
            (current !== "undefined" && current !== "null" && current) ||
            data.version,
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

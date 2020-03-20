/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";
import { useVersion } from "systems/Version";
import { ChangeEvent } from "react";

export const VersionSelector: React.FC = () => {
  const { version, setCurrent } = useVersion();

  const handleChange = (ev: ChangeEvent<HTMLSelectElement>) => {
    setCurrent(ev.target!.value);
  };

  return (
    <select sx={styles.wrapper} onChange={handleChange} value={version.current}>
      {/* TODO: Check vs, I think it is a string*/}
      {version.all.map((vs: any) => (
        <option key={vs} value={vs}>
          {vs}
        </option>
      ))}
    </select>
  );
};

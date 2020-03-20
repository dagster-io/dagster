/** @jsx jsx */
import { Styled, jsx } from "theme-ui";
import { useRef, useEffect, HTMLAttributes, DetailedHTMLProps } from "react";
import hljs from "highlight.js";
import python from "highlight.js/lib/languages/python";
import yaml from "highlight.js/lib/languages/yaml";
import bash from "highlight.js/lib/languages/bash";

import * as styles from "./styles";

hljs.registerLanguage("python", python);
hljs.registerLanguage("yaml", yaml);
hljs.registerLanguage("bash", bash);

type PreProps = DetailedHTMLProps<
  HTMLAttributes<HTMLPreElement>,
  HTMLPreElement
> & {
  "data-language": string;
};

// TODO: Check out this element's props and fix ref type.
export const Pre: React.FC<PreProps> = ({ children, ...props }) => {
  const ref = useRef<any>();
  const language = props["data-language"] || "python";

  useEffect(() => {
    hljs.highlightBlock(ref.current);
  }, []);

  return (
    // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
    // @ts-ignore
    <Styled.pre sx={styles.wrapper} {...props}>
      <Styled.code ref={ref} className={`language-${language} hljs`}>
        {children}
      </Styled.code>
    </Styled.pre>
  );
};

// NOTE: This is unused. Instead, a remark plugin in used in next.config.js

import SyntaxHighlighter from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/cjs/styles/hljs";
import useAxios from "axios-hooks";

const LiteralInclude: React.FunctionComponent<{
  lines: string;
  path: string;
}> = ({ lines, path }) => {
  const [{ data, loading, error }, refetch] = useAxios(
    `/api/includes?filePath=${encodeURIComponent(path)}`
  );
  return (
    <>
      {data && (
        <SyntaxHighlighter language="python" style={dracula}>
          {data}
        </SyntaxHighlighter>
      )}
    </>
  );
};

export default LiteralInclude;

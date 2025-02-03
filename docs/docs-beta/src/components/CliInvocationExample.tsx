import CodeBlock from '@theme/CodeBlock';
import React, {Suspense, useMemo} from 'react';
import {useLoadModule} from './CodeExample';

interface CliInvocationExampleProps {
  path: string;
  lineStart?: number;
  lineEnd?: number;
  startAfter?: string; // marker that indicates beginning of code snippet
  endBefore?: string; // marker that indicates ending of code snippet
}

const CliInvocationExample: React.FC<CliInvocationExampleProps> = ({...props}) => {
  return (
    <Suspense>
      <CliInvocationExampleInner {...props} />
    </Suspense>
  );
};

const CliInvocationExampleInner: React.FC<CliInvocationExampleProps> = (props) => {
  const {path, lineStart, lineEnd, startAfter, endBefore, ...extraProps} = props;
  const language = 'shell';

  const cacheKey = JSON.stringify(props);
  const {content, error} = useLoadModule(cacheKey, path, lineStart, lineEnd, startAfter, endBefore);

  const [command, result] = useMemo(() => {
    const [command, ...rest] = content.split('\n\n');
    return [command, rest.join('\n\n')];
  }, [content]);

  if (error) {
    return <div style={{color: 'red', padding: '1rem', border: '1px solid red'}}>{error}</div>;
  }

  return (
    <>
      <div className="cli-invocation-example-command">
        <CodeBlock language={language} {...extraProps}>
          {command || 'Loading...'}
        </CodeBlock>
      </div>
      {command && result && (
        <div className="cli-invocation-example-result">
          <CodeBlock language={language} {...extraProps}>
            {result || 'Loading...'}
          </CodeBlock>
        </div>
      )}
    </>
  );
};

export default CliInvocationExample;

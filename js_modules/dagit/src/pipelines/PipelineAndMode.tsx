import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

interface Props {
  pipelineName: string;
  pipelineHref?: string;
  mode: string;
}

export const PipelineAndMode: React.FC<Props> = ({pipelineName, pipelineHref, mode}) => {
  const pipeline = pipelineHref ? <Link to={pipelineHref}>{pipelineName}</Link> : pipelineName;
  return (
    <>
      {pipeline}
      {mode === 'default' ? null : <span style={{color: Colors.GRAY3}}>{`: ${mode}`}</span>}
    </>
  );
};

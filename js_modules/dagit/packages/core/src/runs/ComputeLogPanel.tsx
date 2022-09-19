import {Box, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {AppContext} from '../app/AppContext';

import {ComputeLogContent} from './ComputeLogContent';
import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';
import {useComputeLogs} from './useComputeLogs';

interface ComputeLogPanelProps {
  runId: string;
  ioType: string;
  setComputeLogUrl: (url: string | null) => void;
}

interface ComputeLogPanelMaybeKeyProps extends ComputeLogPanelProps {
  computeLogKey?: string;
  stepKeys: string[];
}

export const ComputeLogPanel: React.FC<ComputeLogPanelMaybeKeyProps> = (props) => {
  const {runId, stepKeys, computeLogKey, ioType, setComputeLogUrl} = props;

  if (!stepKeys.length || !computeLogKey) {
    return (
      <Box
        flex={{justifyContent: 'center', alignItems: 'center'}}
        style={{flex: 1, height: '100%'}}
      >
        <Spinner purpose="section" />
      </Box>
    );
  }

  return (
    <ComputeLogsPanelWithKey
      runId={runId}
      computeLogKey={computeLogKey}
      ioType={ioType}
      setComputeLogUrl={setComputeLogUrl}
    />
  );
};

interface ComputeLogPanelWithKeyProps extends ComputeLogPanelProps {
  computeLogKey: string;
}

const resolveDownloadUrl = (
  rootServerURI: string,
  logData: ComputeLogContentFileFragment | null,
) => {
  const downloadUrl = logData?.downloadUrl;
  if (!downloadUrl) {
    return null;
  }
  const isRelativeUrl = (x?: string) => x && x.startsWith('/');
  return isRelativeUrl(downloadUrl) ? rootServerURI + downloadUrl : downloadUrl;
};

const ComputeLogsPanelWithKey: React.FC<ComputeLogPanelWithKeyProps> = React.memo((props) => {
  const {runId, computeLogKey, ioType, setComputeLogUrl} = props;
  const {rootServerURI} = React.useContext(AppContext);

  const {isLoading, stdout, stderr} = useComputeLogs(runId, computeLogKey);
  const logData = ioType === 'stdout' ? stdout : stderr;
  const downloadUrl = resolveDownloadUrl(rootServerURI, logData);

  return (
    <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
      <ContentWrapper
        logData={stdout}
        isLoading={isLoading}
        isVisible={ioType === 'stdout'}
        downloadUrl={downloadUrl}
        setComputeLogUrl={setComputeLogUrl}
      />
      <ContentWrapper
        logData={stderr}
        isLoading={isLoading}
        isVisible={ioType === 'stderr'}
        downloadUrl={downloadUrl}
        setComputeLogUrl={setComputeLogUrl}
      />
    </div>
  );
});

const ContentWrapper = ({
  isLoading,
  isVisible,
  logData,
  downloadUrl,
  setComputeLogUrl,
}: {
  isVisible: boolean;
  isLoading: boolean;
  logData: ComputeLogContentFileFragment | null;
  downloadUrl: string | null;
  setComputeLogUrl: (url: string | null) => void;
}) => {
  React.useEffect(() => {
    setComputeLogUrl(downloadUrl);
  }, [setComputeLogUrl, downloadUrl]);
  return (
    <ComputeLogContent
      logData={logData}
      isLoading={isLoading}
      isVisible={isVisible}
      downloadUrl={downloadUrl}
    />
  );
};

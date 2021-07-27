import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';

import {ComputeLogContent} from './ComputeLogContent';
import {ComputeLogsProvider} from './ComputeLogProvider';
import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';
interface RunComputeLogs {
  runId: string;
  stepKeys: string[];
  computeLogKey?: string;
  ioType: string;
  setComputeLogUrl: (url: string | null) => void;
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

export const ComputeLogPanel: React.FC<RunComputeLogs> = React.memo(
  ({runId, stepKeys, computeLogKey, ioType, setComputeLogUrl}) => {
    const {rootServerURI} = React.useContext(AppContext);

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
      <div style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>
        <ComputeLogsProvider runId={runId} stepKey={computeLogKey}>
          {({isLoading, stdout, stderr}) => {
            const logData = ioType === 'stdout' ? stdout : stderr;
            const downloadUrl = resolveDownloadUrl(rootServerURI, logData);
            return (
              <>
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
              </>
            );
          }}
        </ComputeLogsProvider>
      </div>
    );
  },
);

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

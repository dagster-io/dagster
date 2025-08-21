import {useEffect} from 'react';

import {ILogCaptureInfo, IRunMetadataDict} from './RunMetadataProvider';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

export const matchingComputeLogKeyFromStepKey = (
  logCaptureSteps: {[fileKey: string]: ILogCaptureInfo} | undefined,
  stepKey: string,
) => {
  const stepsInfo = logCaptureSteps ? Object.values(logCaptureSteps) : [];
  const matching = stepsInfo.find((info) => info.stepKeys.includes(stepKey));
  return matching && matching?.fileKey;
};

export function useComputeLogFileKeyForSelection({
  stepKeys,
  selectionStepKeys,
  metadata,
  defaultToFirstStep = true,
}: {
  stepKeys: string[];
  selectionStepKeys: string[];
  metadata: IRunMetadataDict;
  defaultToFirstStep?: boolean;
}) {
  const [computeLogFileKey, setComputeLogFileKey] = useQueryPersistedState<string>({
    queryKey: 'logFileKey',
  });

  useEffect(() => {
    if (!stepKeys?.length || computeLogFileKey) {
      return;
    }

    if (!selectionStepKeys.length && !defaultToFirstStep) {
      return;
    }

    if (metadata.logCaptureSteps) {
      const logFileKeys = Object.keys(metadata.logCaptureSteps);
      const selectedLogKey = logFileKeys.find((logFileKey) => {
        return selectionStepKeys.every(
          (stepKey) =>
            metadata.logCaptureSteps &&
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            metadata.logCaptureSteps[logFileKey]!.stepKeys.includes(stepKey),
        );
      });
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      setComputeLogFileKey(selectedLogKey || logFileKeys[0]!);
    } else if (!stepKeys.includes(computeLogFileKey)) {
      const matching = matchingComputeLogKeyFromStepKey(
        metadata.logCaptureSteps,
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        selectionStepKeys.length === 1 ? selectionStepKeys[0]! : stepKeys[0]!,
      );
      if (matching) {
        setComputeLogFileKey(matching);
      }
    } else if (selectionStepKeys.length === 1 && computeLogFileKey !== selectionStepKeys[0]) {
      const matching = matchingComputeLogKeyFromStepKey(
        metadata.logCaptureSteps,
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        selectionStepKeys[0]!,
      );
      if (matching) {
        setComputeLogFileKey(matching);
      }
    }
  }, [
    stepKeys,
    computeLogFileKey,
    selectionStepKeys,
    metadata.logCaptureSteps,
    setComputeLogFileKey,
    defaultToFirstStep,
  ]);

  const logCaptureInfo: ILogCaptureInfo | undefined =
    metadata.logCaptureSteps && computeLogFileKey in metadata.logCaptureSteps
      ? metadata.logCaptureSteps[computeLogFileKey]
      : undefined;

  return {logCaptureInfo, computeLogFileKey, setComputeLogFileKey};
}

import React from 'react';

type CloudFeatureFlagContextType = {
  enableAMPTimeline: boolean;
};
export const CloudFeatureFlagContext = React.createContext<CloudFeatureFlagContextType>({
  enableAMPTimeline: true,
});
export const useCloudFeatureFlag = () => {
  return React.useContext(CloudFeatureFlagContext);
};

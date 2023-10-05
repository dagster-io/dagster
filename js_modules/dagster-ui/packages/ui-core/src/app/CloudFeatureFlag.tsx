import React from 'react';

type CloudFeatureFlagContextType = {
  enableAMPTimeline: boolean;
};
const CloudFeatureFlagContext = React.createContext<CloudFeatureFlagContextType>({
  enableAMPTimeline: false,
});
export const useCloudFeatureFlag = () => {
  return React.useContext(CloudFeatureFlagContext);
};

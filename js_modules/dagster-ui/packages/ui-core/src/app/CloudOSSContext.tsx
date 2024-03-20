import React from 'react';

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
  showGlobalAMPToSensorAMPBanner: boolean;
}>({
  isBranchDeployment: false,
  showGlobalAMPToSensorAMPBanner: false,
});

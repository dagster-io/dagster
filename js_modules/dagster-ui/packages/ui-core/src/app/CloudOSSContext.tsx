import React from 'react';

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
  currentDeploymentName?: string;
}>({
  isBranchDeployment: false,
});

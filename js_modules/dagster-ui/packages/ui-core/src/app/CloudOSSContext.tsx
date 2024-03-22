import React from 'react';

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
}>({
  isBranchDeployment: false,
});

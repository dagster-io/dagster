import React from 'react';

export function useDocumentVisibility() {
  const [documentVisible, setDocumentVisible] = React.useState(true);
  React.useEffect(() => {
    const handler = () => {
      setDocumentVisible(!document.hidden);
    };
    document.addEventListener('visibilitychange', handler);
    return () => {
      document.removeEventListener('visibilitychange', handler);
    };
  });

  return documentVisible;
}

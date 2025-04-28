import React from 'react';
interface WideContentProps {
  children: React.ReactNode;
  maxSize?: 1000 | 1100 | 1200 | 1300;
}

const WideContent: React.FC<WideContentProps> = ({children, maxSize = 1300}) => {
  return (
    <div className={`wide-content s${maxSize}`} style={{}}>
      {children}
    </div>
  );
};

export default WideContent;

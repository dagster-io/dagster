import React from 'react';
import cx from 'classnames';

type CommunityLinksProps = {
  className?: string;
};

const CommunityLinks: React.FC<CommunityLinksProps> = ({ className }) => {
  return (
    <div className={cx('flex flex-row nowrap justify-around', className)}>
      <a href="https://github.com/dagster-io/dagster">
        <img className="h-8" src="/assets/images/logos/github-icon.svg" />
      </a>
      <a href="https://dagster-slackin.herokuapp.com/">
        <img className="h-8" src="/assets/images/logos/slack-icon.svg" />
      </a>
      <a href="https://stackoverflow.com/questions/tagged/dagster">
        <img
          className="h-8"
          src="/assets/images/logos/stack-overflow-icon.svg"
        />
      </a>
    </div>
  );
};

export default CommunityLinks;

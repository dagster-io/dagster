import React from 'react';
import cx from 'classnames';

type CommunityLinksProps = {
  className?: string;
};

const Icon: React.FC<{ href: string; src: string }> = ({ href, src }) => {
  return (
    <a href={href} target="blank">
      <img
        className="h-10 rounded-md p-2 hover:shadow hover:bg-gray-50"
        src={src}
      />
    </a>
  );
};

const CommunityLinks: React.FC<CommunityLinksProps> = ({ className }) => {
  return (
    <div className={cx('flex flex-row nowrap justify-around', className)}>
      <Icon
        href="https://github.com/dagster-io/dagster"
        src="/assets/images/logos/github-icon.svg"
      />
      <Icon
        href="https://dagster-slackin.herokuapp.com/"
        src="/assets/images/logos/slack-icon.svg"
      />
      <Icon
        href="https://stackoverflow.com/questions/tagged/dagster"
        src="/assets/images/logos/stack-overflow-icon.svg"
      />
    </div>
  );
};

export default CommunityLinks;

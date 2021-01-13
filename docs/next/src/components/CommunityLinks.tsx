import React from 'react';
import cx from 'classnames';
import { VersionedImage } from './VersionedComponents';

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
      <a href="https://github.com/dagster-io/dagster" target="_blank">
        <VersionedImage
          className="h-6"
          src="/assets/images/logos/github-icon.svg"
        />
      </a>
      <a href="https://dagster-slackin.herokuapp.com/" target="_blank">
        <VersionedImage
          className="h-6"
          src="/assets/images/logos/slack-icon.svg"
        />
      </a>
      <a href="https://stackoverflow.com/questions/tagged/dagster" target="_blank">
        <VersionedImage
          className="h-6"
          src="/assets/images/logos/stack-overflow-icon.svg"
        />
      </a>
      {/* FontAwesome requires that their usage license is included: https://fontawesome.com/license */}
      <a href="https://www.getrevue.co/profile/dagster" target="_blank">
        <VersionedImage
          className="h-6"
          src="/assets/images/logos/email-icon.svg"
        />
      </a>
    </div>
  );
};

export default CommunityLinks;

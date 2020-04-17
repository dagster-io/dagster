import { Dispatch, SetStateAction } from 'react';
import cx from 'classnames';
import Nav from './Nav';

type SidebarMobileProps = {
  isNavigationVisible: boolean;
  setIsNavigationVisible: Dispatch<SetStateAction<boolean>>;
};

const SidebarMobile: React.FC<SidebarMobileProps> = ({
  isNavigationVisible,
  setIsNavigationVisible,
}) => {
  return (
    <div
      className={cx({
        hidden: !isNavigationVisible,
      })}
    >
      <div className="fixed inset-0 flex z-40">
        <div className="fixed inset-0">
          <div className="absolute inset-0 bg-gray-600 opacity-75"></div>
        </div>
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
          <div className="absolute top-0 right-0 -mr-14 p-1">
            <button
              className="flex items-center justify-center h-12 w-12 rounded-full focus:outline-none focus:bg-gray-600"
              aria-label="Close sidebar"
              onClick={() => setIsNavigationVisible(false)}
            >
              <svg
                className="h-6 w-6 text-white"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
            <Nav className="mt-5 px-2" isMobile />
          </div>
        </div>
        <div className="flex-shrink-0 w-14" />
      </div>
    </div>
  );
};

export default SidebarMobile;

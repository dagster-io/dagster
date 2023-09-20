import * as React from 'react';

interface Props {
  children: React.ReactNode;
}

export const Callout = ({children}) => {
  return (
    <div className={`callout bg-primary-100 border-l-4 border-primary-500 px-4 py-4`}>
      <div className="flex items-start">
        <div className="flex-shrink-0 mt-[1px]">
          <svg
            className={`h-5 w-5 text-primary-500`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
          </svg>
        </div>
        <div className="ml-3 text-sm text-gray-900">{children}</div>
      </div>
    </div>
  );
};

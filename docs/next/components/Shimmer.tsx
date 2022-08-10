import * as React from 'react';

// Shimmer (skeleton) used as content placeholder while loading
export function Shimmer() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 w-full my-12 h-96 animate-pulse prose max-w-none">
      <div className="bg-gray-200 px-4 w-48 h-12"></div>
      <div className="bg-gray-200 mt-12 px-4 w-1/2 h-6"></div>
      <div className="bg-gray-200 mt-5 px-4 w-2/3 h-6"></div>
      <div className="bg-gray-200 mt-5 px-4 w-1/3 h-6"></div>
      <div className="bg-gray-200 mt-5 px-4 w-1/2 h-6"></div>
    </div>
  );
}

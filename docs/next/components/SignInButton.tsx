import * as React from 'react';

export const SignInButton = () => {
  const onClick = () => {
    const url = new URL('https://dagster.cloud');
    const anonymousId = window.analytics?.user().anonymousId();
    if (anonymousId) {
      const params = new URLSearchParams();
      params.append('ajs_aid', anonymousId);
      url.search = params.toString();
    }
    window.location.assign(url.toString());
  };

  return (
    <button
      className="hidden xl:block py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
      onClick={onClick}
    >
      Sign in
    </button>
  );
};

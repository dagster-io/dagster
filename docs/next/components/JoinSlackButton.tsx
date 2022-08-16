import React from 'react';

export const JoinSlackButton: React.FC<{icon?: boolean}> = ({icon}) => {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="h-screen inset-0 fixed z-50 flex flex-col justify-center items-center bg-opacity-25 bg-black ml-0"
        >
          <div
            className="w-10/12 md:w-4/6 lg:w-3/6 rounded-3xl shadow-xl relative overflow-hidden bg-white"
            style={{height: 600}}
          >
            <iframe
              src="https://dagster-slackin.herokuapp.com/"
              className="inset-0 absolute w-full h-full"
            />
          </div>
        </div>
      )}
      <p className="self-center">
        <a
          onClick={() => setOpen(true)}
          className={
            icon
              ? 'px-3 py-3 inline-flex cursor-pointer hover:bg-lavender bg-opacity-0 hover:bg-opacity-50 rounded-full transition'
              : 'px-4 py-1 border border-gable-green cursor-pointer bg-transparent hover:bg-gable-green hover:text-white inline-flex gap-2 leading-8 items-center whitespace-nowrap transition rounded-full'
          }
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
          </svg>
          <span className={icon ? 'hidden' : ''}>Join us on Slack</span>
        </a>
      </p>
    </>
  );
};

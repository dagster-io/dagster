export default function Custom404() {
  return (
    <div
      className="flex-1 min-w-0 relative z-0 focus:outline-none pt-4"
      tabIndex={0}
    >
      <div className="py-4 px-4 sm:px-6 lg:px-8 w-full">
        <div className="DocSearch-content prose dark:prose-dark max-w-none">
          <div className="mt-16 lg:mt-4 md:h-(screen-60) flex justify-center items-center">
            <div className="flex flex-col justify-center items-center max-w-3xl prose-sm lg:prose dark:prose-dark mx-12">
              <img
                className="w-24 lg:w-64 animate-wiggle hover:animate-spin"
                src="/docs-wip/assets/logos/small.png"
              />
              <h1>404: Not Found</h1>
              <h2>The page you are looking for does not exist. </h2>
              <p>
                If it should, please use the
                <span className="px-2 py-1 ml-2 text-gray-500 text-sm border border-gray-200 rounded-md hover:bg-gray-100 cursor-default">
                  Share Feedback
                </span>{" "}
                button at the top of this page to let us know
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

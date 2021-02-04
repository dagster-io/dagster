export default function Custom404() {
  return (
    <div className="h-(screen-16) w-full flex justify-center items-center">
      <div className="flex flex-col justify-center items-center max-w-3xl prose mx-12">
        <img
          className="animate-bounce"
          src="https://docs.dagster.io/assets/logos/small.png"
        />
        <h1>404: Not Found</h1>
        <h2>The page you are looking for does not exist. </h2>
        <p>
          If it should, please use the
          <span className="px-2 py-1 ml-2 text-gray-500 text-sm border border-gray-200 rounded-md hover:bg-gray-100">
            Share Feedback
          </span>{" "}
          button at the top of this page to let us know
        </p>
      </div>
    </div>
  );
}

import { useState } from "react";

// export default function Home() {
//   return (
//     <div className="flex items-center justify-center">
//       <Head>
//         <title>Dagster Documentation</title>
//         <link rel="icon" href="/favicon.ico" />
//       </Head>

//       <h1>Dagster Documentation</h1>
//     </div>
//   );
// }

const Modal = () => {
  return (
    <div className="fixed z-10 inset-0 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/*
  Background overlay, show/hide based on modal state.

  Entering: "ease-out duration-300"
  From: "opacity-0"
  To: "opacity-100"
  Leaving: "ease-in duration-200"
  From: "opacity-100"
  To: "opacity-0"
    */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" />
        </div>
        {/* This element is to trick the browser into centering the modal contents. */}
        <span
          className="hidden sm:inline-block sm:align-middle sm:h-screen"
          aria-hidden="true"
        >
          ​
        </span>
        {/*
  Modal panel, show/hide based on modal state.

  Entering: "ease-out duration-300"
  From: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
  To: "opacity-100 translate-y-0 sm:scale-100"
  Leaving: "ease-in duration-200"
  From: "opacity-100 translate-y-0 sm:scale-100"
  To: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
    */}
        <div
          className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-headline"
        >
          <div>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              {/* Heroicon name: check */}
              <svg
                className="h-6 w-6 text-green-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                ></path>
              </svg>
            </div>
            <div className="mt-3 sm:mt-5">
              <h3
                className="text-lg text-center leading-6 font-medium text-gray-900"
                id="modal-headline"
              >
                Try Dagster in your browser
              </h3>

              <img className="py-4" src="images/gitpod.png" />
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Try writing Dagster pipelines right in your browser using
                  Gitpod. You'll get an environment where you can write code and
                  interact with Dagit side-by-side.
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Note: You will need to login with Github to use the service.
                </p>
              </div>
            </div>
          </div>
          <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button
              type="button"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
            >
              Launch Gitpod
            </button>
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
            >
              Back to Docs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const codeSnippet = `from dagster import execute_pipeline, pipeline, solid

@solid
def get_name(_):
    return 'dagster'


@solid
def hello(context, name: str):
    context.log.info('Hello, {name}!'.format(name=name))


@pipeline
def hello_pipeline():
    hello(get_name())
`;

const ActionItems = ({ openModal }) => {
  return (
    <div className="my-12 grid gap-4 grid-cols-1 sm:grid-cols-3">
      <div className="bg-gradient-to-b from-purple-400 to-purple-500 px-6 py-8 rounded-xl">
        <div className="text-white font-bold">Start the tutorial</div>
        <div className="text-white text-sm my-4">
          New to Dagster? Learn all about the library in a short tutorial.
        </div>

        <a
          href="/tutorials"
          className="text-white text-sm inline-block mt-4 font-semibold px-3 py-2 rounded-md bg-purple-600"
        >
          Start learning
        </a>
      </div>
      <div className="bg-gradient-to-b from-blue-400 to-blue-500 px-6 py-8 rounded-xl">
        <div className="text-white font-bold">Try it in the browser</div>
        <div className="text-white text-sm my-4">
          Try Dagster and Dagit right now in your browser.
        </div>

        <button
          onClick={openModal}
          className="text-white text-sm inline-block mt-4 font-semibold px-3 py-2 rounded-md bg-blue-600"
        >
          Start building
        </button>
      </div>

      <div className="bg-gradient-to-b from-yellow-400 to-yellow-500 px-6 py-8 rounded-xl">
        <div className="text-white font-bold">Read the Docs</div>
        <div className="text-white text-sm my-4">
          Read the documentation to learn about how Dagster can work for you.
        </div>

        <a
          href="/tutorial"
          className="text-white text-sm inline-block mt-4 font-semibold px-3 py-2 rounded-md bg-yellow-600"
        >
          Start Reading
        </a>
      </div>
    </div>
  );
};

const Prose = ({ children }) => {
  return <div className="prose dark:prose-dark max-w-none">{children}</div>;
};

const Index = () => {
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  const openModal = () => {
    setModalOpen(true);
  };

  return (
    <>
      {modalOpen && <Modal />}
      <div
        className="flex-1 min-w-0 relative z-0 focus:outline-none pt-8"
        tabIndex={0}
      >
        {/* Start main area*/}
        <div className="py-6 px-4 sm:px-6 lg:px-8 w-full">
          <Prose>
            <h1>Getting Started With Dagster</h1>

            <h2>What is Dagster?</h2>

            <p>
              Dagster is a data orchestrator for machine learning, analytics,
              and ETL.
            </p>
          </Prose>

          <section className="text-gray-700 body-font">
            <div className="container  py-12 mx-auto flex flex-wrap">
              <div className="flex flex-wrap md:-m-2 -m-1">
                <div className="flex flex-wrap w-1/2">
                  <div className="md:p-2 p-1 w-1/2">
                    <img
                      alt="gallery"
                      className="w-full object-cover h-full object-center block"
                      src="/images/dagit-3.png"
                    />
                  </div>
                  <div className="md:p-2 p-1 w-1/2">
                    <img
                      alt="gallery"
                      className="w-full object-cover h-full object-center block"
                      src="/images/dagit-2.png"
                    />
                  </div>
                  <div className="md:p-2 p-1 w-full">
                    <img
                      alt="gallery"
                      className="w-full h-full object-cover object-center block"
                      src="/images/dagit-5.png"
                    />
                  </div>
                </div>
                <div className="flex flex-wrap w-1/2">
                  <div className="md:p-2 p-1 w-full">
                    <img
                      alt="gallery"
                      className="w-full h-full object-cover object-center block"
                      src="/images/dagit-1.png"
                    />
                  </div>
                  <div className="md:p-2 p-1 w-1/2">
                    <img
                      alt="gallery"
                      className="w-full object-cover h-full object-center block"
                      src="/images/dagit-5.png"
                    />
                  </div>
                  <div className="md:p-2 p-1 w-1/2">
                    <img
                      alt="gallery"
                      className="w-full object-cover h-full object-center block"
                      src="/images/dagit-2.png"
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          <Prose>
            <p>
              Dagster lets you define pipelines in terms of the data flow
              between reusable, logical components, then test locally and run
              anywhere. With a unified view of pipelines and the assets they
              produce, Dagster can schedule and orchestrate Pandas, Spark, SQL,
              or anything else that Python can invoke.
            </p>

            <p>
              Dagster is designed for data platform engineers, data engineers,
              and full-stack data scientists. Building a data platform with
              Dagster makes your stakeholders more independent and your systems
              more robust. Developing data pipelines with Dagster makes testing
              easier and deploying faster.
            </p>
          </Prose>

          <ActionItems openModal={openModal} />

          <Prose>
            <h2>Why should you use Dagster?</h2>
            <h3 id="develop-and-test-on-your-laptop-deploy-anywhere">
              Develop and test on your laptop, deploy anywhere
            </h3>
            <p>
              With Dagster’s pluggable execution, the same pipeline can run
              in-process against your local file system, or on a distributed
              work queue against your production data lake. You can set up
              Dagster’s web interface in a minute on your laptop, or deploy it
              on-premise or in any cloud.
            </p>
            <h3 id="model-and-type-the-data-produced-and-consumed-by-each-step">
              Model and type the data produced and consumed by each step
            </h3>
            <p>
              Dagster models data dependencies between steps in your
              orchestration graph and handles passing data between them.
              Optional typing on inputs and outputs helps catch bugs early.
            </p>
            <h3 id="link-data-to-computations">Link data to computations</h3>
            <p>
              Dagster’s Asset Manager tracks the data sets and ML models
              produced by your pipelines, so you can understand how your they
              were generated and trace issues when they don’t look how you
              expect.
            </p>
            <h3 id="build-a-self-service-data-platform">
              Build a self-service data platform
            </h3>
            <p>
              Dagster helps platform teams build systems for data practitioners.
              Pipelines are built from shared, reusable, configurable data
              processing and infrastructure components. Dagster’s web interface
              lets anyone inspect these objects and discover how to use them.
            </p>
            <h3 id="avoid-dependency-nightmares">
              Avoid dependency nightmares
            </h3>
            <p>
              Dagster’s repository model lets you isolate codebases, so that
              problems in one pipeline don’t bring down the rest. Each pipeline
              can have its own package dependencies and Python version.
              Pipelines run in isolated processes so user code issues can&#39;t
              bring the system down.
            </p>
            <h3 id="debug-pipelines-from-a-rich-ui">
              Debug pipelines from a rich UI
            </h3>
            <p>
              Dagit, Dagster’s web interface, includes expansive facilities for
              understanding the pipelines it orchestrates. When inspecting a
              pipeline run, you can query over logs, discover the most time
              consuming tasks via a Gantt chart, re-execute subsets of steps,
              and more.
            </p>
          </Prose>
        </div>
        {/* End main area */}
      </div>
      <aside className="hidden relative xl:block flex-none w-96 flex-shrink-0 border-gray-200">
        {/* Start secondary column (hidden on smaller screens) */}
        <div className="flex flex-col justify-between  sticky top-24  py-6 px-4 sm:px-6 lg:px-8">
          <div className="mb-8 border px-4 py-4 relative overflow-y-scroll max-h-(screen-60)">
            <div className="uppercase text-sm font-semibold text-gray-500">
              Quick Links
            </div>
            <div className="mt-6 prose dark:prose-dark">
              <ul>
                <li>
                  <a href="#">Go to Tutorial</a>
                </li>
                <li>
                  <a href="#">Go to Main Concepts</a>
                </li>
                <li>
                  <a href="#">Go to Examples</a>
                </li>
                <li>
                  <a href="#">Ask a question on Github</a>
                </li>
                <li>
                  <a href="#">Join us on Slack</a>
                </li>
              </ul>
            </div>
          </div>
        </div>
        {/* End secondary column */}
      </aside>
    </>
  );
};

export default Index;

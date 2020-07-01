import { NextPage } from 'next';
import { VersionedLink } from 'components/VersionedComponents';

const Index: NextPage<{ userAgent: string }> = () => (
  <>
    <div className="mt-10 mx-auto max-w-screen-xl px-4 sm:mt-12 sm:px-6 lg:mt-16">
      <div className="text-center">
        <div className="flex justify-center">
          <img
            className="w-1/2 sm:w-1/3 md:w-1/5 h-auto text-center h-full"
            src="https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png"
          />
        </div>
        <p className="mt-6 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-8 md:text-xl md:max-w-2xl">
          Dagster is a system for building modern data applications. Dagster
          provides an elegant programming model, UI tools, and programmatic APIs
          to enable infrastructure engineers, data engineers, and data
          scientists to collaborate on ETL/ELT, ML pipelines, building data
          applications, and more.
        </p>
        <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
          <div className="rounded-md shadow">
            <VersionedLink href="/tutorial">
              <a className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base leading-6 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:shadow-outline-blue transition duration-150 ease-in-out md:py-4 md:text-lg md:px-10">
                Tutorial
              </a>
            </VersionedLink>
          </div>
          <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
            <VersionedLink href="/install">
              <a className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base leading-6 font-medium rounded-md text-blue-600 bg-white hover:text-blue-500 focus:outline-none focus:shadow-outline-blue transition duration-150 ease-in-out md:py-4 md:text-lg md:px-10">
                Install
              </a>
            </VersionedLink>
          </div>
        </div>
      </div>
    </div>
    <div className="mt-8 py-12 bg-white">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:max-w-5xl lg:px-8">
        <div className="lg:grid lg:grid-cols-3 lg:gap-8">
          <div>
            <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
              <svg
                className="h-8 w-8 "
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
            </div>
            <div className="mt-5">
              <h5 className="text-lg leading-6 font-medium text-gray-900">
                Elegant Programming Model
              </h5>
              <p className="mt-2 text-base leading-6 text-gray-500">
                Dagster is a set of abstractions for building self-describing,
                testable, and reliable data applications. It embraces the
                principles of functional data programming; gradual, optional
                typing; and testability as a first-class value.
              </p>
            </div>
          </div>
          <div className="mt-10 lg:mt-0">
            <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
              <svg
                className="h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                />
              </svg>
            </div>
            <div className="mt-5">
              <h5 className="text-lg leading-6 font-medium text-gray-900">
                Beautiful Tools
              </h5>
              <p className="mt-2 text-base leading-6 text-gray-500">
                Dagster's development environment, dagit — designed for data
                engineers, machine learning engineers, data scientists — enables
                astoundingly productive local development.
              </p>
            </div>
          </div>
          <div className="mt-10 lg:mt-0">
            <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
              <svg
                className="h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div className="mt-5">
              <h5 className="text-lg leading-6 font-medium text-gray-900">
                Flexible and Incremental
              </h5>
              <p className="mt-2 text-base leading-6 text-gray-500">
                Dagster integrates with your existing tools and infrastructure.
                Dagster can invoke any computation — whether it be Spark, a
                Python, a Jupyter notebook, or SQL — and is designed to deploy
                to any workflow engine, such as Airflow.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </>
);

export default Index;

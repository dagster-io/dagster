// import { VersionedGithubLink } from 'components/VersionedComponents';

import { NextPage } from 'next';
import { GetStaticProps } from 'next';
import { VersionedGithubLink } from 'components/VersionedComponents';

const Modules: NextPage<{ body: string }> = (props) => {
  const body: any = props.body;

  return (
    <>
      <h1 className="text-lg font-bold">Examples</h1>
      <p className="text-sm py-4">
        This section contains examples of how to use Dagster. All examples can
        be found on <VersionedGithubLink filePath="examples" word="Github" />.
      </p>
      <div className="flex flex-col">
        <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="py-2 align-middle inline-block sm:px-6 lg:px-8">
            <div className="border overflow-hidden border-b border-gray-200 sm:rounded-lg">
              <table className="divide-y divide-gray-200 border border-rounded-md">
                <thead>
                  <tr>
                    <th className="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>

                    <th className="px-6 py-3 bg-gray-50" />
                  </tr>
                </thead>
                <tbody>
                  {body.map((example: any, i: number) => (
                    <tr className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 text-sm leading-5 font-medium text-gray-900">
                        {example.title}
                      </td>
                      <td className="px-6 py-4 text-sm leading-5 text-gray-500">
                        {example.description}
                      </td>

                      <td className="px-6 py-4 whitespace-no-wrap text-right text-sm leading-5 font-medium">
                        <a
                          href={`/examples/${example.name}`}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Open
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const data = await import('./examples.json');
  return {
    props: {
      body: data.default,
    },
  };
};

export default Modules;

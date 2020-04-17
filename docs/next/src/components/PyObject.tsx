import data from 'data/searchindex.json';
import { VersionedLink } from './VersionedComponents';

const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  displayText?: string;
}> = ({ module, object, displayText }) => {
  const objects = data.objects as any;
  const moduleObjects = objects[module];
  const objectData = moduleObjects && moduleObjects[object];

  // This is just to supress errors for now. Once we switch over to this site,
  // we shoud throw an error here. That will make sure we don't have docs
  // that link to objects that don't exist anymore.
  if (!moduleObjects || !objectData) {
    return (
      <VersionedLink href="#">
        <a>
          <code className="text-red-800">Invalid: {displayText || object}</code>
        </a>
      </VersionedLink>
    );
  }

  const fileIndex = objectData[0];
  // TODO: Make sure to use the hashOverride when it's defined
  // const hashOverride = objectData[3];
  const doc = data.docnames[fileIndex];
  const link = doc.replace('sections/api/apidocs/', '/docs/apidocs/');
  return (
    <VersionedLink href={link + '#' + module + '.' + object}>
      <a>
        <code>{displayText || object}</code>
      </a>
    </VersionedLink>
  );
};

export default PyObject;

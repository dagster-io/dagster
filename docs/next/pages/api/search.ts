import {NextApiRequest, NextApiResponse} from 'next';

const searchURI = process.env.SWIFTYPE_SEARCH_URI;
const engineKey = process.env.SWIFTYPE_ENGINE_KEY;
const maxQueryLength = parseInt(process.env.SWIFTYPE_MAX_QUERY_LENGTH, 10);

export default async function handler(request: NextApiRequest, response: NextApiResponse) {
  const {method} = request;
  if (method !== 'POST') {
    return response.status(400).json({data: 'Invalid request.'});
  }

  const {body} = request;
  const query = `${body?.query || ''}`.trim().slice(0, maxQueryLength).toLowerCase();

  if (!query) {
    return response.status(400).json({data: 'Invalid query.'});
  }

  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      engine_key: engineKey,
      q: query,
    }),
  };

  const searchResponse = await fetch(searchURI, options);
  const searchJSON = await searchResponse.json();

  response.status(200).json({
    query,
    records: searchJSON.records,
  });
}

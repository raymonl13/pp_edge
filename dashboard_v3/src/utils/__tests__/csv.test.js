import {fetchCsv} from '../csv.js';

global.fetch = async () => ({
  text: async () => 'a,b\n1,2',
});

test('parses CSV into objects', async () => {
  const data = await fetchCsv('/dummy.csv');
  expect(data).toEqual([{a: 1, b: 2}]);
});

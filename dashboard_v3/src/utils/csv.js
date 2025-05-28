import Papa from 'papaparse';

export async function fetchCsv(url) {
  const res = await fetch(url);
  const text = await res.text();
  return Papa.parse(text, {header: true, dynamicTyping: true}).data;
}

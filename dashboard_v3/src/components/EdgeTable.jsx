import React, { useEffect, useState } from 'react';

const safeParse = s => { try { return safeParse(s ?? "[]"); } catch { return []; } };
import { fetchCsv } from '../utils/csv.js';
import SparkLine from './SparkLine.jsx';

export default function EdgeTable() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    fetchCsv('/edge_sheet_sample.csv').then(setRows);
  }, []);

  return (
    <table className="min-w-full border">
      <thead>
        <tr>
          <th className="p-2 border">Player</th>
          <th className="p-2 border text-right">Edge %</th>
          <th className="p-2 border">Spark</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const sparkVals =
            Array.isArray(r.spark) ? r.spark : safeParse(r.spark);
          return (
            <tr key={r.player}>
              <td className="p-2 border">{r.player}</td>
              <td className="p-2 border text-right">{r.edge}</td>
              <td className="p-2 border">
                <SparkLine values={sparkVals} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

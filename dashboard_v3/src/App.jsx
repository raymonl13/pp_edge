import React from 'react';
import EdgeTable from './components/EdgeTable.jsx';
export default function App(){
  return(
    <div className="p-4 font-sans">
      <h1 className="text-2xl font-bold mb-4">PP-EDGE Dashboard v3</h1>
      <EdgeTable/>
    </div>
  );
}

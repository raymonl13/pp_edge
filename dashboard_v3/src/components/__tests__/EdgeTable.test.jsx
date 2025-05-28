import { render, screen } from '@testing-library/react';
import EdgeTable from '../EdgeTable.jsx';

test('renders stub players A and B', async () => {
  render(<EdgeTable />);
  expect(await screen.findByText('A')).toBeInTheDocument();
  expect(await screen.findByText('B')).toBeInTheDocument();
});

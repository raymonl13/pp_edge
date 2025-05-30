import { render, screen, waitFor } from '@testing-library/react'
import { ApiProvider } from '../../api'
import EdgeTable from '../EdgeTable'

const fake = [{ player:'Alice', edge:0.23, spark:0.5 }]
const mockApi = { get: () => Promise.resolve({ data: fake }) }

test('EdgeTable loads and shows API data', async () => {
  render(
    <ApiProvider value={mockApi}>
      <EdgeTable />
    </ApiProvider>
  )
  await waitFor(() => expect(screen.getByText('Alice')).toBeInTheDocument())
  expect(screen.getAllByRole('row')).toHaveLength(fake.length + 1)
})

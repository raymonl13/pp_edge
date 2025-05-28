import {render} from '@testing-library/react';
import SparkLine from '../SparkLine.jsx';

test('renders SVG polyline', () => {
  const {container} = render(<SparkLine values={[0, 5, 10]} />);
  expect(container.querySelector('polyline')).toBeInTheDocument();
});

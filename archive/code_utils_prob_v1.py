
def bayes_hit_prob(leg: dict) -> float:
    """Mini helper for M3 smoke-tests."""
    return {'Hits':0.63, 'HR':0.11}.get(leg.get('stat'), 0.5)

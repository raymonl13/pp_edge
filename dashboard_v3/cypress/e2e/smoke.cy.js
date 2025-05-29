describe('Dashboard smoke', () => {
  it('loads table', () => {
    cy.visit('/')
    cy.contains('PP-EDGE Dashboard v3')
    cy.get('table tbody tr').should('have.length.greaterThan', 0)
  })
})

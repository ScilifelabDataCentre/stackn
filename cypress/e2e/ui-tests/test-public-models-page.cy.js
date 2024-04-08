describe("Test of the public models page", () => {

    beforeEach(() => {

        cy.visit("/models/")
    })

    it("should contain header with text Model cards", () => {

        cy.get('h3').should('contain', 'Model cards')
        cy.get("title").should("have.text", "Models | SciLifeLab Serve (beta)")
    })

    it("should contain text about no public models", () => {

        cy.get('p').should('contain', 'No public model cards available.')
    })

})
describe("Test sign up", () => {

    let userdata

    beforeEach(() => {
        // reset and seed the database prior to every test
        if (Cypress.env('do_reset_db') === true) {
            cy.log("Resetting db state. Running db-reset.sh");
            cy.exec("./cypress/e2e/db-reset.sh");
            cy.wait(60000);
        }
        else {
            cy.log("Skipping resetting the db state.");
        }
    })

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.fixture('users.json').then(function (data) {
            userdata = data.login;
          })
    })

    it("should create new user account with valid form input", () => {

        cy.visit("/signup/");
        cy.get("title").should("have.text", "Register | SciLifeLab Serve")

        cy.get('input[name=email]').type(userdata.email);
        cy.get('input[name=first_name]').type("first name");
        cy.get('input[name=last_name]').type("last name");
        cy.get('input[name=password1]').type(userdata.password);
        cy.get('input[name=password2]').type(userdata.password);
        cy.get('input[name="department"]').click().click();
        cy.get('input[name="department"]').type('Biology Education Centre');
        
        cy.get("input#submit-id-save").click();

        cy.url().should("include", "accounts/login");
        cy.get('.alert-success').should('contain', 'Account created successfully!');
    })
})

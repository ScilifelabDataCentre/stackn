describe("Test contributor user functionality", () => {

    // TODO: share logged in session across tests

    // username here must match username in db-seed-contributor.sh
    const username = "e2e_tests_contributor_tester"
    const pwd = "test12345"

    // Names of objects to create
    const project_name = "Project e2e blank";
    const volume_name = "e2e-project-vol";

    before(() => {
        // seed the db with: contributor user, a blank project
        cy.log("Seeding the db for the contributor tests. Running db-seed-contributor.sh");
        cy.exec("./cypress/e2e/db-seed-contributor.sh");
    })

    it("can create a new blank project", () => {
        // First login as the test user
        cy.visit("accounts/login/");

        cy.get('input[name=username]').type(username);
        cy.get('input[name=password]').type(pwd);

        cy.get("button").contains('Login').click();

        cy.url().should("include", "projects");
        cy.get('h3').should('contain', 'Projects');

        // Next click button for UI to create a new project
        cy.get("a").contains('New project').click();
        cy.url().should("include", "projects/templates");
        cy.get('h3').should('contain', 'New project');

        // Next click button to create a new blank project
        cy.get("a").contains('Create').first().click();
        cy.url().should("include", "projects/create?template=");
        cy.get('h3').should('contain', 'New project');
        
        // Fill in the options for creating a new blank project
        cy.get('input[name=name]').type(project_name);
        cy.get('textarea[name=description]').type("A test project created by an e2e test.");
        cy.get("button").contains('Create project').click();
        cy.url().should("include", "/project-e2e-blank");
        cy.get('h3').should('contain', 'Overview');
    })
  
    it("can create a new mlflow project", () => {
    })

    it("can delete a project", () => {
    })
})
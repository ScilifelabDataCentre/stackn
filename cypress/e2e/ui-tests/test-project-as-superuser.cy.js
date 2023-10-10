describe("Test superuser access", () => {

    // Tests performed as an authenticated user that has superuser privileges
    // user: admin

    let users

    before(() => {
        // seed the db with: superuser user, a blank project
        cy.log("Seeding the db for the superuser tests. Running db-seed-contributor.sh");
        cy.exec("./cypress/e2e/db-reset.sh")
        cy.wait(60000)
        cy.visit("/")
        cy.log("Running seed_superuser.py")
        cy.exec("./cypress/e2e/db-seed-superuser.sh")
    })

    beforeEach(() => {
        // username in fixture must match username in db-reset.sh
        cy.log("Logging in as superuser")
        cy.fixture('users.json').then(function (data) {
            users = data

            cy.loginViaApi(users.superuser.username, users.superuser.password)
        })
    })

    it.skip("can see extra deployment options and extra settings in a project", () => {
    })

    // this test is just copied from what we had in contributor tests, not sure it works.
    it.skip("can create a persistent volume", () => {
        // Names of objects to create
        const project_name = "e2e-create-proj-test"
        const volume_name = "e2e-project-vol"
        const project_title_name = project_name + " | SciLifeLab Serve"
        const createResources = Cypress.env('create_resources');

        if (createResources === 'true') {

            cy.visit("/projects/")
            cy.get('div.card-body:contains("' + project_name + '")').find('a:contains("Open")').first().click()
            cy.get('div.card-body:contains("Persistent Volume")').find('a:contains("Create")').click()

            cy.get('input[name=app_name]').type(volume_name)
            cy.get('button').contains('Create').click()
            cy.get('span').should('contain', 'Installed')
            cy.get('tbody:contains("Persistent Volume")').find('i.bi-three-dots-vertical').click()
            cy.get('tbody:contains("Persistent Volume")').find('a.confirm-delete').click()
            cy.get('button').contains('Delete').click()

            cy.get('tbody:contains("Persistent Volume")').find('span').should('contain', 'Terminated')
            cy.get('tbody:contains("Persistent Volume")').find('span').should('contain', 'Deleted')

          } else {
            cy.log('Skipped because create_resources is not true');
          }

    })

    it.skip("can bypass N projects limit", () => {
    })

    it.skip("can bypass N apps limit", () => {
    })

})
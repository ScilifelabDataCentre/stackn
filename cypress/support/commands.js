// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('loginViaUI', (username, password) => {
    cy.session(
      username,
      () => {
        cy.visit('/accounts/login/')
        cy.get('input[name=username]').type(username)
        cy.get('input[name=password]').type(`${password}{enter}`, { log: false })
        cy.url().should('include', '/projects')
        cy.get('h3').should('contain', 'My projects')
      },
      {
        validate: () => {
          cy.getCookie('sessionid').should('exist')
          cy.getCookie('csrftoken').should('exist')
        },
      }
    )
  })

Cypress.Commands.add('loginViaApi', (username, password) => {

    const relurl = "/accounts/login/"

    cy.session(
      username,
      () => {
        cy.visit(relurl)

        cy.get("[name=csrfmiddlewaretoken]")
        .should("exist")
        .should("have.attr", "value")
        .as("csrfToken");

        cy.get("@csrfToken").then((token) => {
            cy.request({
              method: "POST",
              url: relurl,
              form: true,
              body: {
                username: username,
                password: password,
              },
              headers: {
                "X-CSRFTOKEN": token,
              },
            });
          });
      },
      {
        validate: () => {
          cy.getCookie('sessionid').should('exist')
          cy.getCookie('csrftoken').should('exist')
        },
      }
    )
  })


Cypress.Commands.add('createBlankProject', (project_name) => {

  cy.visit("/projects/")

  // Click button for UI to create a new project
  cy.get("a").contains('New project').click()
  cy.get('h3').should('contain', 'New project')

  // Next click button to create a new blank project
  cy.get("a").contains('Create').first().click()
  cy.get('h3').should('contain', 'New project')

  // Fill in the options for creating a new blank project
  cy.get('input[name=name]').type(project_name)
  cy.get('textarea[name=description]').type("A test project created by an e2e test.")
  cy.get("input[name=save]").contains('Create project').click()
  
})
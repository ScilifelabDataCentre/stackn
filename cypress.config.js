const { defineConfig } = require("cypress");

module.exports = defineConfig({
  env: {
    do_reset_db: false,
    wait_db_reset: 60000,
    create_resources: true,
  },

  e2e: {
    baseUrl: 'http://studio.130.238.178.6.nip.io:8080',
    //baseUrl: 'https://serve-dev.scilifelab.se',
    experimentalSessionAndOrigin: true,

    setupNodeEvents(on, config) {
      // implement node event listeners here
      const logOptions = {
        printLogsToConsole: 'always',
      };

      require('cypress-terminal-report/src/installLogsPrinter')(on, logOptions);
    },
  },
});

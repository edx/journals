// Karma configuration
var webdriver = require('selenium-webdriver');
var firefox = require('selenium-webdriver/firefox');


module.exports = function(config) {
    const coveragePath = 'journals/apps/journals/static/js/!(spec|lib)/**/*.js';
    var preprocessors = {};

    preprocessors[coveragePath] = ['coverage'];

    config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browse
    // for loading files with requirejs follow this doc http://karma-runner.github.io/latest/plus/requirejs.html
	files: [
      'journals/apps/journals/static/js/spec/**/*.js'
    ],

    // list of files to exclude
    exclude: [],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    //preprocessors: preprocessors,

    // enabled plugins
    plugins:[
       'karma-jasmine-jquery',
       'karma-jasmine',
       'karma-requirejs',
       'karma-firefox-launcher',
       'karma-chrome-launcher',
       'karma-selenium-webdriver-launcher',
       'karma-coverage-allsources',
       'karma-coverage',
       'karma-spec-reporter',
       'karma-sinon'
   ],

    // Karma coverage config
    coverageReporter: {
        include: coveragePath,
        instrumenterOptions: {
            istanbul: { noCompact: true }
        },
        reporters: [
            {type: 'text'},
            {type: 'lcov', subdir: 'test_root/reports/report-lcov'},
            {type: 'html', subdir: 'test_root/reports/report-html'}
        ]
    },

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['spec', 'coverage-allsources', 'coverage'],

    // web server port
    port: 13876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_DEBUG,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,

    customLaunchers: {
        // Firefox configuration that doesn't perform auto-updates
        FirefoxNoUpdates: {
            base: 'Firefox',
            prefs: {
                'app.update.auto': false,
                'app.update.enabled': false
            }
        },
        ChromeDocker: {
            base: 'SeleniumWebdriver',
            browserName: 'chrome',
            getDriver: function () {
                return new webdriver.Builder()
                    .forBrowser('chrome')
                    .usingServer('http://edx.devstack.chrome:4444/wd/hub')
                    .build();
            }
        },
        FirefoxDocker: {
            base: 'SeleniumWebdriver',
            browserName: 'firefox',
            getDriver: function () {
                var options = new firefox.Options(),
                    profile = new firefox.Profile();
                profile.setPreference('focusmanager.testmode', true);
                options.setProfile(profile);
                return new webdriver.Builder()
                    .forBrowser('firefox')
                    .usingServer('http://edx.devstack.firefox:4444/wd/hub')
                    .setFirefoxOptions(options)
                    .withCapabilities({'browserName': 'firefox', acceptSslCerts: true, acceptInsecureCerts: true})
                    .build();
            }
        }
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true
  })
}

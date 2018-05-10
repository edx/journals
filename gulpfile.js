var gulp = require('gulp'),
    eslint = require('gulp-eslint'),
    argv = require('yargs').array('browsers').argv,
    KarmaServer = require('karma').Server,
    path = require('path');

(function() {
    'use strict';

    var paths = {
        spec: [
            'journals/static/js/spec/**/*.js',
            'journals/apps/journals/static/js/spec/**/*.js'
        ],
        lint: [
            'gulpfile.js',
            'journals/static/js/**/*.js',
            'journals/apps/journals/static/js/*.js',
            'journals/apps/journals/static/js/**/*.js'
        ],
        karamaConf: 'karma.conf.js'
    };

/**
 * Runs the JS unit tests
 */
    gulp.task('test', function(cb) {
        new KarmaServer({
            configFile: path.resolve('karma.conf.js'),
            hostname: argv.hostname,
            browsers: argv.browsers,
            singleRun: argv.singleRun
        }, cb).start();
    });

/**
 * Runs the ESLint linter.
 *
 * http://eslint.org/docs/about/
 */
    gulp.task('lint', function() {
        return gulp.src(paths.lint)
        .pipe(eslint())
        .pipe(eslint.format())
        .pipe(eslint.failAfterError());
    });

/**
 * Monitors the source and test files, running tests
 * and linters when changes detected.
 */
    gulp.task('watch', function() {
        gulp.watch(paths.spec, ['test', 'lint']);
    });

    gulp.task('default', ['test']);
}());

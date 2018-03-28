journals  |Travis|_ |Codecov|_
===================================================
.. |Travis| image:: https://travis-ci.org/edx/journals.svg?branch=master
.. _Travis: https://travis-ci.org/edx/journals

.. |Codecov| image:: http://codecov.io/github/edx/journals/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/edx/journals?branch=master

The ``README.rst`` file should start with a brief description of the repository, which sets it in the context of other repositories under the ``edx`` organization. It should make clear where this fits in to the overall edX codebase. You may also want to provide a brief overview of the code in this repository, including the main components and useful entry points for starting to understand the code in more detail, or link to a comparable description in your repo's docs.

Documentation
-------------
.. |ReadtheDocs| image:: https://readthedocs.org/projects/journals/badge/?version=latest
.. _ReadtheDocs: http://journals.readthedocs.io/en/latest/

`Documentation <https://journals.readthedocs.io/en/latest/>`_ is hosted on Read the Docs. The source is hosted in this repo's `docs <https://github.com/edx/journals/tree/master/docs>`_ directory. To contribute, please open a PR against this repo.

License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the LICENSE_ file for details.

.. _LICENSE: https://github.com/edx/journals/blob/master/LICENSE

How To Contribute
-----------------

Contributions are welcome. Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details. Even though it was written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Get Help
--------

Ask questions and discuss this project on `Slack <https://openedx.slack.com/messages/general/>`_ or in the `edx-code Google Group <https://groups.google.com/forum/#!forum/edx-code>`_.

Getting Started
---------------

Running in Docker
~~~~~~~~~~~~~~~~~
To get started, please complete the following steps:

1. Configure edx OIDC
    1. Create OAuth client in LMS
        1. Go to LMS Admin http://localhost:18000/admin/oauth2/client/
        2. Click the `Add client` button.
        3. Leave the user field blank.
        4. Specify the name of this service, ``journals``, as the client name.
        5. Set the `URL` to the root path of this service: ``http://localhost:18606/``.
        6. Set the `Redirect URL` to the OIDC client endpoint: ``http://localhost:18606/complete/edx-oidc/``.
        7. Copy the `Client ID` and `Client Secret` values. They will be used later in `journals/settings/local.py`.
        8. Select `Confidential (Web applications)` as the client type.
        9. Click `Save`.
    2. Trust OAuth client in LMS
        1. Go to http://localhost:18000/admin/edx_oauth2_provider/trustedclient/add/
        2. Select your newly-created client's redirect URL from the dropdown.
        3. Click ``Save``.
2. Create a Site Configuration
    1. Go to http://localhost:18606/admin/core/siteconfiguration/add/
    2. Set site to be your default site
    3. Set `LMS base url` to `http://edx.devstack.lms:18000`
    4. Set `LMS public base url` to `http://localhost:18000`
    5. Set `OAuth settings` to the following JSON::
        {
            "SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY":"<<Client Secret generated from above>>",
            "SOCIAL_AUTH_EDX_OIDC_URL_ROOT":"http://edx.devstack.lms:18000/oauth2",
            "SOCIAL_AUTH_EDX_OIDC_ISSUERS":["http://edx.devstack.lms:18000"],
            "SOCIAL_AUTH_EDX_OIDC_KEY":"<<Client ID generated from above>>",
            "SOCIAL_AUTH_EDX_OIDC_SECRET":"<<Client Secret generated from above>>",
            "SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT": "http://localhost:18000/oauth2",
            "SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL":"http://localhost:18000/logout",
            "SOCIAL_AUTH_EDX_OIDC_ISSUER":"http://edx.devstack.lms:18000/oauth2"
        }
3. Initialize envionrment
    1. Run `make dev.init`. This should create your containers, migrate your databases, and build your elastic search indexes.

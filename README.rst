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
            1. Credentials: edx/edx
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
    3. Edit your local journals settings file
        1. Set the following values in `journals/settings/local.py`:
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | Setting                                             | Description                                                                | Value                                                                    |
            +=====================================================+============================================================================+==========================================================================+
            | SOCIAL_AUTH_EDX_OIDC_KEY                            | OAuth 2.0 client key                                                       | (This should be set to the value of "Client id" generated from above)    |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_SECRET                         | OAuth 2.0 client secret                                                    | (This should be set to the value of "Client secret" generated from above)|
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_URL_ROOT                       | OAuth 2.0 authentication URL                                               | http://edx.devstack.lms:18000/oauth2                                     |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT                | OAuth 2.0 public authentication URL                                        | http://localhost:18000/oauth2                                            |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL                     | OAuth 2.0 logout URL                                                       | http://localhost:18000/logout                                            |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY        | OIDC ID token decryption key. This value is used to validate the ID token. | (This should be the same value as SOCIAL_AUTH_EDX_OIDC_SECRET.)          |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_EDX_OIDC_ISSUER                         | OIDC ID issuer.                                                            | http://edx.devstack.lms:18000/oauth2                                     |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
            | SOCIAL_AUTH_REDIRECT_IS_HTTPS                       | Determines whether Auth is forced over SSL                                 | False                                                                    |
            +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+

2. Initialize envionrment
    1. Run `make dev.init`. This should create your containers, migrate your databases, and build your elastic search indexes.

3. Set up connection with LMS
    1. Enabled API Admin
        1. Go to http://localhost:18000/admin/api_admin/apiaccessconfig/
        2. Add a new item where enabled is checked true and save
    2. Get a Client ID and Secret from LMS
        1. Login to LMS (http://localhost:18000/login)
        2. Go to http://localhost:18000/api-admin
        3. Enter the requested fields (can be whatever) and click "Request API Access"
        4. Go to http://localhost:18000/admin/api_admin/apiaccessrequest/ and find the request tied to that user
        5. Change the status of the request to "Approved"
        6. Go to http://localhost:18000/api-admin/status/ to get your ID and Secret
    3. Set the following values in `journals/settings/local.py`:
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | Setting                                             | Description                                                                | Value                                                                    |
        +=====================================================+============================================================================+==========================================================================+
        | LMS_BASE_INTERNAL_URL                               | URL to internal devstack LMS                                               | Probably "http://edx.devstack.lms:18000"                                 |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | LMS_EXTERNAL_DOMAIN                                 | URL to external devstack LMS                                               | Probably "http://localhost:18000"                                        |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | LMS_CLIENT_ID                                       | Client ID generated from Api-Admin request above                           | Alphanumeric string                                                      |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | LMS_CLIENT_SECRET                                   | Client Secret generated from Api-Admin request above                       | Alphanumeric string                                                      |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | LMS_BLOCK_API_PATH                                  | Location of course blocks api                                              | Probably "/api/courses/v1/blocks/"                                       |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+
        | DEFAULT_VIDEO_COURSE_RUN_ID                         | Course run ID that you want videos to be pulled from                       | For Demo course in Devstack "course-v1:edX%2BDemoX%2BDemo_Course"        |
        +-----------------------------------------------------+----------------------------------------------------------------------------+--------------------------------------------------------------------------+

journals  |Travis|_ |Codecov|_
===================================================
.. |Travis| image:: https://travis-ci.org/edx/journals.svg?branch=master
.. _Travis: https://travis-ci.org/edx/journals

.. |Codecov| image:: http://codecov.io/github/edx/journals/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/edx/journals?branch=master

The Journal service is a standalone IDA that provides functionality to author, market and view Content Journals. This repository contains the needed code to support the base Journal functionality. It uses the Content Mangement System, Wagtail, to create and author Journals.

Additional edX Platform modules are being developed to allow the Journal to be integrated into the edX platform. These include modules for Ecommerce (to support purchasing journals), and LMS/Discovery (to support surfacing and interacting with journals). The integration modules can be found in the following repositories:

-  edx-platform: https://github.com/edx/edx-platform/tree/whitelabel/journal
-  course-discovery: https://github.com/edx/course-discovery/tree/whitelabel/journal
-  ecommerce: https://github.com/edx/ecommerce/tree/whitelabel/journal

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

Getting Started
---------------
Journal currently runs in it’s own docker environment. For development, it is dependent on the edx-platform which also runs in it’s own docker environment. Initial setup is necessary to configure both environments such that they can communicate with each other.

edx-platform configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Get edx-platform docker devstack up and running.
   
   -  ``git clone https://github.com/edx/devstack.git; git checkout whitelabel/journals``
   -  Then follow instructions found here to configure: https://github.com/edx/devstack/blob/master/README.rst

2. Verify that edx-platform is working correctly. Visit http://localhost:18000 and make sure you can login

3. Install whitelabel/journal branches for the following three services in the directories where devstack is configured to look:

   -  LMS: ``cd ~/projects/edx-platform; git checkout whitelabel/journals``
   -  Discovery: ``cd ~/projects/course-discovery; git checkout whitelabel/journals``
   -  Ecommerce: ``cd ~/projects/ecommerce; git checkout whitelabel/journals``

4. Restart the services: ``docker-compose restart``

Journal Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Run ``make dev.destroy`` to destroy previous setup and start from scratch

2. Run ``make dev.provision`` to setup all necessary configuration in Journals and edx-platform and create ‘Demo Journal’ 

3. Verify Journal is running by going to http://localhost:18606. You should see “edx Index” page by default showing one Journal “Demo Journal”

4. To edit the Demo Journal, first login as ``username:staff@example.com`` ``password:edx``, then click the CMS link in the header. This will bring you into Wagtail CMS environment. 
sdfasdfasdf

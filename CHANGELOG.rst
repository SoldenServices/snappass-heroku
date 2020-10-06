Connor Group Changes (10-07-2020)
----------------------------------
* use python-environ to create settings from .env file or environment variables
* use Flask_S3 for serving static files from S3 / CloudFront in production
* use the flask-debugtoolbar in development
* minor template changes for branding


Version 1.5.0 (in development)
------------------------------
* The ``URL_PREFIX`` environment variable can be used to add a prefix to URLs,
  which is useful when running behind a reverse proxy like nginx.
* Replaced mockredis with fakeredis in the unit test environment.
* Added support for Python 3.8.

Version 1.4.2
-------------
 * Various minor README and documentation improvements
 * Upgrade to Jinja 2.10.1
 * Fix autocomplete bug where hitting "back" would allow to autocomplete the password

Version 1.4.1
-------------
 * Switch to local (non-CDN) Font Awesome assets
 * Upgraded cryptography to 2.3.1 (for CVE-2018-10903, although snappass is
   unaffected because it doesn't use the vulnerable ``finalize_with_tag`` API)

Version 1.4.0
-------------
*You will lose stored passwords during the upgrade to this version*
 * Added a prefix in redis in front of the storage keys, making the redis safer to share with other applications
 * Small test and syntax improvements
 * Changing versioning number to match Pinterest's master versioning for sanity.

Prior modifications
-------------
* Added better 404 handling.
* Added filtering of additional user-agents.
* Removed Docker-related files.

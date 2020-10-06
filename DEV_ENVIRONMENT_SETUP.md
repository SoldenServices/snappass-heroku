## Development Environment Setup

- Create a virtualenv
- Install packages from `dev-requirements.txt` and `requirements.txt`
- Add a `.env` file in the snappass directory and set variables for
  *  `SECRET_KEY`
      * Used to sign cookies and other cryptographic operations
  * `DEBUG`
      * Toggles the flask debug toolbar on and off
  * `MOCK_REDIS`
      * For tests and running locally without a real Redis database
  * `USE_S3`
      * Toggle Flask_S3 on and off
  * `S3_BUCKET_NAME`
      * The S3 bucket name to use with Flask_S3
  * `USE_CDN`
      * toggle changing FQDN that Flask_S3 uses to generate urls.  Used with `USE_S3`
  * `CDN_DOMAIN`
      *  the FQDN for Flask_S3 to use to generate urls. 


## Using S3 for static files

The crude `s3_upload.py` script is meant to be used to upload contents of the `static` directory to
the S3 bucket specified in the `.env` file.  This only needs to be done if static files change.  The 
headers need to be set on the files uploaded to S3 so the `Content-Type` is set properly.
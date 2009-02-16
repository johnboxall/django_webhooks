"""
A script which delivers all unprocessed webhooks.

This is intended to be run as a cron job. Add the following to your crontab:

    DJANGO_SETTINGS_MODULE=yoursite.settings
    */15 * * * * python /path/to/webhooks/bin/process.py

"""
from webhooks import webhooks
webhooks.process()
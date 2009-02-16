Django WebHooks
===============

About
-----

> Web Hooks is an open initiative to standardize event notifications between web services by subscribing to URLs.

Django WebHooks makes it easy to integrate WebHooks into your Django Project.


Using Django Webhooks
---------------------

1. Download the code from GitHub:

        git clone git://github.com/johnboxall/django-webhooks.git webhooks
    
1. Edit `settings.py` and add  `webhooks` to your `INSTALLED_APPS`:

        # settings.py
        ...
        INSTALLED_APPS = (... 'webhooks', ...)
        
1. Register webhooks for models - `admin.py` is a good place:

        # admin.py

        from webhooks import webhooks

        webhooks.register(MyModel, ["fields", "to", "serialize"])

1. Create Listeners for the webhook. For example to create a Listener that will be messaged whenever a `User` instance with `username="john"` is saved:

        from django.contrib.auth.models import User
        from django.contrib.contenttypes.models import ContentType
        from webhooks.models import Listener

        user_type = ContentType.objects.get(app_label="auth", model="user")
        john = User.objects.get(username="john")
        
        Listener.create(obj_type=user_type,
                        obj_property="username",
                        obj_value="john",
                        url="http://where.john/is/listening/",
                        owner=john)

1. Profit.


Creating a Webhook Endpoint
---------------------------

1. **Django:**

        # views.py
        import simplejson
        
        def listener(request):
            json = request.raw_post_data
            webhook = simplejson.loads(json)


1. **PHP:**

        <?php
    
        // http://ca3.php.net/manual/en/reserved.variables.httprawpostdata.php
        // http://ca3.php.net/manual/en/wrappers.php.php
        $json = file_get_contents('php://input');
    
        // http://ca3.php.net/manual/en/function.json-decode.php
        var_dump(json_decode($json, true));
    
        ?>
    

Details
-------

1. HTTP POST request / raw_post_data
1. Creating a listener ...
1. ...    


ToDo
----

1. Code in `webhooks.models.Message` should be moved into `webhooks.helpers` so it can be subclassed / overridden more easily.
1. Add HMAC authorization headers to all Webhooks messages ([http://code.google.com/p/support/wiki/PostCommitWebHooks](see Google Code implementation)
1. Add verify view for (think PayPal IPN)


Resources
---------

* http://blog.webhooks.org/
* http://blogrium.com/2006/12/27/automator-for-the-web/
* http://blogrium.com/2006/11/27/lets-make-seeking-bliss-easier/
* http://blogrium.com/?p=70
* http://www.slideshare.net/progrium/web-hooks Web-Hooks by blogrium.com / superhappydevhouse
* http://groups.google.com/group/webhooks/ webhooks google group
* http://code.google.com/p/support/wiki/PostCommitWebHooks
* http://www.slideshare.net/progrium/web-hooks-and-the-programmable-world-of-tomorrow-presentation
* http://github.com/guides/post-receive-hooks
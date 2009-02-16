import socket
import urllib
import urlparse
import datetime

from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType


TIMEOUT = 3

class CreatedUpdatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Message(CreatedUpdatedModel):
    """
    A Message is sent when a WebHook is activated.
    
    """
    obj_type = models.ForeignKey('contenttypes.ContentType', help_text="Content type of the object of the message.")
    obj_id = models.PositiveIntegerField(help_text="ID of the object of the message.")
    obj = generic.GenericForeignKey("obj_type", "obj_id")
    payload = models.TextField(blank=True, help_text="Content of the message.")
    digest = models.CharField(blank=True, max_length=256, help_text="Hexdigest of the message's payload. Used to verify postbacks.")
    processed = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.obj)
        
    def process(self, hook):
        """
        If anyone is listening to this message then deliver it to them. Otherwise delete it.
        
        """
        if self.has_listeners():
            self.serialize(hook.fields, hook.serializer)
            self.deliver()
            self.processed = True
            self.save()
        else:
            self.delete()

    def deliver(self):
        """
        Deliver this message to each Listener by creating a MessageQueue instance and delivering it.
        
        """
        for listener in self.listeners:
            MessageQueue.objects.create(message=self, listener=listener).process()
            
    def serialize(self, fields, serializer, **kwargs):
        """
        Serialize obj using fields and serializer.
        
        """
        # ### TODO: Could use a hasher to calculate a message hash here.
        self.payload = serializer.serialize([self.obj], fields=fields, **kwargs)

    @property
    def listeners(self):
        """
        Return a QuerySet of Listeners for this message.
        
        Strategy:
          1. Look at all the Listeners looking at this model and see what properties they are watching.
          2. Look for all Listeners which have property values equal to the 
        
        """                
        if not hasattr(self, '_listeners_cache'):
            props = Listener.objects.filter(obj_type=self.obj_type).values_list("obj_property", flat=True).distinct()
            if len(props):
                filter_listeners_query = None
                for property_name in props:
                    query_property_value = {"obj_value": getattr(self.obj, property_name)}
                    query_property_name = {"obj_property": property_name}
                    query = models.Q(**query_property_value) & models.Q(**query_property_name)
                    if filter_listeners_query is None:
                        filter_listeners_query = query
                    else:
                        filter_listeners_query |= query
                self._listeners_cache = Listener.objects.filter(filter_listeners_query)
            else:
                self._listeners_cache = self.obj._default_manager.none()
        return self._listeners_cache

    def has_listeners(self):
        """
        Return True if this Message has any Listeners.
        
        """
        return len(self.listeners) > 0


class Listener(CreatedUpdatedModel):
    """
    A Listener is waiting waiting at a url for a hook from a model with certain properties.
    
    """
    obj_type = models.ForeignKey('contenttypes.ContentType', 
                                 help_text="The type of object I'm listening to.",
                                 related_name="listening_for")
    obj_property = models.CharField(max_length=32, blank=True, help_text="The property I'm listening for.")
    obj_value = models.CharField(max_length=32, blank=True, help_text="The value of the property I'm listening for.")
    url = models.URLField(verify_exists=False, help_text="The URL I'm listening at.")
    owner_type = models.ForeignKey('contenttypes.ContentType', related_name="listening_to")
    owner_id = models.PositiveIntegerField()
    owner = generic.GenericForeignKey('owner_type', 'owner_id')
    
    def __unicode__(self):
        return self.url


class MessageQueue(CreatedUpdatedModel):
    """
    A instance of a hook message.
    
    """
    message = models.ForeignKey('webhooks.Message', help_text="What message is being sent.")
    listener = models.ForeignKey('webhooks.Listener', help_text="Where this message is being sent.")
    processed = models.BooleanField(default=False, help_text="True if this message was successfully received.")
    attempts = models.IntegerField(default=0, help_text="Number of attempts to deliver this message.")
    failed_at = models.DateTimeField(null=True, blank=True, help_text="Last time this message failed.")
    
    class Meta:
        verbose_name = "message queue"
        verbose_name_plural = "message queue"
    
    def __unicode__(self):
        return unicode(self.listener)

    def process(self):
        self.attempts += 1
        if self.deliver(fail_silently=True):
            self.processed = True
        else:
            self.failed_at = datetime.datetime.now()
        self.save()

    def deliver(self, fail_silently=False):
        """
        Returns True if the message was successfully delivered.
                
        """
        # ### Look at the response - if not 200 then failed.
        import urllib2
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(TIMEOUT)
        try:
            urllib2.urlopen(self.listener.url, self.message.payload)
        except urllib2.URLError:
            print 'except'
            if fail_silently:
                return False
            else:
                raise
        else:
            return True
        finally:
            socket.setdefaulttimeout(original_timeout)




# def _get_hasher(hasher):
#     if hasher is None:
#         from django.utils import hashcompat   
#         return hashcompat.sha_constructor
#     else:
#         return hasher
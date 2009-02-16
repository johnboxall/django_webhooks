from django.db.models.base import ModelBase

from webhooks.models import Message, MessageQueue


class WebHookRegistery(object):
    """
    All Hooks must register here!
    
    """
    def __init__(self):
        self.registry = {}

    def register(self, model_or_iterable, fields, signal=None, serializer=None, 
                 retries=1, synchronous=False):
        """
        Default WebHook uses the Django JSON serializer with the post_save signal.
        `model_or_iterable` is a model or iterable of models to register WebHooks for.
        `fields` is a list of model fields to be serialized.
        `signal` is the signal to register on the model.
        `serializer` is the serializer used to create the message.
        `retries` is the number of times to attempt to deliver a message to a Listener.
        `synchronous` where hooks should be processed as they happen or as a cron job.
        
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
            
        if signal is None:
            from django.db.models.signals import post_save
            signal = post_save
            
        if serializer is None:
            from django.core import serializers
            JSONSerializer = serializers.get_serializer("json")
            serializer = JSONSerializer()
            
        webhook = WebHook(fields=fields, signal=signal, serializer=serializer, 
                          retries=retries, synchronous=synchronous)
        
        for model in model_or_iterable:
            self.registry[model] = webhook
            webhook.connect(model)
            
    def process(self):
        """
        Deliver all messages.
        
        """
        # Send all new Messages.
        qs = Message.objects.filter(processed=False).select_related(depth=1)
        for m in qs:        
            m.process(self.registry[m.obj._default_manager.model])
            
        # Retry all failed MessageQueue instances.
        for webhook in self.registry.values():
            qs = MessageQueue.objects.filter(processed=False, attempts__lt=webhook.retries)
            for mq in qs:
                mq.process()
            
            # Everything that hasn't been processed and has too many retries is done.
            qs = MessageQueue.objects.filter(processed=False, attempts__gte=webhook.retries).update(processed=True)


class WebHook(object):
    def __init__(self, fields=None, signal=None, serializer=None, retries=1, 
                 synchronous=False):
        self.fields = fields
        self.signal = signal
        self.serializer = serializer                
        self.retries = retries
        self.synchronous = synchronous
    
    def connect(self, model):
        self.signal.connect(self.send, sender=model)
    
    def send(self, sender, **kwargs):
        """
        If synchronous then send the hook message. Otherwise set it in the queue for later.
        
        """
        m = Message.objects.create(obj=kwargs['instance'])
        if self.synchronous:
            m.process()


webhooks = WebHookRegistery()
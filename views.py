from django.http import HttpResponse

VERIFIED = "VERIFIED"
INVALID = "INVALID"

# def verify(request):
#     """
#     Returns a HTTP/200 OKAY if this we sent this message.
#     
#     """
#     if request.method == "POST" and verify(request.raw_post_data):
#         return HttpResponse(VERIFIED)
#     else:
#         return HttpResponse(INVALID)
        
        
def listener(request):
    print request.get_full_path()
    print request.raw_post_data
    print request.POST
    
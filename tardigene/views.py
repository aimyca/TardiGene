import os 
import requests
import pandas as pd 

from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world") 

from django.shortcuts import render
from .models import Item
from pymongo import MongoClient
# Create your views here.

CONNECTION_STRING = "mongodb+srv://admin:admin@shop.vklonm4.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(CONNECTION_STRING)


def home(request):
    products = Item.objects.all()
    collection = client["shopping_data"]["products"]

    cursor = collection.find({})
    data = [i for i in cursor]

    context = {"products": data}
    return render(request, 'index.html', context=context)

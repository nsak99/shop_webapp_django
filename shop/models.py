from django.db import models

# Create your models here.


class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    photo = models.CharField(max_length=1000)

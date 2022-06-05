from __future__ import unicode_literals, absolute_import

from celery import shared_task

from .models import *


@shared_task
def add(x, y):
    return x + y


@shared_task
def generate_sale_reports(order_items, data):
    report = [order_items, data['shipping']['address'], data['shipping']['city'], data['shipping']['state'],
              data['shipping']['zip']]
    for i in report[0]:
        Report.objects.create(vendor=i[3], order_id=i[0], item_name=i[1], quantity=i[2], price=i[4])

    return "Report generated"


@shared_task
def update_item_task(action, product_id, customer_id):
    customer = User.objects.get(pk=customer_id)
    product = Product.objects.get(id=product_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        if order_item.quantity < product.quantity:
            order_item.quantity += 1
    elif action == 'remove':
        order_item.quantity -= 1

    order_item.save()

    if order_item.quantity == 0:
        order_item.delete()

    return "Item updated successfully"

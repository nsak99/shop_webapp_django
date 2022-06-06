from __future__ import unicode_literals, absolute_import

import datetime
from celery import shared_task
from django.contrib.auth import authenticate

from .models import *


@shared_task
def login_authentication_task(username, password):
    user = authenticate(username=username, password=password)
    return user.id


@shared_task
def get_store_items_task(customer_id):
    customer = User.objects.get(pk=customer_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    cart_items = order.get_cart_items
    return cart_items


@shared_task()
def process_order_task(data, customer_id):
    transaction_id = datetime.datetime.now().timestamp()
    customer = User.objects.get(pk=customer_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    for item in OrderItem.objects.filter(order=order.id):
        product = Product.objects.filter(name=item.product.name).get()
        product.quantity -= item.quantity
        product.save()

    order.order_items = [
        [item.order.id, item.product.name, item.quantity, item.product.vendor.username, item.product.price] for item in
        OrderItem.objects.filter(order=order.id)]
    order.order_total = total

    if total == order.get_cart_total:
        order.complete = True

    order.save()

    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        state=data['shipping']['state'],
        zipcode=data['shipping']['zip'],
    )

    report = [order.order_items, data['shipping']['address'], data['shipping']['city'], data['shipping']['state'],
              data['shipping']['zip']]
    print(report)
    for i in report[0]:
        Report.objects.create(vendor=i[3], order_id=i[0], item_name=i[1], quantity=i[2], price=i[4])

    return "Order processed successfully"


@shared_task
def update_items_task(product_id, action, customer_id):
    customer = User.objects.get(id=customer_id)
    product = Product.objects.get(id=product_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        if order_item.quantity < product.quantity:
            order_item.quantity += 1
        else:
            return False
            # messages.error(request, "No more items!")
    elif action == 'remove':
        order_item.quantity -= 1

    order_item.save()

    if order_item.quantity == 0:
        order_item.delete()

    return "Items updated successfully"

from django.contrib.auth.decorators import login_required, user_passes_test
from .models import *
from django.http import JsonResponse
import json
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .tasks import login_authentication_task, get_store_items_task, process_order_task, update_items_task


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_id = login_authentication_task.delay(username, password)
            print(user_id)
            user = User.objects.get(id=user_id.get())
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect(store)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form": form})


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect(store)
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()

    return render(request, 'register.html', context={"register_form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect(store)


def store(request):
    if request.user.is_authenticated:
        customer = request.user
        cart_items = get_store_items_task.delay(customer.id)
        cart_items = cart_items.get()
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cart_items = order['get_cart_items']

    products = Product.objects.all()
    context = {"products": products, 'cart_items': cart_items}
    return render(request, 'store.html', context=context)


@login_required(login_url=login_request)
def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cart_items = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cart_items = order['get_cart_items']

    context = {'items': items, 'order': order, 'cart_items': cart_items}
    return render(request, 'cart.html', context=context)


@login_required(login_url=login_request)
def checkout(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cart_items = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cart_items = order['get_cart_items']

    context = {'items': items, 'order': order, 'cart_items': cart_items}
    return render(request, 'checkout.html', context=context)


@user_passes_test(lambda u: u.groups.filter(name='vendor'))
def vendor(request):

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        cart_items = order.get_cart_items
    else:
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cart_items = order['get_cart_items']

    if request.user.is_authenticated:
        if request.POST.get('action') == 'edit':
            data = request.POST
            product = Product.objects.get(pk=data["product_id"])
            if data["items_added"]:
                product.quantity += int(data["items_added"])
            if data["new_price"]:
                product.price = float(data["new_price"])
            product.save()
        elif request.POST.get('action') == 'add':
            data = request.POST
            Product.objects.update_or_create(name=data['name'], price=float(data['price']), image=data['image'],
                                             vendor=request.user, quantity=int(data['quantity']))

    items = Product.objects.filter(vendor=request.user.id)
    reports = Report.objects.filter(vendor=request.user.username)
    context = {'items': items, 'cart_items': cart_items, 'reports': reports}

    return render(request, 'vendor.html', context=context)


def update_item(request):
    if request.body:
        data = json.loads(request.body)
        product_id = data['productId']
        action = data['action']

        customer = request.user
        result = update_items_task.delay(product_id, action, customer.id)
        if not result.get():
            messages.error(request, "No more items!")
        # product = Product.objects.get(id=product_id)
        # order, created = Order.objects.get_or_create(customer=customer, complete=False)
        #
        # order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
        #
        # if action == 'add':
        #     if order_item.quantity < product.quantity:
        #         order_item.quantity += 1
        #     else:
        #         messages.error(request, "No more items!")
        # elif action == 'remove':
        #     order_item.quantity -= 1
        #
        # order_item.save()
        #
        # if order_item.quantity == 0:
        #     order_item.delete()

    return JsonResponse('Item was added', safe=False)


def process_order(request):
    if request.user.is_authenticated:
        customer = request.user
        data = json.loads(request.body)
        process_order_task.delay(data, customer.id)
        messages.success(request, f"Order has been made successfully.")

    else:
        print("User is not logged in...")

    return JsonResponse('Payment completed', safe=False)

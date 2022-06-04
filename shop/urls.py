from django.urls import path

from shop import views

urlpatterns = [
    path('', views.store, name='store'),
    path('login/', views.login_request, name='login'),
    path('register/', views.register_request, name='register'),
    path('logout/', views.logout_request, name='logout'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('vendor/', views.vendor, name='vendor'),
    path('update-item/', views.update_item, name='update-item'),
    path('process-order/', views.process_order, name='process-order'),
]

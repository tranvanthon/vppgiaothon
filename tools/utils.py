# from store.models import Order


# def get_or_create_cart(request):
#     # Uu tien cho user login
#     if request.user.is_authenticated:
#         order = Order.objects.filter(customer=request.user, complete=False).first()
#         if not order:
#             order = Order.objects.create(customer=request.user, complete=False)
#         request.session["cart_id"] = order.id
#         return order

#     return None
from store.models import Order


def get_or_create_cart(request):

    # User login
    if request.user.is_authenticated:

        order = Order.objects.filter(
            customer=request.user,
            complete=False,
        ).first()

        if not order:
            order = Order.objects.create(
                customer=request.user,
                complete=False,
            )

        request.session["cart_id"] = order.id

        return order

    # Guest user
    cart_id = request.session.get("cart_id")

    if cart_id:
        order = Order.objects.filter(
            id=cart_id,
            complete=False,
        ).first()

        if order:
            return order

    order = Order.objects.create(
        complete=False,
    )

    request.session["cart_id"] = order.id

    return order

from store.models import Order


def get_or_create_cart(request):

    if request.user.is_authenticated:

        order, created = Order.objects.get_or_create(
            customer=request.user,
            status=Order.Status.DRAFT,
            defaults={
                "complete": False,
            },
        )

        request.session["cart_id"] = order.id

        return order

    cart_id = request.session.get("cart_id")

    if cart_id:

        order = Order.objects.filter(
            id=cart_id,
            status=Order.Status.DRAFT,
        ).first()

        if order:
            return order

    order = Order.objects.create(
        status=Order.Status.DRAFT,
        complete=False,
    )

    request.session["cart_id"] = order.id

    return order

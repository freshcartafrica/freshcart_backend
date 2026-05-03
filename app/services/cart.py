from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Product, User


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def serialize_cart(cart: Cart) -> dict:
    items = []
    subtotal = 0.0
    for item in cart.items:
        price = float(item.product.price)
        subtotal += price * item.quantity
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product_name": item.product.name,
                "unit_price": price,
                "image_url": item.product.image_url,
            }
        )
    return {"id": cart.id, "items": items, "subtotal": round(subtotal, 2)}


def add_item_to_cart(db: Session, user: User, product_id: int, quantity: int) -> Cart:
    cart = get_or_create_cart(db, user)
    product = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
    if not product:
        raise ValueError("Product not found")
    item = next((entry for entry in cart.items if entry.product_id == product_id), None)
    if item:
        item.quantity += quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
    db.commit()
    db.refresh(cart)
    return cart


def remove_item_from_cart(db: Session, user: User, product_id: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = next((entry for entry in cart.items if entry.product_id == product_id), None)
    if item:
        db.delete(item)
        db.commit()
    db.refresh(cart)
    return cart

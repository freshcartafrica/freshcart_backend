from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import Admin, Cart, Category, Product, User, UserRole, Vendor


def slugify(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "-")


def seed_database(db: Session) -> None:
    if db.query(Category).first():
        return

    categories = [
        Category(name="Fruits", slug="fruits"),
        Category(name="Vegetables", slug="vegetables"),
        Category(name="Drinks", slug="drinks"),
        Category(name="Staples", slug="staples"),
        Category(name="Protein", slug="protein"),
    ]
    db.add_all(categories)
    db.flush()

    admin_user = User(
        full_name="FreshCart Admin",
        email="admin@freshcart.africa",
        password_hash=get_password_hash("password123"),
        role=UserRole.admin,
    )
    vendor_user = User(
        full_name="Lagos Farm Hub",
        email="vendor@freshcart.africa",
        password_hash=get_password_hash("password123"),
        role=UserRole.vendor,
    )
    shopper = User(
        full_name="Ada Shopper",
        email="user@freshcart.africa",
        phone="+2348000000000",
        password_hash=get_password_hash("password123"),
        role=UserRole.user,
    )
    db.add_all([admin_user, vendor_user, shopper])
    db.flush()

    db.add(Admin(user_id=admin_user.id))
    vendor = Vendor(user_id=vendor_user.id, business_name="Lagos Farm Hub", is_verified=True)
    db.add(vendor)
    db.flush()
    db.add(Cart(user_id=shopper.id))

    catalog = [
        ("Fruits", "Banana Bunch", 3.5, "bunch"),
        ("Fruits", "Sweet Orange Pack", 4.2, "pack"),
        ("Fruits", "Watermelon Slice", 5.1, "item"),
        ("Fruits", "Pineapple Gold", 4.8, "item"),
        ("Vegetables", "Fresh Tomatoes", 2.6, "basket"),
        ("Vegetables", "Bell Pepper Mix", 3.1, "pack"),
        ("Vegetables", "Ugu Leaves", 1.9, "bundle"),
        ("Vegetables", "Carrots", 2.2, "pack"),
        ("Drinks", "Zobo Bottle", 1.5, "bottle"),
        ("Drinks", "Orange Juice", 2.9, "bottle"),
        ("Drinks", "Yoghurt Drink", 3.3, "bottle"),
        ("Drinks", "Table Water", 0.8, "sachet"),
        ("Staples", "Local Rice 5kg", 12.5, "bag"),
        ("Staples", "Garri White", 6.4, "bag"),
        ("Staples", "Beans Brown", 7.7, "bag"),
        ("Staples", "Semovita 1kg", 2.9, "bag"),
        ("Protein", "Frozen Chicken", 10.8, "pack"),
        ("Protein", "Egg Tray", 5.4, "tray"),
        ("Protein", "Catfish", 7.2, "item"),
        ("Protein", "Turkey Wings", 9.8, "pack"),
        ("Fruits", "Mango Basket", 6.0, "basket"),
        ("Vegetables", "Cucumber", 1.6, "item"),
        ("Staples", "Palm Oil 1L", 3.7, "bottle"),
        ("Drinks", "Malt Can", 1.2, "can"),
    ]

    category_map = {category.name: category for category in categories}
    products = []
    for idx, (category_name, name, price, unit) in enumerate(catalog, start=1):
        products.append(
            Product(
                vendor_id=vendor.id,
                category_id=category_map[category_name].id,
                name=name,
                slug=f"{slugify(name)}-{idx}",
                description=f"{name} sourced for fast neighborhood delivery.",
                price=price,
                unit=unit,
                stock_quantity=10 + idx,
                image_url=None,
                featured=idx <= 6,
            )
        )
    db.add_all(products)
    db.commit()

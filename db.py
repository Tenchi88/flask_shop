from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Sequence
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

PRODUCTS = [
    {
        'title': 'MacBook Air',
        'price_rub': 80000,
        'image_url': 'static/img/macbook_air.jpg',
        'in_store': True,
        'params':
            'Процессор: Core i5\n'
            'Частота процессора: 1800 МГц\n'
            'Объем оперативной памяти(точно): 8 Гб\n'
            'Объем жесткого диска: 128.. .256 Гб\n'
            'Размер экрана(точно): 13.3"\n'
            'Видеокарта: Intel HD Graphics 6000\n'
            'Вес: 1.35 кг\n'
            'Оптический привод: DVD нет\n'
            '4G LTE: нет\n'
            'Bluetooth: есть\n'
            'Wi - Fi: есть\n',
        'category': 'laptops'
    },
    {
        'title': 'MacBook Pro',
        'price_rub': 150000,
        'image_url': 'static/img/macbook_pro.jpg',
        'in_store': True,
        'params':
            'Процессор: Core i5\n'
            'Частота процессора: 2300 МГц\n'
            'Объем оперативной памяти (точно): 8 Гб\n'
            'Объем жесткого диска: 128...256 Гб\n'
            'Размер экрана (точно): 13.3 "\n'
            'Видеокарта: Intel Iris Plus Graphics 640\n'
            'Вес: 1.37 кг\n'
            'Оптический привод: DVD нет\n'
            '4G LTE: нет\n'
            'Bluetooth: есть\n'
            'Wi-Fi: есть\n',
        'category': 'laptops'
    },
    {
        'title': 'iPhone 8',
        'price_rub': 79999,
        'image_url': 'static/img/iphone_8.jpg',
        'in_store': True,
        'params':
            'смартфон, iOS 11\n'
            'экран 5.8", разрешение 2436x1125\n'
            'двойная камера 12/12 МП, автофокус, F/1.8\n'
            'память 64 Гб, без слота для карт памяти\n'
            '3G, 4G LTE, LTE-A, Wi-Fi, Bluetooth, NFC, GPS, ГЛОНАСС\n'
            'вес 174 г, ШxВxТ 70.90x143.60x7.70 мм\n',
        'category': 'smart_phones'
    },
    {
        'title': 'iPhone X',
        'price_rub': 99999,
        'image_url': 'static/img/iphone_X.png',
        'in_store': True,
        'params':
            'смартфон, iOS 11\n'
            'экран 5.8", разрешение 2436x1125\n'
            'двойная камера 12/12 МП, автофокус, F/1.8\n'
            'память 64 Гб, без слота для карт памяти\n'
            '3G, 4G LTE, LTE-A, Wi-Fi, Bluetooth, NFC, GPS, ГЛОНАСС\n'
            'вес 174 г, ШxВxТ 70.90x143.60x7.70 мм\n',
        'category': 'smart_phones'
    }
]

API_KEYS = {
    'xxx': 'admin'
}

Base = declarative_base()
engine = create_engine('sqlite:///shop.db')
Session = scoped_session(sessionmaker(bind=engine))


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer,
                Sequence('product_id_seq'),
                primary_key=True
                )

    title = Column(String)
    price_rub = Column(Integer)
    image_url = Column(String, nullable=True)
    in_store = Column(Boolean, default=False)
    params = Column(String)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship('Category', back_populates='products')

    def to_dict(self, fields=None):
        info = {}
        model_fields = fields or [c.name for c in self.__table__.columns]
        for field in model_fields:
            info[field] = getattr(self, field)
        return info


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, Sequence('category_id_seq'), primary_key=True)

    title = Column(String)
    slug = Column(String)
    is_visible = Column(Boolean)

    products = relationship('Product', back_populates='category')

    def to_dict(self, fields=None):
        info = {}
        model_fields = fields or [c.name for c in self.__table__.columns]
        for field in model_fields:
            info[field] = getattr(self, field)
        return info


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    laptops = Category(title='Ноутбуки', slug='slug', is_visible=True)
    Session.add(laptops)
    smart_phones = Category(title='Мобильные телефоны', slug='slug', is_visible=True)
    Session.add(smart_phones)
    i = 0
    Session.commit()
    for product in PRODUCTS:
        p = Product(
            title=product['title'],
            price_rub=product['price_rub'],
            image_url=product['image_url'],
            in_store=product['in_store'],
            params=product['params'],
            category=eval(product['category'])# if i < 2 else smart_phones
        )
        i += 1
        Session.add(p)
    Session.commit()

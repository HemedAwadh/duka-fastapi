from sqlalchemy import create_engine, Integer, String, Float, Column, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# engine = create_engine('postgresql://postgres:admin@localhost:5432/flask_api')
engine=create_engine('postgresql://api_user:herrera@167.71.62.79:5432/myduka_db')
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



# Creating models
# Products model
class Product(Base):
    __tablename__='products'
    id=Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    buying_price=Column(Float,nullable=False)
    selling_price=Column(Float,nullable=False)

    # sales=relationship('Sale',backref='product')

# Sales model
class Sale(Base):
    __tablename__='sales'
    id=Column(Integer,primary_key=True)
    pid=Column(Integer,ForeignKey('products.id'),nullable=False)
    quantity=Column(Integer,nullable=False)
    created_at=Column(DateTime,nullable=False)

# User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

# Payment model
class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, nullable=False)
    mrid = Column(String(100), nullable=False)
    crid = Column(String(100), nullable=False)
    amount = Column(Float, nullable=True)
    trans_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# This is the correct way to create tables
Base.metadata.create_all(bind=engine)


# from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
# from sqlalchemy.orm import relationship, declarative_base
# from datetime import datetime

# Base = declarative_base()

# class Product(Base):
#     __tablename__ = 'products'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     buying_price = Column(Float, nullable=False)
#     selling_price = Column(Float, nullable=False)
    
#     sales = relationship("Sale", back_populates="product")

# class Sale(Base):
#     __tablename__ = 'sales'
#     id = Column(Integer, primary_key=True, index=True)
#     pid = Column(Integer, ForeignKey('products.id'), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
#     product = relationship("Product", back_populates="sales")

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key=True, index=True)
#     full_name = Column(String, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     password = Column(String, nullable=False)

# class Payment(Base):
#     __tablename__ = 'payments'
#     id = Column(Integer, primary_key=True, index=True)
#     sale_id = Column(Integer, nullable=False)
#     mrid = Column(String(100), nullable=False)
#     crid = Column(String(100), nullable=False)
#     amount = Column(Float, nullable=True)
#     trans_code = Column(String(100), nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)





    #docker run -v d:\FLASK_API\app:/app/database/database.db -p 127.0.0.1:5000:80 -t flask-api

    #docker run -v /home/volume-database/flask-api/app:/app/database/database.db -p 5000:80 -t flask-api

    #docker run -v /home/volume-database/flask-api/app:/app/database/database.db -p 5000:80 -d -t flask-api
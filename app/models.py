import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin,db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    todos: so.WriteOnlyMapped['Todo'] = so.relationship(back_populates='owner')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_guest(self):
        return getattr(self, '_is_guest', False)

    @is_guest.setter
    def is_guest(self, value):
        self._is_guest = value

    def get_id(self):
        if self.is_guest:
            return "guest"  # A fixed ID for guest
        return str(self.id)
    @property
    def is_active(self):
        # Guest users are active too
        return True

class Guest(UserMixin):
    def __init__(self):
        self.id = 'guest'
        self.is_guest = True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
    
class Todo(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    text: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False)
    date_created: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    time: so.Mapped[int] = so.mapped_column(sa.Integer, default=0) #time in seconds
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.id'))
    owner: so.Mapped[User] = so.relationship(back_populates='todos')

    def __repr__(self):
        return '<Task %r>' % self.id

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'guest':
        return Guest()
    return User.query.get(int(user_id))
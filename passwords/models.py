import couchdb, couchdb.design

server = couchdb.Server()
try:
    db = server.create('passwords')
except couchdb.PreconditionFailed:
    db = server['passwords']


users_by_name = couchdb.design.ViewDefinition('users', 'users_by_name', """
function(doc) {
  if ( doc.type == 'user' )
    emit([doc._id, 0]);
  if ( doc.type == 'password' )
    emit([doc.user, 1]);
}""")

users_by_name.sync(db)

class ValidationError(Exception):
    pass

class ObjectDoesNotExist(Exception):
    pass


class CouchManager(object):
    def __init__(self):
        self.model = None

    def get_by_id(self, id):
        try:
            doc = db[id]
        except couchdb.ResourceNotFound as e:
            if e.args == (('not_found', 'missing'),):
                raise self.model.DoesNotExist()
            else:
                raise
        obj = self.model()
        for field in doc:
            setattr(obj, field, doc[field])
        return obj

    def __get__(self, obj, type=None):
        if obj is None:
            # I think mutating self here will cause problems with model inheritance
            self.model = type
            return self
        else:
            raise Exception("Can't access manager from instance")


class CouchModelMeta(type):
    def __new__(cls, name, bases, dict):
        new = type.__new__(cls, name, bases, dict)

        if not hasattr(new, 'objects'):
            new.objects = CouchManager()

        new.DoesNotExist = type('%s.DoesNotExist' % (name), (ObjectDoesNotExist,), {})

        return new

class CouchModel(object):
    __metaclass__ = CouchModelMeta
    def __init__(self, **kwargs):
        self._id = None
        self._rev = None
        self.type = self.__class__.__name__.lower()

        for column in kwargs:
            setattr(self, column, kwargs[column])

    def save(self):
        self.validate()
        (self._id, self._rev) = db.save(self.as_dict())

    def validate(self):
        pass

    def as_dict(self):
        data = {}
        if self._rev:
            data['_rev'] = self._rev
        if self._id:
            data['_id'] = self._id
        return data



class UserManager(CouchManager):
    def with_passwords(self, user_name):
        """
        Get a user by name along with all their passwords. It'd be nice to user
        objects.get_by_id(users_by_name).with_passwords(), like a django
        queryset, but I'm not sure how to do that yet.
        """
        rows = db.view('users/users_by_name', startkey=(user_name, 0), endkey=(user_name, 2), include_docs=True)
        rows = list(rows)
        if not rows:
            raise self.model.DoesNotExist
        user = User(**(rows[0].doc))
        user._passwords = [row.doc for row in rows[1:]]
        return user

class User(CouchModel):
    objects = UserManager()
    def as_dict(self):
        data = super(User, self).as_dict()
        data.update({
                '_id': self._id,
                'type': 'user'
                })
        return data

    def validate(self):
        if not self._id:
            raise ValidationError

    @property
    def name(self):
        return self._id

    @name.setter
    def name(self, value):
        self._id = value


    @property
    def passwords(self):
        try:
            return self._passwords
        except AttributeError:
            rows = db.view('users/users_by_name', startkey=(self.name, 0), endkey=(self.name, 2), include_docs=True)
            self._passwords = [row.doc for row in rows]
            return self._passwords


class Password(CouchModel):

    def as_dict(self):
        data = super(Password, self).as_dict()
        data.update({
                'type': 'password',
                'password': self.password,
                'user': self.user,
                })
        return data

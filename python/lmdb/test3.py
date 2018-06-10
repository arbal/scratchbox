import datetime
import random
import lmdb
from schema import User, Transaction


users = []

user1 = User()
user1.oid = 1
user1.name = 'Homer Simpson'
user1.authid = 'homer'
user1.email = 'homer.simpson@example.com'
user1.birthday = datetime.date(1950, 12, 24)
user1.is_friendly = True
user1.tags = ['relaxed', 'beerfan']
users.append(user1)

user2 = User()
user2.oid = 2
user2.name = 'Crocodile Dundee'
user2.authid = 'crocoboss'
user2.email = 'croco@example.com'
user2.birthday = datetime.date(1960, 2, 4)
user2.is_friendly = False
user2.tags = ['red', 'yellow']
user2.referred_by = user1.oid
users.append(user2)

user3 = User()
user3.oid = 3
user3.name = 'Foobar Space'
user3.authid = 'foobar'
user3.email = 'foobar@example.com'
user3.birthday = datetime.date(1970, 5, 7)
user3.is_friendly = True
user3.tags = ['relaxed', 'beerfan']
user3.referred_by = user1.oid
users.append(user3)


env = lmdb.open('.db4')

with Transaction(env, write=True) as txn:
    for user in users:
        _user = txn.users[user.oid]
        if not _user:
            txn.users[user.oid] = user
            #txn.users_by_authid[user.authid] = user.oid
            print('user stored', user)
        else:
            print('user loaded', _user)

with Transaction(env, write=True) as txn:
    for i in range(100):
        user = User()
        user.oid = i + 10
        user.name = 'Test {}'.format(i)
        user.authid = 'test-{}'.format(i)
        for j in range(10):
            user.ratings['test-rating-{}'.format(j)] = random.random()

        _user = txn.users[user.oid]
        if not _user:
            txn.users[user.oid] = user
            #txn.users_by_authid[user.authid] = user.oid
            print('user stored', user, user.oid, user.authid)
        else:
            print('user loaded', _user, _user.oid, _user.authid)

def test(env):
    with Transaction(env) as txn:
        for i in range(100):
            authid = 'test-{}'.format(i)
            oid = txn.users_by_authid[authid]
            if oid:
                user = txn.users[oid]
                print('success: user "{}" loaded by authid "{}"'.format(oid, authid))
            else:
                print('failure: user not found for authid "{}"'.format(authid))

def test_truncate(env):
    with Transaction(env, write=True) as txn:
        rows = txn.users_by_authid.truncate()
        print('users_by_authid truncated: {} rows'.format(rows))

def test_rebuild(env):
    with Transaction(env, write=True) as txn:
        rows = txn.users.rebuild_index('idx1')
        print('users_by_authid rebuilt: {} rows'.format(rows))

test(env)
test_truncate(env)
test_rebuild(env)
test(env)
test_rebuild(env)
test(env)

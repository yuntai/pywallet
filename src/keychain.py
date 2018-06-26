# HD wallet implementation using ecc implementation provided by the part of
# `Programming Bitcoin` class given by Jimmy Song

# https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

import hashlib
import hmac
from unittest import TestCase

import ecc
from helper import hash160, encode_base58_checksum

KEY_TYPES = ['public', 'private']
VERSIONS = {
  'mainnet':dict(zip(KEY_TYPES,[0x0488B21E,0x0488ADE4])),
  'testnet':dict(zip(KEY_TYPES,[0x043587CF,0x04358394])),
}

def point(pk):
  return pk.point

def ser_P(point):
  return point.sec()

def ser_32(i):
  return i.to_bytes(32, 'big')

def ser_256(v):
  return v.to_bytes(256, 'big')

def split_32(I):
  return I[:32], I[32:]

def rng(sz):
  return randint(0, 2**sz).to_bytes(sz//8, 'big')

def hmac_sha512(key=None, Data=None):
  return hmac.new(key, Data, hashlib.sha256).digest()

def get_master_key(S = None):
  S = rng(256) if S is None else S
  I = hmac_sha512(Key="Bitcoin seed".encode(), Data=S)

  I_L, I_R = split_32(I)

  if I_L == 0 or I_L >= ecc.N:
    return None

  return parse_256(I_L), I_R

def CKDpriv(k_par, c_par, i):
  if i >= 2**31: # hardened child
    I = hmac_sha512(key = c_par, Data = concat(b'\x00', ser_256(k_par), ser_32(i)))
  else: # normal child
    I = hmac_sha512(key = c_par, Data = concat(ser_P(point(k_par)), ser_32(i)))

  I_L, I_R = split_32(I)

  if parse_256(I_L) < ecc.N:
    k_i = (parse_256(I_L) + k_par) % ecc.N
    if k_i == 0:
      return None
    return k_i, I_R

def CKDpub(K_par, c_par, i):
  if i >= 2**31:
    return None
  else:
    I = hmac_sha512(key = c_par, Data = concat(ser_P(K_par), ser_32(i)))

  I_L, I_R = split_32(I)
  if parse_256(I_L) < ecc.N:
    K_i = point(parse_256(I_L)) + K_par
    if K_i == ecc.infinity:
      return None
    return K_i, I_R

def N(k, c):
  return point(k), c

class ExtendedKey:

  def __init__(self, parent, level, key, chain_code, child_number,
               nentwork_type, key_type):
    self.parent = parent
    self.level = level
    self.key = key
    self.chain_code = chain_code
    self.child_number = child_number
    self.network_type = network_type
    self.key_type = key_type

    self.children = []

  def serialize(self):
    "78 bytes structure"
    result = int_to_little_endian(self.versoin, 4)
    result += self.level
    result += self.parent.fingerprint()
    result += ser_32(child_number)
    result += self.chain_code
    result += ser_p(self.key)
    return result

  def encode(self):
    return encode_base58_checksum(self.serialize())

  @classmethod
  def master(cls, seed=None, network='testnet'):
    key, chain_code = get_master_key(S=seed)
    return ExtendedKey(None, 0, key, chain_code, None, network_type, 'private')

  @classmethod
  def parse(cls, s):
    pass

  # key identifier
  def id(self):
    if self.key_type == 'private':
      return hash160(point(self.key).sec())
    else:
      return hash160(self.key)

  def fingerprint():
    return id()[:32]

  # derive children key for a given index
  def derive_children(self, ix):
    pass

  # get next children with new index
  def derive_next(self):
    while True:
      next_ix = len(self.children)
      child = self.derive(ix)
      self.children.append(child)
      if child is not None:
        break
    return child

class KeyChain:
  def __init__(self, seed, path):
    self.path = path

  # parse path and return ExtendedKey
  def derive(self):
    nodes = self.path.split("/")
    h = nodes.pop()
    assert(h in "mM")
    f = CDKPriv if h == "m" else CDKPub
    root = master_key_gen(self.seed)
    if h == 'M':
      root = N(root)

    cur = root
    for n in nodes:
      # test hardened
      cur = f(cur, n)
    return cur

class ExtendedKeyTest(TestCase):
  def private_key_roundtrip():
    pk = ExtendedPrivateKey(ecc.PrivateKey())
    self.assertTrue(True)
  def test1(self):
    seed = hex("000102030405060708090a0b0c0d0e0f")
    k = KeyChain(seed, "m").derive()
    self.assertTrue(k.ser(),"xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi")

#Test vector 1
"""
Seed (hex): 000102030405060708090a0b0c0d0e0f

Chain m
ext pub: xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8
ext prv: xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi
Chain m/0H
ext pub: xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw
ext prv: xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7
Chain m/0H/1
ext pub: xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ
ext prv: xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs
Chain m/0H/1/2H
ext pub: xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5
ext prv: xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM
Chain m/0H/1/2H/2
ext pub: xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV
ext prv: xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334
Chain m/0H/1/2H/2/1000000000
ext pub: xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy
ext prv: xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76

Test vector 2
Seed (hex): fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542

Chain m
ext pub: xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB
ext prv: xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U
Chain m/0
ext pub: xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH
ext prv: xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt
Chain m/0/2147483647H
ext pub: xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a
ext prv: xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9
Chain m/0/2147483647H/1
ext pub: xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon
ext prv: xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef
Chain m/0/2147483647H/1/2147483646H
ext pub: xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL
ext prv: xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc
Chain m/0/2147483647H/1/2147483646H/2
ext pub: xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt
ext prv: xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j
"""

#Test vector 3
"""
These vectors test for the retention of leading zeros. See bitpay/bitcore-lib#47 and iancoleman/bip39#58 for more information.

Seed (hex): 4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be

Chain m
ext pub: xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13
ext prv: xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6
Chain m/0H
ext pub: xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y
ext prv: xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L
"""


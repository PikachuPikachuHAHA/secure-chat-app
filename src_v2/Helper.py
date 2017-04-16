from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
import os,sys,binascii,time
import constants as CN
import time
import pickle,json
import struct
import constants as constants
from Message import Message, MessageParser
from Cryptographer import Cryptographer as crypt



def pickle_message(msg):
    final_msg = {}
    final_msg['msg_type'] = msg.msg_type
    final_msg['payload'] = msg.payload
    final_msg['signature'] = msg.signature
    final_msg['iv_tag'] = msg.iv_tag
    return pickle.dumps(final_msg)


def unpickle_message(msg):
    msg = pickle.loads(msg)
    return Message(msg_type=msg['msg_type'], payload=msg['payload'], signature=msg['signature'],iv_tag=msg['iv_tag'] )


def send_msg(sender_socket, dest_addr, msg):
    msg = pickle_message(msg)
    sender_socket.sendto(str(msg), dest_addr)


def send_receive_msg(sender_socket, dest_addr, msg, recv_udp):
    recv_udp.condition.acquire()
    msg = pickle_message(msg)
    sender_socket.sendto(str(msg), dest_addr)
    reply = recv_udp.receive(100000000)
    return unpickle_message(reply[0]), reply[1]


def tuple_from_string(data):
    final_tuple = []
    try:
        while True:
            if data == "":
                break
            h_len = struct.unpack("!H", data[:2])[0]
            each = data[2:2 + h_len]
            final_tuple.append(each)
            data = data[2 + h_len:]
        return tuple(final_tuple)
    except (IndexError, struct.error):
        print "tuple conversion error"


def string_from_tuple(data):
    final_string = ""
    for each in data:
        ln = struct.pack("!H", len(each))
        final_string += ln
        final_string += each
    return final_string


'''
client solves the puzzle
returns n: n such that SHA256(R, n) is zero in its first k bits
'''


def solve_puzzle(challenge):
    n=0
    string=challenge[0]
    k=challenge[1]
    while 1:
        h = hashes.Hash(hashes.SHA256(), backend=default_backend())
        h.update(string)
        h.update(bytes(n))
        if is_first_k_zeros(h.finalize(), k):
            return n

        n += 1

# server verifies the challenge solution


def verify_challenge_solution(string,n,k):
    h = hashes.Hash(hashes.SHA256(), backend=default_backend())
    h.update(string)
    h.update(bytes(n))
    if is_first_k_zeros(h.finalize(), k):
        return n


# checks if first k bytes are zero


def is_first_k_zeros(hashed_val,k):
    first_k_bytes = hashed_val[:k]
    for i in first_k_bytes:
        if ord(i) != 0:
            return False
    return True



# create random challenge string


def get_challenge(los):
    c_str= os.urandom(CN.NONCE_LENGTH)
    while c_str in los:
        c_str = os.urandom(CN.NONCE_LENGTH)
    return c_str, ord(chr(CN.P_DIFFICULTY))

# loads all the hashed password into the server at server startup from .json file


def load_hasehed_pwd():
    user_cred_dict={}
    with open(CN.USER_CRED_FILE,'rb') as ucf:
        for uc in ucf:
            uc= uc.rstrip('\n')
            line=uc.split('##')
            user_cred_dict.update({line[0]:line[1]})
    return user_cred_dict

# read pt_user_cred.json file to hash passwords into user_cred.txt file


def create_hased_user_cred():
    c=crypt()

    pt_user_cred_fn=open(CN.PT_USER_CRED_FILE)
    pt_user_cred=json.load(pt_user_cred_fn)
    with open(CN.USER_CRED_FILE,'wb') as ucf:
        for pt_uc in pt_user_cred:
            u=pt_uc["un"].encode('utf-8').strip()
            hashed=c.compute_hash_from_client_password(bytes(pt_uc["un"]),bytes(pt_uc["pwd"]))
            d=u+"##"+hashed+"\n"
            ucf.write(d)



# create_hased_user_cred()
# dict= load_hasehed_pwd()
# c=crypt()
# parul_pwd=c.compute_hash_from_client_password('parul','53@Parul!')
# parul_pwd=bytes(parul_pwd)
# parul_dic_pwd=dict.get('parul')
# print parul_pwd==parul_dic_pwd




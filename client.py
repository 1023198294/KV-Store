import sys, requests
import argparse

def redirectToLeader(server_address, message):
    type = message["type"]
    # looping until someone tells he is the leader
    while True:
        # switching between "get" and "put"
        if type == "get":
            try:
                response = requests.get(server_address,
                                        json=message,
                                        timeout=1)
            except Exception as e:
                return e
        elif type=='put':
            try:
                response = requests.put(server_address,
                                        json=message,
                                        timeout=1)
            except Exception as e:
                return e
        elif type=='delete':
            try:
                response = requests.put(server_address,
                                        json=message,
                                        timeout=1)
            except Exception as e:
                return e
        # if valid response and an address in the "message" section in reply
        # redirect server_address to the potential leader
        if response.status_code == 200 and "payload" in response.json():
            payload = response.json()["payload"]
            if "message" in payload:
                server_address = payload["message"] + "/request"
            else:
                break
        else:
            break
    return response.json()

# client put request
def put(addr, key, value):
    server_address = addr + "/request"
    payload = {'key': key, 'value': value,'act':'put'}
    message = {"type": "put", "payload": payload}
    # redirecting till we find the leader, in case of request during election
    print(redirectToLeader(server_address, message))


# client get request
def get(addr, key):
    server_address = addr + "/request"
    payload = {'key': key,'act':'get'}
    message = {"type": "get", "payload": payload}
    # redirecting till we find the leader, in case of request during election
    print(redirectToLeader(server_address, message))
def DEL(addr,key):
    server_address = addr+'/request'
    payload = {'key':key,'act':'del'}
    message = {'type':'delete','payload':payload}
    print(redirectToLeader(server_address,message))
def invalid_input():
    print("PUT usage: python client.py PUT address 'key' 'value'")
    print("GET usage: python client.py GET address 'key'")
    print("DEL usage: python client.py DEL address 'key'")
    print("Format: address: http://ip:port")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        # addr, key
        # get
        action = sys.argv[1]
        addr = sys.argv[2]
        key = sys.argv[3]
        if action=='get' or action=='GET':
            get(addr, key)
        elif action=='del' or action=='DEL':
            DEL(addr,key)
        else:
            invalid_input()

    elif len(sys.argv) == 5:
        # addr, key value
        # put
        action = sys.argv[1]
        addr = sys.argv[2]
        key = sys.argv[3]
        val = sys.argv[4]
        if action=='put'or action=='PUT':
            put(addr, key, val)
        else:
            invalid_input()
    else:
        invalid_input()
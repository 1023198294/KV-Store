import sys
import grpc
import mykvserver_pb2
import mykvserver_pb2_grpc
from debugger import debugger

def invalid_input():
    print("PUT usage: python client.py PUT address 'key' 'value'")
    print("GET usage: python client.py GET address 'key'")
    print("DEL usage: python client.py DEL address 'key'")
    print("Format: address: http://ip:port")
    input()
    exit()
# client put request


if __name__ == "__main__":
    print(' * this is grpc client')
    action = sys.argv[1]
    addr = sys.argv[2]
    key = sys.argv[3]
    while True:

        channel = grpc.insecure_channel(addr)
        # print(addr)
        if len(sys.argv) == 4:
            # addr, key
            # get,del
            stub = mykvserver_pb2_grpc.KVServerStub(channel)
            response = None
            if action=='get' or action=='GET':
                msg = mykvserver_pb2.GetMessage()
                msg.type = 'get'
                msg.payload.act = 'get'
                msg.payload.key = key
                msg.payload.value = ''
                response = stub.GetRequest(msg)
                if response.payload.message:
                    print('redirect to leader',response.payload.message)
                    addr = response.payload.message
                else:
                    print(response)
                    break
            elif action=='del' or action=='DEL':
                msg = mykvserver_pb2.DelMessage()
                msg.type = 'del'
                msg.payload.act = 'del'
                msg.payload.key = key
                msg.payload.value = ''
                response = stub.DelRequest(msg)
                if response.payload.message:
                    print('redirect to leader',response.payload.message)
                    addr = response.payload.message
                else:
                    print(response)
                    break
            else:
                invalid_input()

        elif len(sys.argv) == 5:
            # addr, key value
            # put
            val = sys.argv[4]
            if action=='put'or action=='PUT':
                stub = mykvserver_pb2_grpc.KVServerStub(channel)
                msg = mykvserver_pb2.PutMessage()
                msg.type = 'put'
                msg.payload.act = 'put'
                msg.payload.key = key
                msg.payload.value = val
                response = stub.PutRequest(msg)
                if response.payload.message:
                    print('redirect to leader',response.payload.message)
                    addr = response.payload.message
                else:
                    print(response)
                    break
                #print(response)
            else:
                invalid_input()
        else:
            invalid_input()
from node_grpc import Node
from node_grpc import FOLLOWER, LEADER
import sys
import grpc
from concurrent import futures
import mykvserver_pb2
import mykvserver_pb2_grpc
import time
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
my_ip = None
my_host = None
my_port = None
n = None

class KVServer(mykvserver_pb2_grpc.KVServerServicer):
    def Join(self, request, context):
        response = mykvserver_pb2.JoinResponse(ok=True)
        return response
    def PutRequest(self, request, context):
        #type = request.type
        #print('putting, request = ',request)
        payload = {'act':None,'key':None,'value':None}
        payload['act'] = request.payload.act
        payload['key'] = request.payload.key
        payload['value'] = request.payload.value
        response = mykvserver_pb2.PutReply()
        response.code = 'fail'
        if n.status == LEADER:
            #print('getting, request = ', request)
            result = n.handle_put(payload)
            if result:
                response.code='success'
        elif n.status== FOLLOWER:
            print('redirect to leader ',n.leader)
            response.payload.message = n.leader
            response.payload.act = payload['act']
            response.payload.key = payload['key']
            response.payload.value = payload['value']

        #print('put response:',response)
        return response

    def GetRequest(self, request, context):
        #print('getting, request = ',request)
        payload = {'act': None, 'key': None,'value':None}
        payload['act'] = request.payload.act
        payload['key'] = request.payload.key
        payload['value'] = request.payload.value
        response = mykvserver_pb2.GetReply()
        response.code = 'fail'
        if n.status == LEADER:
            #print('getting, request = ', request)
            result = n.handle_get(payload)
            if result and result['value']:
                response.code = 'success'
                response.payload.act = request.payload.act
                response.payload.key = request.payload.key
                response.payload.value = result['value']

        elif n.status == FOLLOWER:
            print('redirect to leader ',n.leader)
            response.payload.message = n.leader
            response.payload.act = payload['act']
            response.payload.key = payload['key']
            response.payload.value = payload['value']
        #print('get response:',response)

        return response

    def DelRequest(self, request, context):
        #print('del, request = ', request)
        payload = {'act': None, 'key': None, 'value': None}
        payload['act'] = request.payload.act
        payload['key'] = request.payload.key
        payload['value'] = 'None'
        response = mykvserver_pb2.DelReply()
        response.code = 'fail'
        if n.status == LEADER:
            #print('del, request = ', request)
            result = n.handle_put(payload)
            if result:
                response.code = 'success'
        elif n.status == FOLLOWER:
            print('redirect to leader ', n.leader)
            response.payload.message = n.leader
            response.payload.act = payload['act']
            response.payload.key = payload['key']
            response.payload.value = payload['value']

        #print('put response:', response)
        return response

    def VoteRequest(self, request, context):
        term = request.term
        commitIdx = request.commitIdx
        staged = {'act': None, 'key': None, 'value': None}
        staged['act'] = request.staged.act
        staged['key'] = request.staged.key
        staged['value'] = request.staged.value
        #debugger (str(term)+str(commitIdx)+str(staged))
        choice, term = n.decide_vote(term, commitIdx, staged)
        #print(choice,term)
        message = mykvserver_pb2.VoteReply(choice=choice,term=term)
        return message

    def HeartBeat(self, request, context):
        #print('Procedure heart beat')
        msg = {
            'term':request.term,
            'addr':request.addr,
        }
        if request.payload:
            msg['payload'] = {
             'act' : request.payload.act,
             'key' : request.payload.key,
             'value':request.payload.value
            }
        if request.action:
            msg['action'] = request.action
        if request.commitIdx:
            msg['commitIdx'] = request.commitIdx
        term,commitIdx = n.heartbeat_follower(msg)
        reply = mykvserver_pb2.HBReply()
        reply.term = term
        reply.commitIdx = commitIdx
        return reply
    def SpreadLog(self, request, context):
        pass
    def SpreadCommit(self, request, context):
        pass


def GRPCserver(ip_list,my_ip):
    global n
    n = Node(ip_list, my_ip)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mykvserver_pb2_grpc.add_KVServerServicer_to_server(KVServer(),server)
    server.add_insecure_port(my_ip)
    time.sleep(5)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    # python server.py index ip_list
    if len(sys.argv) == 3:
        index = int(sys.argv[1])
        ip_list_file = sys.argv[2]
        ip_list = []
        # open ip list file and parse all the ips
        with open(ip_list_file) as f:
            for ip in f:
                ip_list.append(ip.strip())
        my_ip = ip_list.pop(index)
        print(' * this is server Number',index)
        GRPCserver(ip_list,my_ip)
    else:
        print("usage: python server.py <index> <ip_list_file>")

import threading
import time
import utils
from config import cfg
from LRU import LRUCache
FOLLOWER = 0
CANDIDATE = 1
LEADER = 2
addr = None
import grpc
import mykvserver_pb2
import mykvserver_pb2_grpc
from debugger import debugger
class Node():
    def __init__(self, fellow, my_ip):
        self.addr = my_ip
        self.fellow = fellow
        self.lock = threading.Lock()
        self.DB = {}
        self.log = []
        self.staged = None
        self.term = 0
        self.status = FOLLOWER
        self.majority = ((len(self.fellow) + 1) // 2) + 1
        self.voteCount = 0
        self.commitIdx = 0
        self.timeout_thread = None
        self.init_timeout()
        self.capacity = 3
        self.cache = LRUCache(capacity=self.capacity)



    # increment only when we are candidate and receive positve vote
    # change status to LEADER and start heartbeat as soon as we reach majority
    def incrementVote(self):
        self.voteCount += 1
        if self.voteCount >= self.majority:
            print(f"{self.addr} becomes the leader of term {self.term}")
            self.status = LEADER
            self.startHeartBeat()

    # vote for myself, increase term, change status to candidate
    # reset the timeout and start sending request to followers
    def startElection(self):
        self.term += 1
        self.voteCount = 0
        self.status = CANDIDATE
        self.init_timeout()
        self.incrementVote()
        self.send_vote_req()

    # ------------------------------
    # ELECTION TIME CANDIDATE

    # spawn threads to request vote for all followers until get reply
    def send_vote_req(self):
        # TODO: use map later for better performance
        # we continue to ask to vote to the address that haven't voted yet
        # till everyone has voted
        # or I am the leader
        for voter in self.fellow:
            threading.Thread(target=self.ask_for_vote,
                             args=(voter, self.term)).start()

    # request vote to other servers during given election term
    def ask_for_vote(self, voter, term):

        # need to include self.commitIdx, only up-to-date candidate could win
        #debugger (self.addr+'+'+voter)
        channel = grpc.insecure_channel(voter)
        stub = mykvserver_pb2_grpc.KVServerStub(channel)

        message = mykvserver_pb2.VoteMessage()
        #debugger (stub.VoteRequest(message),2)

        message.term = term
        message.commitIdx = self.commitIdx
        if self.staged:
            message.staged.act = self.staged['act']
            message.staged.key = self.staged['key']
            message.staged.value = self.staged['value']

        while self.status == CANDIDATE and self.term == term:

            reply = stub.VoteRequest(message)
            if reply:
                #choice = reply.json()["choice"]
                choice = reply.choice
                #print(f"RECEIVED VOTE {choice} from {voter}")
                if choice and self.status == CANDIDATE:
                    self.incrementVote()
                elif not choice:
                    # they declined because either I'm out-of-date or not newest term
                    # update my term and terminate the vote_req
                    #term = reply.json()["term"]
                    term = int(reply.term)
                    if term > self.term:
                        self.term = term
                        self.status = FOLLOWER
                    # fix out-of-date needed
                break

    # ------------------------------
    # ELECTION TIME FOLLOWER

    # some other server is asking
    def decide_vote(self, term, commitIdx, staged):
        # new election
        # decline all non-up-to-date candidate's vote request as well
        # but update term all the time, not reset timeout during decision
        # also vote for someone that has our staged version or a more updated one
        if self.term < term and self.commitIdx <= commitIdx and (
                staged or (self.staged == staged)):
            self.reset_timeout()
            self.term = term
            return True, self.term
        else:
            return False, self.term

    # ------------------------------
    # START PRESIDENT

    def startHeartBeat(self):
        #print("Starting HEARTBEAT")
        if self.staged:
            # we have something staged at the beginngin of our leadership
            # we consider it as a new payload just received and spread it aorund
            self.handle_put(self.staged)

        for each in self.fellow:
            t = threading.Thread(target=self.send_heartbeat, args=(each, ))
            t.start()

    def update_follower_commitIdx(self, follower):
        channel = grpc.insecure_channel(follower)
        stub = mykvserver_pb2_grpc.KVServerStub(channel)
        message = mykvserver_pb2.HBMessage()
        message.term = self.term
        message.addr = self.addr
        message.action = 'commit'
        message.payload.act = self.log[-1]['act']
        message.payload.key = self.log[-1]['key']
        message.commitIdx = self.commitIdx
        if self.log[-1]['value']:
            message.payload.value = self.log[-1]['value']
        reply = stub.HeartBeat(message)

    def send_heartbeat(self, follower):
        # check if the new follower have same commit index, else we tell them to update to our log level
        if self.log:
            self.update_follower_commitIdx(follower)


        while self.status == LEADER:
            start = time.time()
            channel = grpc.insecure_channel(follower)
            stub = mykvserver_pb2_grpc.KVServerStub(channel)

            ping = mykvserver_pb2.JoinRequest()
            #print(ping)
            if ping:
                if follower not in self.fellow:
                    self.fellow.append(follower)
                message = mykvserver_pb2.HBMessage()
                message.term = self.term
                message.addr = self.addr
                reply = stub.HeartBeat(message)
                if reply:
                    self.heartbeat_reply_handler(reply.term,
                                                 reply.commitIdx)
                delta = time.time() - start
                # keep the heartbeat constant even if the network speed is varying
                time.sleep((cfg.HB_TIME - delta) / 1000)
            else:
                for index in range(len(self.fellow)):
                    if self.fellow[index] == follower:
                        self.fellow.pop(index)
                        print('Server {} lost connect'.format(follower))
                        break

    # we may step down when get replied
    def heartbeat_reply_handler(self, term, commitIdx):
        # i thought i was leader, but a follower told me
        # that there is a new term, so i now step down
        if term > self.term:
            self.term = term
            self.status = FOLLOWER
            self.init_timeout()

        # TODO logging replies

    # ------------------------------
    # FOLLOWER STUFF

    def reset_timeout(self):
        self.election_time = time.time() + utils.random_timeout()

    # /heartbeat

    def heartbeat_follower(self, msg):
        # weird case if 2 are PRESIDENT of same term.
        # both receive an heartbeat
        # we will both step down

        term = msg["term"]
        if self.term <= term:
            self.leader = msg["addr"]
            self.reset_timeout()
            # in case I am not follower
            # or started an election and lost it
            if self.status == CANDIDATE:
                self.status = FOLLOWER
            elif self.status == LEADER:
                self.status = FOLLOWER
                self.init_timeout()
            # i have missed a few messages
            if self.term < term:
                self.term = term

            # handle client request
            if "action" in msg:
                print("received action", msg)
                action = msg["action"]
                # logging after first msg
                if action == "log":
                    payload = msg["payload"]
                    self.staged = payload
                    #print(self.staged)
                # proceeding staged transaction
                elif self.commitIdx <= msg["commitIdx"]:
                    #print('update staged')
                    if not self.staged:
                        self.staged = msg["payload"]
                    self.commit()

        return self.term, self.commitIdx

    # initiate timeout thread, or reset it
    def init_timeout(self):
        self.reset_timeout()
        # safety guarantee, timeout thread may expire after election
        if self.timeout_thread and self.timeout_thread.isAlive():
            return
        self.timeout_thread = threading.Thread(target=self.timeout_loop)
        self.timeout_thread.start()

    # the timeout function
    def timeout_loop(self):
        # only stop timeout thread when winning the election
        while self.status != LEADER:
            delta = self.election_time - time.time()
            if delta < 0:
                self.startElection()
            else:
                time.sleep(delta)

    def handle_get(self, payload):
        print('handle_getting ',payload)
        key = payload["key"]
        act = payload["act"]
        if act == 'get':
            print("getting", payload)
            cache_res = self.cache.get(key)
            if cache_res is not None:
                print('result in cache')
                payload["value"] = cache_res
                return payload
            elif key in self.DB:
                print('result in db')
                payload["value"] = self.DB[key]
                return payload
        '''
        elif act == 'del':
            print('deleting',payload)
            if key in self.DB:
                self.DB[key] = None
                return payload
        '''
        return None

    # takes a message and an array of confirmations and spreads it to the followers
    # if it is a comit it releases the lock
    def spread_update(self, message, confirmations=None, lock=None):
        for i, each in enumerate(self.fellow):

            channel = grpc.insecure_channel(each)
            stub = mykvserver_pb2_grpc.KVServerStub(channel)
            m = mykvserver_pb2.HBMessage()
            m.term = message['term']
            m.addr = message['addr']
            if message['payload'] is not None:
                #print(message['payload'])
                m.payload.act = message['payload']['act']
                m.payload.key = message['payload']['key']
                m.payload.value = message['payload']['value']
            #m.action = 'commit'
            if message['action']:
                m.action = message['action']
            m.commitIdx = self.commitIdx
            r = stub.HeartBeat(m)
            if r and confirmations:
                # print(f" - - {message['action']} by {each}")
                confirmations[i] = True
        if lock:
            lock.release()

    def handle_put(self, payload):
        #print("putting", payload)
        # lock to only handle one request at a time
        self.lock.acquire()
        self.staged = payload
        waited = 0
        log_message = {
            "term": self.term,
            "addr": self.addr,
            "payload": payload,
            "action": "log",
            "commitIdx": self.commitIdx
        }

        # spread log  to everyone
        log_confirmations = [False] * len(self.fellow)
        threading.Thread(target=self.spread_update,
                         args=(log_message, log_confirmations)).start()
        while sum(log_confirmations) + 1 < self.majority:
            waited += 0.0005
            time.sleep(0.0005)
            if waited > cfg.MAX_LOG_WAIT / 1000:
                print(f"waited {cfg.MAX_LOG_WAIT} ms, update rejected:")
                self.lock.release()
                return False
        # reach this point only if a majority has replied and tell everyone to commit
        commit_message = {
            "term": self.term,
            "addr": self.addr,
            "payload": payload,
            "action": "commit",
            "commitIdx": self.commitIdx
        }
        #print('commit to all')
        can_delete = self.commit()
        threading.Thread(target=self.spread_update,
                         args=(commit_message, None, self.lock)).start()
        print("majority reached, replied to client, sending message to commit, message:",commit_message)
        return can_delete

    # put staged key-value pair into local database
    def commit(self):
        self.commitIdx += 1
        self.log.append(self.staged)
        key = self.staged["key"]
        act = self.staged["act"]
        value = None
        can_delete = True
        cache_update = False
        #if self.staged['value'] == 'None':
        #    self.DB[key]= None
        #    key = None
        #    can_delete = False
        if act == 'put':
            #print('it\'s a put transaction')
            value = self.staged["value"]
            self.DB[key] = value
            cache_update = True
        elif act =='del':
            #print('it\' s a delete transaction')
            if self.DB[key]:
                self.DB[key] = None
            else:
                can_delete = False
            cache_update = True
        if cache_update:
            self.cache.set(key, value)
            self.cache.getallkeys()
        # put newly inserted key-value pair into local cache

        # empty the staged so we can vote accordingly if there is a tie
        self.staged = None
        return can_delete
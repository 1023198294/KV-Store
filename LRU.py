class CacheNode:
    key = None
    value = None
    pre = None
    next = None

    def __init__(self,key,value):
        self.key = key
        self.value = value

class LRUCache:
    mapping = {}
    head = None
    end = None
    def __init__(self,capacity):
        self.capacity = capacity
    def set(self,key,value):
        if key in self.mapping:
            oldNode = self.mapping[key]
            if value is None:
                self.mapping.pop(key)
                self.remove(oldNode)
                #self.getallkeys()
                #print('erase key', key)
            else:
                oldNode.value = value
                self.remove(oldNode)
                self.sethead(oldNode)
        else:
            node = CacheNode(key,value)
            if len(self.mapping) >= self.capacity:
                self.mapping.pop(self.end.key)
                self.remove(self.end)
                self.sethead(node)
            else:
                self.sethead(node)
            self.mapping[key] = node



    def sethead(self,node):
        node.next = self.head
        node.pre = None
        if self.head:
            self.head.pre = node
        self.head = node
        if not self.end:
            self.end = self.head
    def remove(self,node):
        if node.pre:
            node.pre.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.pre = node.pre
        else:
            self.end = node.pre
    def getallkeys(self):
        tmp = None
        if self.head:
            tmp = self.head
            pair = "<{0},{1}>"
            res = ""
            while tmp:
                tmp_p = pair.format(tmp.key,tmp.value)
                res += tmp_p
                res += "->"
                tmp = tmp.next
            tmp_p = pair.format(None,None)
            res += tmp_p
            print('current cache is ',res)
    def get(self,key):
        if key in self.mapping:
            node = self.mapping[key]
            self.remove(node)
            self.sethead(node)
            return node.value
        else:
            return None
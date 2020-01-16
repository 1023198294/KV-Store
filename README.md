# KV Store
 A grpc-based and flask-based fault-tolerant distributed key-value storage system implemented in Python .

# Preparation

open the cmd.exe and **cd** to **the location of this repository**

## Compile the proto buffer

In grpc-based system, if you want to change the structure of the default protobuf,you can edit **mykvserver.proto** according to the standard given by https://developers.google.com/protocol-buffers/docs/proto3 .Then, compile the protobuf by executing

```
➜ ./compile.bat
```

# How to run the Server

### flask mode

The server is initialized with an index and an `ip_list.txt`

```
➜ ./setup.bat
```

## grpc mode

The server is initialized with an index and an `ip_list2.txt`

```
➜ ./setup_grpc.bat
```

# How to run the Client

## flask mode

```
operation : put,get,del
put usage : 
➜ python client.py put [address] [key] [value]
get usage : 
➜ python client.py get [address] [key] 
get del : 
➜ python client.py get [address] [key] 
Format:
address = http://ip:port
```



## grpc mode

```
operation : put,get,del
put usage : 
➜ python client.py put [address] [key] [value]
get usage : 
➜ python client.py get [address] [key] 
get del : 
➜ python client.py get [address] [key] 
Format:
address = ip:port
```

# references

* https://raft.github.io/
* https://github.com/Oaklight/Vesper
* https://en.wikipedia.org/wiki/Raft_(computer_science)

# Python requirements

* python >= 3.4
  * grpcio==1.24.1
  * Flask==1.0.2
  * requests==2.20.0
  * grpc==0.3-19
  * protobuf==3.11.2 

# CONTACT

please email me 1023198294@qq.com


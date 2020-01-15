start python client_grpc.py put 127.0.0.1:5000 name hyj
start python client_grpc.py put 127.0.0.1:5001 name laoba
start python client_grpc.py put 127.0.0.1:5002 name caixukun
start python client_grpc.py put 127.0.0.1:5003 name guolaoshi
start python client_grpc.py put 127.0.0.1:5004 name sunxiaochuan
timeout /T 10 /NOBREAK
start python -i client_grpc.py get 127.0.0.1:5000 name 




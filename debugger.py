def debugger(context,logid=1):
    f = open('log2.txt','w')
    f.write(context)
    f.close()
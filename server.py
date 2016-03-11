import json
import libvirt
import random
import sqlite3
import sys
import uuid
import re
from BeautifulSoup import BeautifulSoup
from flask import Flask, render_template
from flask import request
from flask import jsonify


app = Flask(__name__)


@app.route('/')
def index():
  return render_template('index.html')

@app.route('/vm/create/')
def create():
    vmName = request.args.get('name')
    print vmName
    instance_type = request.args.get('instance_type')
    instance_type = int(instance_type)
    image_id = request.args.get('image_id')
    image_id = int(image_id)
    image_id = image_id -100
    imageFilePath = imageList[image_id]
    print imageFilePath	
    success = 0
    ##### Connect to Database and create table if table is not created      ######
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE if not exists resource(pmid integer, vmid text, instance_type integer, memory integer, cpu integer, name text)''')
    requestMemory = json_object['types'][instance_type-1]['ram']
    requestCPU = json_object['types'][instance_type-1]['cpu']
    requestMemory = int(requestMemory)
    requestCPU = int(requestCPU)
    loop=0
    for ip in ipAddress:
        print "loop entry "
        cmd = 'qemu+tcp://' + ip + '/system'
        connection = libvirt.open(cmd)
        p=connection.getCapabilities()
        soup = BeautifulSoup(p)
        a = soup.find('cpus')
        totalCPU = a['num']
        totalCPU = int(totalCPU)
        totalMemory = soup.find('memory').string
        totalMemory = int(totalMemory) /1024
        freeMemory = connection.getFreeMemory()/(1024*1024)
        freeMemory = int(freeMemory)
        print "Outside Loop"
        print freeMemory
        allocatedCPU = 0
        allocatedMemory =0
        c.execute("SELECT * from resource where pmid = ?",(loop,))
        for record in c.fetchall():
            allocatedCPU = allocatedCPU + record[4]
        
        if requestCPU <= (totalCPU- allocatedCPU) and requestMemory <= (freeMemory):
            print allocatedCPU
            print freeMemory
            f = open('vm.xml', 'r+')
            text = f.read()
            name = vmName
            name = '<name>' + name + '</name>'
            text = re.sub('<name>.*</name>',name , text)

            newuu = uuid.uuid1()
            newuu = '<uuid>'+ str(newuu) +'</uuid>'
            text = re.sub('<uuid>.*</uuid>',newuu , text)
            
            requestMem = requestMemory * 1024
            memreplace = '<memory unit=\'KiB\'>' +str(requestMem) +'</memory>'
            text = re.sub('<memory unit=\'KiB\'>.*</memory>',memreplace , text)


            memreplace = '<currentMemory unit=\'KiB\'>'+ str(requestMem) +'</currentMemory>'
            text = re.sub('<currentMemory unit=\'KiB\'>.*</currentMemory>',memreplace,text)

            cpureplace = '<vcpu placement=\'static\'>' + str(requestCPU)+ '</vcpu>'
            text = re.sub('<vcpu placement=\'static\'>.*</vcpu>',cpureplace,text)

            imageFilePathReplace = "\'" + imageFilePath + "\'"
            sourceReplace = '<source file=' + imageFilePathReplace +  '/>'
            text = re.sub('<source file=.*/>',sourceReplace,text)

            f.seek(0)
            f.write(text)
            f.truncate()
            f.close()
            xml = ""
            with open("vm.xml", "r") as file:  
                xml = file.read()
            connection.defineXML(xml)
            startVM = connection.lookupByName(vmName)
            startVM.create()
            vmidRandom = random.randint(1,50000)
            c.execute("INSERT INTO resource VALUES (?,?,?,?,?,?)",(loop,vmidRandom,instance_type,requestMemory,requestCPU,vmName) )     
            conn.commit()
            return str(vmidRandom)
        loop+=1    
    return '-1'

@app.route('/vm/query/')
def vmquery():
    vm_id = request.args.get('vmid')
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT vmid,name,instance_type,pmid from resource where vmid = ?",(vm_id,))
    dict = {}
    for record in c.fetchall():
        dict['vmid']=record[0]
        dict['name']=record[1]
        dict['instance_type']=record[2]
        dict['pmid']=record[3]
    return jsonify(dict)

@app.route('/vm/destroy/')
def vmdestroy():
    vm_id = request.args.get('vmid')
    vm_id=int(vm_id)
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT pmid from resource where vmid = ?",(vm_id,))
    tempvar=c.fetchone()[0]
    tempvar=int(tempvar)
    cmd = 'qemu+tcp://' + ipAddress[tempvar] + '/system'
    connection = libvirt.open(cmd)
    c.execute("SELECT name from resource where vmid = ?",(vm_id,))
    temvar=c.fetchone()[0]
    startVM = connection.lookupByName(temvar)
    startVM.destroy()
    c.execute("DELETE  from resource where vmid = ?",(vm_id,))
    conn.commit()
    return "1"

@app.route('/vm/types/')
def vmtypes():
    return jsonify(Displaying_Types=json_object)



@app.route('/pm/list/')
def pmlist():
    l=[]
    for lo in range(len(ipAddress)):
        l.append(lo)
    return jsonify(pmids=l)


@app.route('/pm/listvms/')
def listvms():
    pmidSearch = request.args.get('pmid')
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT vmid from resource where pmid = ?",(pmidSearch,))
    return jsonify(vmids=c.fetchall())



@app.route('/pm/query/')
def pmquery():
    pmidSearch = request.args.get('pmid')
    pmidSearch = int(pmidSearch)
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    ip = ipAddress[int(pmidSearch)]
    cmd = 'qemu+tcp://' + ip + '/system'
    connection = libvirt.open(cmd)
    p=connection.getCapabilities()
    soup = BeautifulSoup(p)
    a = soup.find('cpus')
    totalCPU = a['num']
    totalCPU = int(totalCPU)
    totalMemory = soup.find('memory').string
    totalMemory = int(totalMemory) /1024
    freeMemory = connection.getFreeMemory()/(1024*1024)
    freeMemory = int(freeMemory)
    result = {}
    result['pmid'] = pmidSearch
    temp1 = {'cpu':totalCPU,'ram':totalMemory}
    result['capacity'] = temp1
    
    allocatedCPU = 0
    c.execute("SELECT * from resource where pmid = ?",(pmidSearch,))
    counter =0
    for record in c.fetchall():
        allocatedCPU = allocatedCPU + record[4]
        counter = counter + 1

    allocatedCPU = totalCPU - allocatedCPU
    temp2 = {'cpu':allocatedCPU,'ram':freeMemory}
    result['free'] = temp2
    print counter
    result['vms'] = counter
    return jsonify(result)


@app.route('/image/list/')
def imageList():
    count = 0
    tlist = []
    result = {}
    for i in imageList:
        tlist.append( {'id':count+100, 'name':i} )
        count = count + 1
    result['images'] = tlist
    return jsonify(result)

@app.route('/volume/create/')
def createVolume():
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE if not exists volume(volumeid integer,pmid integer, vmid text, volumename text, status text, size integer)''')  
    volumename = request.args.get('name')
    volumesize = request.args.get('size')
    global countVols
    global noOfVols
    if(countVols > noOfVols):
        return "Error Cannot create volume due to over capacity"
    vidRandom = random.randint(1000,50000)
    pmStoreId=countVols/4
    voluneLocalMachineIP=ipAddress[pmStoreId]
    countVols+=1
    cmd = 'qemu+tcp://' + voluneLocalMachineIP + '/system'
    connection = libvirt.open(cmd)
    stgvol_xml = """
    <volume>
  <name>sparse.img</name>
  <allocation>0</allocation>
  <capacity unit="M">50</capacity>
  <target>
    <path>/home/pool/sparse.img</path>
    <permissions>
      <owner>107</owner>
      <group>107</group>
      <mode>0744</mode>
      <label>virt_image_t</label>
    </permissions>
  </target>
</volume>"""
    pool = 'test'
    name=volumename+'.img'
    memreplace = '<name>' + name +'</name>'
    stgvol_xml = re.sub('<name>.*</name>',memreplace ,stgvol_xml)  
    memreplace = '<capacity unit=\"M\">' +volumesize+ '</capacity>'
    stgvol_xml = re.sub('<capacity unit=\"M\">.*</capacity>',memreplace ,stgvol_xml)
    # print(stgvol_xml)
    pool = connection.storagePoolLookupByName(pool)
    stgvol = pool.createXML(stgvol_xml, 0)
    c.execute("INSERT INTO volume VALUES (?,?,?,?,?,?)",(vidRandom,pmStoreId,'0',volumename,'Available',int(volumesize)) )     
    conn.commit()
    result={}
    result['VolumeId']=vidRandom
    return jsonify(result)

# Destroy volumes
@app.route('/volume/destroy/')
def destroyVolume():
    volumeid= request.args.get('volumeid')
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT pmid,volumename from volume where volumeid = ?",(volumeid,))
    temp=c.fetchone()
    tempvar=temp[0]
    volName=temp[1]
    volName+='.img'
    tempvar=int(tempvar)
    print tempvar
    cmd = 'qemu+tcp://'+ipAddress[tempvar]+'/system'
    connection = libvirt.open(cmd)
    pool=connection.storagePoolLookupByName('test')
    svol = pool.storageVolLookupByName(volName)
    svol.delete(0)
    c.execute("UPDATE volume SET status= ? where volumeid = ?",("Deleted",volumeid,))
    conn.commit()
    return "Success"

# Volume Query
@app.route('/volume/query/')
def queryVolume():
    volumeid= request.args.get('volumeid')
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT * from volume where volumeid = ?",(volumeid,))
    temp=c.fetchone()
    dict={}
    dict['voumeid']=temp[0]
    dict['volumename']=temp[3]
    dict['volumesize']=temp[5]
    dict['volumestatus']=temp[4]
    if(temp[4] == 'Deleted'):
        return "error : volumeid :"+str(temp[0])+ " does not exist"
    elif(temp[4] == 'Available'):
        return jsonify(dict)
    else:
        dict['VmId']=temp[2]
    return jsonify(dict)

# Volume Attach
@app.route('/volume/attach/')
def attachVolume():
    vmid=request.args.get('vmid')
    volumeid= request.args.get('volumeid')
    volumeid=int(volumeid)
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("UPDATE volume SET status= ?,vmid=? where volumeid = ?",("Attached",vmid,volumeid,))
    conn.commit()
    c.execute("SELECT * from volume where volumeid = ?",(volumeid,))
    temp=c.fetchone()
    # print temp[3]
    template =\
'''<disk type='file' device='disk'>
      <driver name='qemu' type='raw'/>
      <name>hello</name>
      <target dev='sda' bus='scsi'/>
      <alias name='virtio0-0-0'/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>
'''
    name='<source file=\"/home/pool/'
    name+=temp[3]
    name+='.img\"/>'
    template = re.sub('<name>.*</name>',name ,template)
    print template
    c.execute("SELECT name from resource where vmid = ?",(vmid,))
    xtemp=c.fetchone()
    print temp[1]
    cmd = 'qemu+tcp://'+str(ipAddress[int(temp[1])])+'/system'
    connection = libvirt.open(cmd)

    # pool=connection.storagePoolLookupByName('test')
    # dom = pool.storageVolLookupByName(temp[3]+".img")
    dom = connection.lookupByName(xtemp[0])
    print xtemp[0]
    dom.attachDevice(template)
    return "Success"


# Volume detach
@app.route('/volume/detach/')
def detachVolume():
    volumeid=request.args.get('volumeid')
    conn = sqlite3.connect('orchestration1.db')
    c = conn.cursor()
    c.execute("SELECT * from volume where volumeid = ?",(volumeid,))
    temp=c.fetchone()
    template =\
'''<disk type='file' device='disk'>
      <driver name='qemu' type='raw'/>
      <name>hello</name>
      <target dev='sda' bus='scsi'/>
      <alias name='virtio0-0-0'/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>
'''
    name='<source file=\"/home/pool/'
    name+=temp[3]
    name+='.img\"/>'
    template = re.sub('<name>.*</name>',name ,template)
    c.execute("SELECT name from resource where vmid = ?",(temp[2],))
    xtemp=c.fetchone()
    cmd = 'qemu+tcp://'+str(ipAddress[int(temp[1])])+'/system'
    connection = libvirt.open(cmd)
    dom = connection.lookupByName(xtemp[0])
    dom.detachDevice(template)
    return "Success"


if __name__ == '__main__':
    # global countVols
    # global noOfVols
    countVols=0
    noOfVols=0
    pm_file = sys.argv[1]
    with open(pm_file) as f:
        ipAddress = f.readlines()
    index=0
    for i in ipAddress:
        ipAddress[index] = ipAddress[index].rstrip()
        index+=1

    image_file = sys.argv[2]
    with open(image_file) as f:
        imageList = f.readlines()
    
    json_file = sys.argv[3]
    with open(json_file) as json_file:
        json_object = json.load(json_file)
    index=0
    for i in imageList:
        imageList[index] = imageList[index].rstrip()
        index+=1
    noOfVols=len(ipAddress)*4
    app.run(host='127.0.0.1',debug=True)

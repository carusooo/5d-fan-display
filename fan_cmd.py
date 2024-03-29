# Import the socket library
import argparse
import math
import os
import socket
import sys
import time

__version = "0.3"


SERVER_ADDRESS = '192.168.4.1'
COMMAND_PORT = 5233
DATA_PORT = 5499
DATA_DELAY = 0.04

PACKET_SIZE      = 1460
TRANSFER_END = bytes([100, 51, 49, 100, 56, 56, 68, 69, 70, 97, 52, 97, 56, 99, 50, 101, 51])
PACKET_HEADER = bytes([100, 51, 49, 100, 56, 56, 74, 77, 80])
PACKET_TRAILER = bytes([48, 48, 48, 97, 52, 97, 56, 99, 50, 101, 51])


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Control a 224 LED holographic propeller display.\nVersion %s from https://github.com/jnweiger/led-hologram-propeller\n -- see there for more examples and for updates.' % __version, epilog="""
Commands:

  pause
    Stop the animation at the current frame. A constant image will be shown until a
    'play' command is sent.

  play
    Resume playing. Unpause.
                                 
  turn_off
    Stop the motor from spinning and power off the LEDs
                                 
  turn_on
    Start the motor begin displaying images

  upload FILE.bin
    Load a file into the device. The '.bin' suffix is mandatory and the file name cannot be longer than 8 characters.

""")

parser.add_argument('cmd', metavar='COMMAND', nargs='+', help="Command word.")
parser.add_argument('--command-help', action='version', help=argparse.SUPPRESS, version="--")
args = parser.parse_args()


play_last =     bytes([99, 51, 49, 99, 51, 51, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
play_loop1 =    bytes([99, 51, 49, 99, 51, 55, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
play_next =     bytes([99, 51, 49, 99, 51, 50, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
play_loop2 =    bytes([99, 51, 49, 99, 51, 54, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
play =          bytes([99, 51, 49, 99, 51, 52, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
pause =         bytes([99, 51, 49, 99, 51, 53, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
read_playlist = bytes([99, 51, 49, 99, 51, 56, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
turn_on_BLE =   bytes([99, 51, 49, 99, 52, 51, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
turn_off =      bytes([99, 51, 49, 99, 56, 57, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])
turn_on =       bytes([99, 51, 49, 99, 52, 53, 97, 98, 99, 97, 52, 97, 56, 99, 50, 101, 51])

def buf_bytes(b):
   return ', '.join([str(v) for v in b])

def send_bytes_to_device(byte_array):
    """
    Opens a socket connection to the specified IP and port, and sends the supplied byte array.
    """
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the server
        s.connect((SERVER_ADDRESS, COMMAND_PORT))
        try_recv(s, 0.1, True)
        # Send the byte array
        s.sendall(byte_array)
        print("Bytes sent successfully.")


def send_bytes_read_response(byte_array):
    """
    Opens a socket connection to the specified IP and port, and sends a predefined byte array.

    Args:
    ip (str): The IP address of the server.
    port (int): The port number to connect to on the server.

    Returns:
    None
    """
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the server
        s.connect((SERVER_ADDRESS, COMMAND_PORT))
        # Send the byte array
        s.sendall(byte_array)
        print("Bytes sent successfully.")
        resp = s.recv(1024)
        print(f"receivedResp %d: %s" % (len(resp), resp))


def build_send_file_name_message(ll, string):
    send_file_name_header = bytearray([100, 51, 49, 100, 54, 54, 68, 70])
    send_file_name_trailer = bytearray([97, 52, 97, 56, 99, 50, 101, 51])
    b_arr3 = bytearray(string.encode('GB18030'))
    length = len(b_arr3) + 61

    # Packing the data into bytes
    msg = send_file_name_header + bytes([length]) + bytes([(ll>>24)&0xff, (ll>>16)&0xff, (ll>>8)&0xff, ll&0xff])  +  b_arr3 + send_file_name_trailer
    print("sendFile:", msg)

    return msg

def try_recv(s, timeout=0.2, verbose=False):
  s.settimeout(timeout)       # seconds
  buf = ''
  try:
    buf = s.recv(1024)
    if buf and verbose:
      print(f"recv\n{buf_bytes(buf)}\n")
  except socket.timeout:
    pass
  s.settimeout(None)               # blocking
  return buf

def send_complete_message(s: socket):
    print("Sending complete message")
    msg = (bytearray([100, 51, 49, 100, 56, 56, 68, 69, 70, 97, 52, 97, 56, 99, 50, 101, 51]))
    s.send(msg)

def validate_send_bin_ready(b: bytes):
    valid_resp = bytes([100, 51, 48, 100, 54, 54, 68, 69, 74, 102, 102, 102, 102, 97, 52, 97, 56, 99, 50, 101, 51])
    return ('%s' % valid_resp) == ('%s' % b)

def playlist_slot(i: int):
    i_bytes = bytearray(("%02d" % i).encode('GB18030'))
    cmd_header = bytes([99, 51, 49, 99, 51, 57, 97, 98, 101])
    cmd_footer = bytes([97, 52, 97, 56, 99, 50, 101, 51])
    return cmd_header + i_bytes + cmd_footer

def bin_file_msg(buf: bytes):
    order_length = len(PACKET_HEADER) + len(buf) + len(PACKET_TRAILER)
    order = bytearray(order_length)

    header_index = 0
    footer_index = len(PACKET_HEADER) + len(buf)

    # Set these in little endian order
    order[header_index:header_index+len(PACKET_HEADER)] = PACKET_HEADER
    order[len(PACKET_HEADER):footer_index] = buf
    order[footer_index:] = PACKET_TRAILER
    return order


def upload_bin_file(file):
  print("upload_bin_file('%s', %d, '%s', %f)" % (SERVER_ADDRESS, DATA_PORT, file, DATA_DELAY))

  u = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  u.settimeout(3)               # seconds
  u.connect((SERVER_ADDRESS, DATA_PORT))
  try_recv(u, 0.1, False)

  fname = file.split('/')[-1]
  fname_b = bytes(fname, 'UTF-8')
  if fname[-4:] != '.bin':
    print("upload_file: ERROR: need a filename with '.bin' suffix. Got: '%s'" % fname)
    sys.exit(1)
  if len(fname_b) > 12:
    print("upload_file: ERROR: filename '%s' is %d bytes long. Maximum: 12" %(fname, len(fname_b)))
    sys.exit(1)

  fsize = os.stat(file).st_size
  chunksize = PACKET_SIZE - len(PACKET_HEADER) - len(PACKET_TRAILER)
  npackets = math.ceil(float(fsize)/chunksize)
  padsize = (npackets * chunksize) - fsize
  print("fsize=%d, chunksize=%d, npackets=%d, padsize=%d" % (fsize, chunksize, npackets, padsize))

  ll = fsize + padsize          #  include the padding here
  msg = build_send_file_name_message(ll, fname)
  n = u.send(msg)
  resp = try_recv(u, 1, True)
  if(not validate_send_bin_ready(resp)):
    print("ERROR: device not ready %s." % buf_bytes(resp))
    sys.exit(1)

  fd = open(file, 'rb')
  print(f"preparing to send {npackets} packets")
  for pkt in range(npackets):
    buf = fd.read(chunksize)
    blen = len(buf)
    if blen < chunksize:
      print("last packet=%d, padding needed=%d" % (pkt+1, chunksize-blen))
      if pkt+1 != npackets:
        print("ERROR: not the last packet, expected %d." % npackets)
        sys.exit(1)
      if chunksize-blen != padsize:
        print("ERROR: size mismatch, expected padding %d." % padsize)
        sys.exit(1)
      buf += b'0' * padsize      
    msg = bin_file_msg(buf)
    print(" %6.1f%%\r" % (100. * (pkt+1) / npackets), end='')
    n = u.send(msg)
    time.sleep(DATA_DELAY)            

  try_recv(u, 0.2, True)
  msg = TRANSFER_END
  # print(msg)
  n = u.send(msg)
  try_recv(u, 0.2, True)

  u.shutdown(socket.SHUT_RDWR)
  u.close()


if args.cmd[0] == 'pause':
  send_bytes_to_device(pause)

elif args.cmd[0] == 'play':
  send_bytes_to_device(play)

elif args.cmd[0] == 'turn_off':
  send_bytes_to_device(turn_off)

elif args.cmd[0] == 'turn_on':
  send_bytes_to_device(turn_on)

# elif args.cmd[0] == 'status':
#   n = s.send(b"c0eeb7c9baa3020000000014cc" + b"38" + b"lfhbfb5d2a2")
#   fmt_status(try_recv(s, 2.0, False))

# elif args.cmd[0] == 'del' or args.cmd[0] == 'delete':
#   if len(args.cmd) < 2:
#     print("ERROR: delete needs an INDEX parameter.")
#     sys.exit(1)
#   idx = int(args.cmd[1])
#   if idx <= 0 or idx > 99:
#     print("ERROR: delete INDEX must be > 1 and < 100. (%d seen)" % idx)
#     sys.exit(1)
#   n = s.send(b"c0eeb7c9baa3020000000014cc" + b"39" + b"lfj" + bytes("%02d" % idx, "UTF-8") + b"bfb5d2a2")
#   print("%d bytes sent." % n)

elif args.cmd[0] == 'upload':
  if len(args.cmd) < 2:
    print("ERROR: upload needs an binfile parameter.")
    sys.exit(1)
  upload_bin_file(args.cmd[1])

else:
  print("\nUnknown command '%s' -- try %s --help" % (args.cmd[0], sys.argv[0]))

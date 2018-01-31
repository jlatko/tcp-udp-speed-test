import time
import threading
import socket as sock
import math

HOST = "127.0.0.1"
MAX_SIZE = 50000
MAX_COUNT = 10000

def input_number(message, max_number):
    while True:
        try:
            number = int(raw_input(message))
            if number > 0 and number <= max_number:
                return number
            print "Value out of range 1-{}".format(max_number)
        except ValueError:
            print "Invalid input"

def create_packets(concat_packets, packet_count, packet_size, max_buffer_size):
    packets = ["x" * packet_size] * packet_count
    if concat_packets:
        whole_message = "".join(packets)
        packets = [ whole_message[i*max_buffer_size:(i+1)*max_buffer_size] for i in xrange(int(math.ceil(float(len(whole_message))/max_buffer_size)))]
    return packets, len(packets[0]) * (len(packets) - 1) + len(packets[-1])

def tcp_sender(tcp_socket, packets ):
    packet_size = len(packets[0])
    try:
        time.sleep(0.001)
        tcp_socket.send("SIZE:{}".format(packet_size).encode())
        for packet in packets:
            time.sleep(0.00001)
            tcp_socket.send(packet)
        tcp_socket.send("FINE".encode())
        tcp_socket.shutdown(sock.SHUT_RDWR)
        tcp_socket.close()
        print("Finished, press q to exit or anything else to send again: ")
    except sock.error as e:
        print e
        return

def send_udp(udp_socket, data, address):
    time.sleep(0.00001)
    udp_socket.sendto(data.encode(), address)

def udp_sender(udp_socket, packets, address, total_size):
    packet_size = len(packets[0])
    try:
        send_udp(udp_socket, "SIZE:{}".format(packet_size), address)
        time.sleep(0.0001)
        send_udp(udp_socket, "TOTAL:{}".format(total_size), address)
        time.sleep(0.0001)
        for packet in packets:
            send_udp(udp_socket, packet, address)
        time.sleep(0.0001)
        send_udp(udp_socket, "FINE", address)
    except sock.error as e:
        print e
        return

def send_both(tcp_socket, udp_socket, max_buffer_size, address):
    concat_packets =  raw_input("Concat packets? [y]:") == 'y'
    packet_size = input_number("Packet size: ", max_buffer_size)
    packet_count = input_number("How many packets: ", MAX_COUNT)

    try:
        tcp_socket.connect(address)
        message = tcp_socket.recv(10).decode()
        if message == "BUSY":
            print("server busy")
            return None, None
        elif message != "OK":
            print("unknown server response")
            return None, None
    except sock.error as e:
        print "Failed to connect to server. Error: " + e.strerror
        return None, None

    packets, total_size = create_packets(concat_packets, packet_count, packet_size, max_buffer_size)
    tcp_thread = threading.Thread(target=tcp_sender, args=(tcp_socket, packets,))
    udp_thread = threading.Thread(target=udp_sender, args=(udp_socket, packets, address, total_size))

    tcp_thread.start()
    udp_thread.start()
    return  tcp_thread, udp_thread


def configure_tcp(port):
    tcp_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    tcp_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    return tcp_socket

def main():
    port = input_number("Enter port: ", 65535)
    max_buffer_size = input_number("Enter max buffer size: ", MAX_SIZE)

    udp_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
    tcp_thread, udp_thread = None, None
    while True:
        if raw_input("Enter q to quit, or anything else to start sending: ") == "q":
            if (tcp_thread and tcp_thread.isAlive()) or (udp_thread and udp_thread.isAlive()):
                tcp_socket.shutdown(sock.SHUT_RDWR)
                udp_socket.close()
                udp_socket = None
                tcp_socket.close()
                if (tcp_thread and tcp_thread.isAlive()): tcp_thread.join()
                if (udp_thread and udp_thread.isAlive()): udp_thread.join()
            break
        elif not tcp_thread or not tcp_thread.isAlive():
            tcp_socket = configure_tcp(port)
            tcp_thread, udp_thread = send_both(tcp_socket, udp_socket, max_buffer_size, (HOST, port))
    if udp_socket: udp_socket.close()



if __name__ == "__main__":
    main()

import socket as sock
import time
import threading

FINISH = "FINE"

def input_number(message, max_number):
    while True:
        try:
            number = int(raw_input(message))
            if number > 0 and number < max_number:
                return number
            print("Value out of range 1-{}".format(max_number))
        except ValueError:
            print("Invalid input")

def get_buffer(s, packet_name):
    data = s.recv(1000).decode()
    return int(data[len(packet_name)+1:])

def print_udp(interval, received, expected):
    time_passed = interval[1] - interval[0]
    received_kb = len(received) * 8 / 1000.0
    packet_loss = 100 - received.count("x") * 100.0 / expected
    if time_passed:
        print("Thread UDP: received {} kb in time {} sec with the speed {} kb/sec. Packet loss: {} %".format(
            received_kb,
            time_passed,
            received_kb / time_passed,
            packet_loss
        ))
    else:
        print("time measured too short")

def print_tcp(interval, received):
    time_passed = interval[1] - interval[0]
    received_kb = len(received) * 8 / 1000.0
    if time_passed:
        print("Thread TCP: received {} kb in time {} sec with the speed {} kb/sec".format(
            received_kb,
            time_passed,
            received_kb / time_passed
        ))
    else:
        print("time measured too short")

def accept_clients(tcp_socket, udp_socket):
    tcp_t = None
    udp_t = None
    conn = None
    while True:
        try:
            conn = tcp_socket.accept()[0]
            if (tcp_t and tcp_t.isAlive()) or (udp_t and udp_t.isAlive()):
                conn.send("BUSY".encode())
                conn.close()
            else:
                conn.send("OK".encode())
                print("client connected")
                tcp_t = threading.Thread(target=receive_tcp, args=(conn, ))
                udp_t = threading.Thread(target=receive_udp, args=(udp_socket, ))
                tcp_t.start()
                udp_t.start()
        except sock.error as e:
            print(e.strerror)
            break
    if tcp_t and tcp_t.isAlive():
        if conn:
            conn.shutdown(sock.SHUT_RDWR)
            conn.close()
        tcp_t.join()
    if udp_t and udp_t.isAlive():
        udp_t.join()

def receive_udp(udp_socket):
    try:
        max_buffer_size = get_buffer(udp_socket, 'SIZE')
        expected = get_buffer(udp_socket, 'TOTAL')
    except ValueError:
        print "incorrect client message"
        return
    except sock.error as e:
        print(e.strerror)
        return

    received = ""
    start = time.time()
    while True:
        stop = time.time()
        try:
            data = udp_socket.recv(max_buffer_size)
            if data.decode() == FINISH:
                break
            else:
                received += data

        except sock.error:
            break
    print_udp((start, stop), received, expected)

def receive_tcp(conn):
    try:
        max_buffer_size = get_buffer(conn, 'SIZE')
    except ValueError:
        print "incorrect client message"
        conn.close()
        return
    except sock.error as e:
        print(e.strerror)
        conn.close()
        return

    received = ""
    start = time.time()
    while True:
        stop = time.time()
        try:
            data = conn.recv(max_buffer_size)
            if not data:
                print("connection prematurely ended")
                break
            if data.decode() == FINISH:
                break
            else:
                received += data
        except sock.error:
            break
    print_tcp((start, stop), received)
    conn.close()

def configure_tcp(port):
    tcp_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    tcp_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    tcp_socket.bind(('', port))
    tcp_socket.listen(10)
    print('TCP server ready...')
    return tcp_socket

def configure_udp(port):
    udp_socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
    udp_socket.bind(('localhost', port))
    # timeout is needed not to hang in the udp_thread
    udp_socket.settimeout(1)
    print('UDP server ready...')
    return udp_socket


def main():
    port = input_number("Enter port: ", 65535)

    tcp_socket = configure_tcp(port)
    udp_socket = configure_udp(port)

    accepting_thread = threading.Thread(target=accept_clients, args=(tcp_socket, udp_socket))
    accepting_thread.start()
    while True:
        c = raw_input("Type q for quit:\n")
        if c == "q":
            tcp_socket.shutdown(sock.SHUT_RDWR)
            tcp_socket.close()
            udp_socket.close()
            break
    accepting_thread.join()

if __name__ == "__main__":
    main()

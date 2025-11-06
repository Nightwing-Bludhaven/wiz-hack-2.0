#!/usr/bin/env python3
import socket
import json
import sys


class WizLight:
    def __init__(self, ip=None):
        self.ip = ip
        self.port = 38899

    def send_command(self, method, params=None):
        """Send UDP command to light"""
        if params is None:
            params = {}

        message = {"id": 1, "method": method, "params": params}

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.ip:
            # Send to specific light
            sock.sendto(json.dumps(message).encode(), (self.ip, self.port))
            sock.settimeout(1)
            try:
                response, _ = sock.recvfrom(1024)
                return json.loads(response.decode())
            except socket.timeout:
                return {"error": "No response from light"}
        else:
            # Broadcast to discover lights
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(json.dumps(message).encode(), ("255.255.255.255", self.port))

            lights = []
            sock.settimeout(2)
            while True:
                try:
                    response, addr = sock.recvfrom(1024)
                    lights.append(
                        {"ip": addr[0], "response": json.loads(response.decode())}
                    )
                except socket.timeout:
                    break
            return lights

    def discover(self):
        """Discover lights on network"""
        return self.send_command("getPilot")

    def get_state(self):
        """Get current state of light"""
        return self.send_command("getPilot")

    def set_state(self, state):
        """Turn light on/off"""
        return self.send_command("setState", {"state": state})

    def set_color(self, r, g, b, brightness=100):
        """Set light color and brightness"""
        return self.send_command(
            "setPilot", {"r": r, "g": g, "b": b, "dimming": brightness}
        )


def print_usage():
    print("""
Usage: python3 wiz_control.py <command> [args...]

Commands:
    discover            - Find all lights on network
    status <ip>        - Get status of specific light
    on <ip>           - Turn light on
    off <ip>          - Turn light off
    color <ip> r g b  - Set light color (0-255 for each value)
    """)


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command == "discover":
        light = WizLight()
        lights = light.discover()
        print("Discovered lights:")
        for light in lights:
            print(f"IP: {light['ip']}")
            print(f"Status: {json.dumps(light['response'], indent=2)}\n")

    elif command == "status" and len(sys.argv) == 3:
        ip = sys.argv[2]
        light = WizLight(ip)
        print(json.dumps(light.get_state(), indent=2))

    elif command == "on" and len(sys.argv) == 3:
        ip = sys.argv[2]
        light = WizLight(ip)
        print(json.dumps(light.set_state(True), indent=2))

    elif command == "off" and len(sys.argv) == 3:
        ip = sys.argv[2]
        light = WizLight(ip)
        print(json.dumps(light.set_state(False), indent=2))

    elif command == "color" and len(sys.argv) == 6:
        ip = sys.argv[2]
        r = int(sys.argv[3])
        g = int(sys.argv[4])
        b = int(sys.argv[5])
        light = WizLight(ip)
        print(json.dumps(light.set_color(r, g, b), indent=2))

    else:
        print_usage()


if __name__ == "__main__":
    main()

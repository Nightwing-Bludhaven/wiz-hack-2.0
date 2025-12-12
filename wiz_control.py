#!/usr/bin/env python3
import socket
import json
import sys


class WizLight:
    def __init__(self, ip=None):
        self.ip = ip
        self.port = 38899

    def send_command(self, method, params=None, wait_for_response=True):
        """
        Send UDP command to light.
        
        Args:
            method (str): The Wiz API method (e.g., setPilot)
            params (dict): Parameters for the method
            wait_for_response (bool): If False, sends "fire & forget" (OPTIMIZADO PARA WIFI 2.4GHz)
        """
        if params is None:
            params = {}

        message = {"id": 1, "method": method, "params": params}
        json_command = json.dumps(message).encode()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            if self.ip:
                # Send to specific light
                sock.sendto(json_command, (self.ip, self.port))
                
                if wait_for_response:
                    sock.settimeout(0.5) # Timeout optimizado para Wiz 8.5W
                    try:
                        response, _ = sock.recvfrom(1024)
                        return json.loads(response.decode())
                    except socket.timeout:
                        return {"error": "Timeout waiting for light"}
                    except Exception as e:
                        return {"error": str(e)}
                else:
                    # Modo "Music Visualizer": No esperamos respuesta para reducir LAG en 2.4GHz
                    return {"success": True, "info": "Command sent (no wait)"}
            else:
                # Broadcast (Discover) - Siempre necesita respuesta
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(json_command, ("255.255.255.255", self.port))

                lights = []
                sock.settimeout(2.0)
                while True:
                    try:
                        response, addr = sock.recvfrom(1024)
                        resp_json = json.loads(response.decode())
                        if not any(l['ip'] == addr[0] for l in lights):
                            lights.append({"ip": addr[0], "response": resp_json})
                    except socket.timeout:
                        break
                return lights
        finally:
            sock.close()

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
        """
        Set light color and brightness.
        AUTOMÁTICAMENTE EN MODO RÁPIDO (FIRE & FORGET)
        """
        # Wiz usa dimming 10-100. Si viene en 255, lo normalizamos.
        if brightness > 100:
            brightness = int((brightness / 255) * 100)
        
        # Seguridad para tus Wiz 8.5W
        brightness = max(10, min(100, int(brightness)))
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        # Aquí está la magia: wait_for_response=False
        return self.send_command(
            "setPilot", 
            {"r": r, "g": g, "b": b, "dimming": brightness},
            wait_for_response=False 
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
        # En modo manual sí esperamos respuesta para ver el JSON
        print(json.dumps(light.set_color(r, g, b), indent=2))

    else:
        print_usage()


if __name__ == "__main__":
    main()
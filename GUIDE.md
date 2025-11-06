Aleksandr Rogozin
Hacking Philips Wiz lights via command line
Ever since I have discovered Philips Wiz lights at Home Depot, I’ve been inspired to integrate them into my life for a more personal experience. These lights are bright (1k+ lumen), cheap (<$20 for bulbs) and have decent amount of basic integration in Wiz app and IFTTT. I started with a very simple automation- every workday, turn the lights in my home office on at 9am and turn them off at 5pm. Wiz app is great at handling such schedules, especially since you have to use the Wiz app for lights’ setup anyway.

However, there are few noticeable opportunities in Wiz app that are currently missing: ability to create your own scenes that provide dynamic color changes and integration with personal tools like your work calendar. This made me want to look into other ways I can interact with Philips Wiz. It turns out that there is no official API at the moment, but one can manage the lights by sending JSON payloads via UDP to individual IP addresses of each light on port 38899. You can find IP address and other technical information in Wiz app. After you find IP address, you can issue some example commands:

# Get parameters for Philips Wiz light
echo '{"method":"getPilot","params":{}}' | nc -u -w 1 192.168.87.72 38899
# Example of a successful response
{
  "method": "getPilot",
  "env": "pro",
  "result": {
    "mac": "6c<redacted>6",
    "rssi": -46,
    "src": "",
    "state": true,
    "sceneId": 0,
    "r": 255,
    "g": 238,
    "b": 0,
    "c": 0,
    "w": 0,
    "dimming": 100
  }
}
During my research, I have heavily relied on documentation from sbidy/pywizlight. Please refer to that repo for parameters and methods.

Now that I have seen Wiz light respond to my simple command, I tried setting it to blue color using setPilot method.

# Set Philips Wiz light to blue
echo '{"id":1,"method":"setPilot","params":{"r":0,"g":0,"b":255,"dimming":100}}' | nc -u -w 1 192.168.87.72 38899
Another neat trick you can do is turn light on/off using setState method.

# Turn on Philips Wiz light
echo '{"id":1,"method":"setState","params":{"state":true}}' | nc -u -w 1 192.168.87.72 38899
If you look over documentation in the repo I mentioned above, you will get an idea on the ways to interact with Philips Wiz light using UDP. As a last topic for today, I wanted to touch up on “discovery”. If you have a few lights on a network that can reserve IP addresses, hardcoding Philips Wiz  light IP addresses might be sufficient. In a dynamic environment with many lights, it might make sense to refresh lights’ metadata periodically in order to control them without the need to keep track of inventory. This statement covers a very basic use case though, we will control all the lights without differentiating their locations, light types, or any other important attribute. I will explore advanced organization and control of Philips Wiz during future hackdays.

To discover all lights, please make sure to connect to the same network as Philips Wiz lights. Next, instead of sending getPilot method meant to retrieve details from the individual light, we will send a UDP broadcast packet using socat utility.

# Send UDP broadcast packet
echo '{"method":"getPilot","params":{}}' | socat - UDP-DATAGRAM:255.255.255.255:38899,broadcast

# Example response from UDP broadcast requesting Philips Wiz light details
{"method":"getPilot","env":"pro","result":{"mac":"a8b<redacted>e","rssi":-79,"src":"","state":true,"sceneId":3,"speed":100,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"a8b<redacted>4","rssi":-60,"src":"","state":false,"sceneId":11,"temp":2700,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>5","rssi":-32,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>7","rssi":-37,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>f","rssi":-35,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>6","rssi":-47,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>7","rssi":-42,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"6c2<redacted>d","rssi":-41,"src":"","state":true,"sceneId":18,"dimming":100}}
{"method":"getPilot","env":"pro","result":{"mac":"a8b<redacted>8","rssi":-69,"src":"","state":false,"sceneId":29,"dimming":35}}
{"method":"getPilot","env":"pro","result":{"mac":"a8b<redacted>6","rssi":-78,"src":"","state":false,"sceneId":29,"dimming":36}}
With this information, you are now able to list Philips Wiz lights along with their status and details. Having this information unlocks a lot of new and interesting hacking opportunities that I will be eager to explore in the near future!
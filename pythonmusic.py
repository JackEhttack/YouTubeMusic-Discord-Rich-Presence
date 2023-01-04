import socketserver, time, json
from pypresence import Presence
from threading import Timer

#################################
# Put your application ID in here:
client_id = "1013299217139245166"
# Thanks.
#################################

rp = Presence(client_id)

# Indictates whether RPC is connected or not.
connected = False

def kill():
    """
    Disconnects RPC when you've stopped using YTM.
    """
    global connected
    if connected:
        rp.close()
        connected = False

# This timer is a placeholder, ignore it.
currentCountdown = Timer(180, kill)

def timeToSeconds(clock):
    """
    Converts the "12:34" format into seconds.
    clock: "12:34" format of time.
    returns: clock converted into seconds.
    """
    temp = 0
    
    for k, v in enumerate(reversed(clock.split(":"))):
        temp += int(v) * 60 ** k
    
    return temp

class HandlerClass(socketserver.BaseRequestHandler):

    def handle(self):
        """
        This is where the magic happens:
        Takes the Chrome Extensions POST, decodes it, and passes it to pypresence to make it work.
        Now with auto-disconnect so your friends don't think you are listening to anime OPs every hour of the day.
        """
        
        global currentCountdown, connected
        
        #Really gross code, but it's compact. Takes the HTTP POST from the extension, decodes it into utf-8, seperates by newline characters and takes the last one (the data), and gets rid of random \\n characters.
        self.data = self.request.recv(1024).strip().decode("utf-8", "strict").split("\n")[-1].replace("\\n", "")
        print(self.data)
        
        #Sometimes a blank POST is received, ignore it.
        if self.data == "":
            return
        
        self.data = json.loads(self.data)
        
        #Reconnects RPC so it can be turned off later.
        if not connected:
            rp.connect()
            connected = True
        
        #A near carbon copy of DevDenis's code, now with buttons that typically exposes the playlist you are listening to instead of the song. TODO
        rp.update(
            state=self.data["artist"],
            details=self.data["song"],
            large_image="ytm",
            small_image="play",
            start=time.time(),
            end=timeToSeconds(self.data["timeMax"].strip()) + time.time(),
            #buttons=[{"label": "Listen Along", "url":self.data["url"]}]
            )
        
        #Auto Disconnect if no new song is provided after song_length + 5 seconds.
        if currentCountdown:
            currentCountdown.cancel()
        currentCountdown = Timer(timeToSeconds(self.data["timeMax"].strip()) + 5, kill)
        currentCountdown.start()
        

if __name__ == "__main__":
    host, port = "localhost", 3000
    
    with socketserver.TCPServer((host, port), HandlerClass) as server:
        server.serve_forever()
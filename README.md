# UDP Audio server
Client/Server communication built upon UDP socket.
Client can stream through .wav or by recording audio from input device
## Install
1.Clone
```bash
git clone https://github.com/iae94/UDPAudio.git
```

2.Install
```bash
pip install -r requirements.txt
```

## Usage
### Server
```bash
python server.py --host localhost --port 5001
```
### Client
Sound recording and streaming for 10 seconds
```bash
python client.py --type voice --duration 10
```
Streaming from .wav
```bash
python client.py --type wav --file sample.wav
```
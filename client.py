import wave
import sys
import socket
import pyaudio
import os
import logging
import argparse
from typing import Optional
import time


class UDPClient:
    """
    Abstract class for udp clients
    """
    def __init__(self):
        """
        Create UDP socket
        """
        self.client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def ping(self, server_host: str, server_port: int):
        """
        Ping server sending PING and awaiting PONG
        :param server_host: udp host to ping
        :param server_port: udp port to ping
        :return:
        """
        # Send PING to server
        logger.info(f'Ping {(server_host, server_port)}')
        self.client.sendto(b'PING', (server_host, server_port))

        # Wait response from server (5 sec timeout)
        self.client.settimeout(5)
        try:
            pong, _ = self.client.recvfrom(1024)
        except socket.timeout as e:
            raise Exception(f"UDP server is unavailable -> {e}") from None
        else:
            logger.info(f"UDP server response with {pong.decode()}!")

    def send(self, *args, **kwargs):
        raise NotImplementedError


class WavClient(UDPClient):
    """
    Client for .wav files streaming
    """
    def __init__(self, wav_file: str):
        super().__init__()

        # Check file exists
        if not os.path.exists(wav_file):
            raise FileNotFoundError(f"Wav file: {wav_file} does not exists!")
        self.wav_file = wav_file

    def send(self, server_host: str, server_port: int):
        """
        Open .wav file and stream to server
        :param server_host: udp host to ping
        :param server_port: udp port to ping
        :return:
        """
        self.ping(server_host, server_port)     # Check server still alive
        try:
            with wave.open(os.path.abspath(self.wav_file), 'r') as wf:
                batch = 1024
                data = wf.readframes(batch)     # Read by frame batch
                success_datagrams_count = 0     # Successfully sent
                failed_datagrams_count = 0      # Not sent
                logger.info("Start streaming...")
                while data != b'':
                    try:
                        # Send datagram
                        self.client.sendto(data, (server_host, server_port))
                        logger.info(f'Send datagram -> {success_datagrams_count}')
                        data = wf.readframes(batch)
                        time.sleep(0.0001)   # If sent without some delay then packets will be lost on the udp server side(too fast)
                    except Exception as e:
                        logger.warning(f"Failed to send datagram -> {e}")
                        failed_datagrams_count += 1
                    else:
                        success_datagrams_count += 1
            logger.info(f"File streaming complete: {self.wav_file} ({success_datagrams_count}:{success_datagrams_count + failed_datagrams_count} datagrams)")
        except Exception as e:
            raise e
        finally:
            self.client.close()


class VoiceClient(UDPClient):
    """
    Client for real time audio stream from input device
    """
    def __init__(self, duration: int, input_device_index: Optional[int]):
        super().__init__()
        self.duration = duration
        self.input_device_index = input_device_index

    def select_input_device(self, p: pyaudio.PyAudio):
        """
        Search device and its parameters
        :param p: pyaudio.PyAudio instance
        :return: tuple(device_index, input_channels, sample_rate)
        """
        if self.input_device_index is not None:
            try:
                device = p.get_device_info_by_host_api_device_index(0, self.input_device_index)
            except OSError as e:
                logger.warning(f"There is no device with index: {self.input_device_index} -> {e}")
            else:
                return self.input_device_index, device.get('maxInputChannels'), int(device.get('defaultSampleRate'))

            info = p.get_host_api_info_by_index(0)
            for i in range(info.get('deviceCount')):
                device = p.get_device_info_by_host_api_device_index(0, i)
                if device.get('maxInputChannels') > 0:
                    logger.info(f"Use device: {device.get('name')}")
                    return i, device.get('maxInputChannels'), int(device.get('defaultSampleRate'))
            else:
                raise Exception("There are no input devices!")

    def send(self, server_host: str, server_port: int):
        """
        Open stream from input device through pyaudio.PyAudio() interface and stream to server per chunk size
        :param server_host: udp host to ping
        :param server_port: udp port to ping
        :return:
        """
        p = pyaudio.PyAudio()              # Create an interface to PortAudio

        # Search input device
        device_index, channels, sample_rate = self.select_input_device(p)
        chunk = 1024                       # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16    # 16 bits per sample

        self.ping(server_host, server_port)     # Check server still alive

        logger.info(f'Start recording {self.duration} sec...')
        # Open stream
        stream = p.open(
            format=sample_format,
            channels=channels,                  # Device input channels
            input_device_index=device_index,    # Device index
            rate=sample_rate,                   # Samples per second
            frames_per_buffer=chunk,
            input=True
        )
        try:
            # Chunks for self.duration seconds
            chunks = int(sample_rate / chunk * self.duration)
            for i in range(chunks):
                data = stream.read(chunk)
                self.client.sendto(data, (server_host, server_port))
                logger.info(f'Send datagram -> {i}:{chunks}')

        except Exception as e:
            raise e
        finally:
            # Close streams
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.client.close()


if __name__ == '__main__':
    # Simple Logger
    logger = logging.getLogger('client')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] - %(name)-10s - %(module)-10s - [%(levelname)-8s] - %(threadName)-10s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    #VoiceClient(5, 15).send('localhost', 5001)
    #WavClient('output.wav').send('localhost', 5001)
    #exit()

    # Parse arguments
    parser = argparse.ArgumentParser(description="audio/wav streaming client")
    parser.add_argument('-uh', '--host', type=str, action='store', help='udp server host', default='localhost')
    parser.add_argument('-up', '--port', type=int, action='store', help='udp server port', default=5001)
    parser.add_argument('-t', '--type', required=True, action='store', type=str, choices=['wav', 'voice'], help='can be \"wav\" if stream from file or \"voice\" if stream from input device', default='voice')
    parser.add_argument('-f', '--file', type=str, help='.wav file')
    parser.add_argument('-d', '--duration', type=int, help='recording seconds')
    parser.add_argument('-di', '--device', type=int, help='input device index', default=1)

    # Check required args
    args = parser.parse_args()
    if args.type == 'wav':
        if not args.file:
            parser.error("the following argument are required: \"-f/--file\" if type is \"wav\"")
        client = WavClient(wav_file=args.file)
    elif args.type == 'voice':
        if not args.duration:
            parser.error("the following argument are required: \"-d/--duration\" if type is \"voice\"")
        client = VoiceClient(duration=args.duration, input_device_index=args.device)
    else:
        parser.error(f"Unknown client type: \"{args.type}\"")

    logger.info(f"Create client with args: {args}")
    client.send(server_host=args.host, server_port=args.port)
    logger.info('Done!')


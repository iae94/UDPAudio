import subprocess

if __name__ == '__main__':

    clients = [
        ['python', 'client.py', '--type', 'voice', '--duration', '5'],
        ['python', 'client.py', '--type', 'wav', '--file', 'sample.wav'],
        ['python', 'client.py', '--type', 'voice', '--duration', '10'],
        ['python', 'client.py', '--type', 'wav', '--file', 'sample.wav'],
        ['python', 'client.py', '--type', 'voice', '--duration', '15'],
        ['python', 'client.py', '--type', 'wav', '--file', 'sample.wav'],
        ['python', 'client.py', '--type', 'voice', '--duration', '20'],
        ['python', 'client.py', '--type', 'wav', '--file', 'sample.wav'],
    ]
    [subprocess.Popen(client) for client in clients]






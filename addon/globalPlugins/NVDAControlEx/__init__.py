import globalPluginHandler
import speech
import ctypes
from threading import Thread
import argparse
import shlex

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    # Define commands and their expected arguments
    pipeCommands = {
        "speak": {
            "function": speech.speakText,
            "args": ["text"]
        },
        "speakSpelling": {
            "function": speech.speakSpelling,
            "args": ["text"]
        },
        "speakSsml": {
            "function": speech.speakSsml,
            "args": ["ssml"]
        },
        "pauseSpeech": {
            "function": speech.pauseSpeech,
            "args": ["switch"]
        },
        "cancelSpeech": {
            "function": speech.cancelSpeech,
            "args": []
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipe_name = r'\\.\pipe\NVDAControlPipe'
        self.h_pipe = ctypes.windll.kernel32.CreateNamedPipeW(
            self.pipe_name,
            0x00000003,  # PIPE_ACCESS_DUPLEX
            0x00000004 | 0x00000002 | 0x00000000,  # PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT
            1,  # PIPE_UNLIMITED_INSTANCES
            100000,  # Out buffer size
            100000,  # In buffer size
            0,  # Default timeout
            None  # Security attributes
        )

        if self.h_pipe == 0:
            return None

        # Start a thread to listen for commands
        t = Thread(target=self.read_task)
        t.start()

    def __del__(self):
        if self.h_pipe:
            ctypes.windll.kernel32.CloseHandle(self.h_pipe)
            self.h_pipe = None

    def read_task(self):
        buffer_size = 1024
        while True:
            result = ctypes.windll.kernel32.ConnectNamedPipe(self.h_pipe, None)
            if result == 0:
                break

            try:
                while True:
                    buffer = ctypes.create_string_buffer(buffer_size)
                    bytes_read = ctypes.c_ulong(0)
                    read_result = ctypes.windll.kernel32.ReadFile(
                        self.h_pipe,
                        buffer,
                        buffer_size,
                        ctypes.byref(bytes_read),
                        None
                    )

                    if read_result == 0 or bytes_read.value == 0:
                        break

                    received_data = buffer.value.decode('utf-8')
                    self.process_command(received_data)

            finally:
                ctypes.windll.kernel32.DisconnectNamedPipe(self.h_pipe)

    def process_command(self, command_str):
        """
        Parse and execute a command received from the named pipe.
        """
        try:
            # Split the command into parts
            parts = shlex.split(command_str)
            if not parts:
                return

            command = parts[0]
            if command not in self.pipeCommands:
                print(f"Unknown command: {command}")
                return

            # Get the command details
            command_info = self.pipeCommands[command]
            func = command_info["function"]
            expected_args = command_info["args"]

            # Parse arguments
            parser = argparse.ArgumentParser(description=f"Process {command} command.")
            for arg in expected_args:
                parser.add_argument(arg)

            # Extract arguments from the command
            args = parser.parse_args(parts[1:])

            # Call the function with the parsed arguments
            if expected_args:
                func(**vars(args))
            else:
                func()

        except Exception as e:
            print(f"Error processing command '{command_str}': {e}")

import globalPluginHandler
import speech
from braille import BrailleHandler
import ctypes
from threading import Thread, Event
import argparse
import shlex

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	brailleHandler = BrailleHandler()
	# Define commands and their expected arguments
	pipeCommands = {
		"speak": {
			"function": speech.speakText,
			"args": ["text", "reason", "symbolLevel"]
		},
		"speakSpelling": {
			"function": speech.speakSpelling,
			"args": ["text", "locale", "useCharacterDescriptions"]
		},
		"speakSsml": {
			"function": speech.speakSsml,
			"args": ["ssml", "markCallback", "symbolLevel"]
		},
		"pauseSpeech": {
			"function": speech.pauseSpeech,
			"args": ["switch"]
		},
		"cancelSpeech": {
			"function": speech.cancelSpeech,
			"args": []
		},
		"braille": {
			"function": brailleHandler.message,
			"args": ["text"]
		},
		"active": {
			"function": lambda: None,
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

		if self.h_pipe == -1:  # INVALID_HANDLE_VALUE
			raise ctypes.WinError()

		self.stop_event = Event()
		# Start a thread to listen for commands
		self.thread = Thread(target=self.read_task)
		self.thread.start()

	def __del__(self):
		self.stop_event.set()
		if self.h_pipe and self.h_pipe != -1:
			ctypes.windll.kernel32.CloseHandle(self.h_pipe)
			self.h_pipe = None
		if self.thread and self.thread.is_alive():
			self.thread.join()

	def read_task(self):
		buffer_size = 1024
		while not self.stop_event.is_set():
			try:
				result = ctypes.windll.kernel32.ConnectNamedPipe(self.h_pipe, None)
				if result == 0:
					error = ctypes.get_last_error()
					if error == 535:  # ERROR_PIPE_CONNECTED
						pass
					else:
						raise Exception(f"NVDAControlInterfacePipeError: WinError {error}")

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
					continue

				received_data = buffer.value.decode('utf-8')
				self.process_command(received_data)

				ctypes.windll.kernel32.DisconnectNamedPipe(self.h_pipe)
			except Exception as e:
				print(f"Error in read_task: {e}")
				continue

	def process_command(self, command_str):
		"""
		Parse and execute a command received from the named pipe.
		"""
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
			parser.add_argument(arg, type=self._arg_type_converter)

		# Extract arguments from the command
		try:
			args = parser.parse_args(parts[1:])
		except SystemExit:
			return  # argparse exits on error, catch it to avoid stopping the plugin

		# Call the function with the parsed arguments
		if expected_args:
			func(**vars(args))
		else:
			func()

	def _arg_type_converter(self, value):
		"""
		Convert the argument value to the appropriate type.
		"""
		if value.lower() in ('true', 'false'):
			return value.lower() == 'true'
		try:
			return int(value)
		except ValueError:
			try:
				return float(value)
			except ValueError:
				return value


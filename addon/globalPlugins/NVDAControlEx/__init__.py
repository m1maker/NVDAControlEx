import globalPluginHandler
import speech
import ctypes
from threading import Thread


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	pipeCommands = {
		"speak" : speech.speakText,
		"speakSpelling" : speech.speakSpelling,
		"speakSsml" : speech.speakSsml,
		"pauseSpeech" : speech.pauseSpeech,
		"cancelSpeech" : speech.cancelSpeech
	}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.pipe_name = r'\\.\pipe\NVDAControlPipe'
		self.h_pipe = ctypes.windll.kernel32.CreateNamedPipeW(
			self.pipe_name,
			0x00000003,
			0x00000004 | 0x00000002 | 0x00000000,
			1,
			100000,
			100000,
			0,
			None
		)

		if self.h_pipe == 0:
			return None

		t = Thread(target = self.read_task)
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

					command_parts = received_data.split(' ', 1)
					command = command_parts[0]
					if command in self.pipeCommands:
						args = command_parts[1] if len(command_parts) > 1 else ""
						self.pipeCommands[command](args)

					if command == "exit":
						break

			finally:
				ctypes.windll.kernel32.DisconnectNamedPipe(self.h_pipe)

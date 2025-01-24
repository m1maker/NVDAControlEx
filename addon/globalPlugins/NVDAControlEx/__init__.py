import globalPluginHandler
import speech
import ctypes

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

		if self.h_pipe == ctypes.windll.kernel32.INVALID_HANDLE_VALUE:
			return None

	def __del__(self):
		if self.h_pipe:
			ctypes.windll.kernel32.CloseHandle(self.h_pipe)
			self.h_pipe = None

# NVDA Control Ex Add-on Documentation

## Overview

The NVDA Control Ex Add-on provides a named pipe interface (`\\.\pipe\NVDAControlPipe`) for external applications to send commands to NVDA. These commands can control speech output, braille display, and other NVDA functionalities.

## Key Features

1. **Named Pipe Communication**:
   - The add-on creates a named pipe (`\\.\pipe\NVDAControlPipe`) to receive commands from external applications.
   - Commands are sent as strings and processed by the plugin.

2. **Supported Commands**:
   - The add-on supports the following commands:
     - `speak`: Speaks the provided text.
     - `speakSpelling`: Spells out the provided text.
     - `speakSsml`: Speaks SSML (Speech Synthesis Markup Language) content.
     - `pauseSpeech`: Pauses or resumes speech.
     - `cancelSpeech`: Cancels the current speech output.
     - `braille`: Displays the provided text on the braille display.
     - `active`: Responds with "NVDA" to confirm the add-on is active.

3. **Threaded Architecture**:
   - The add-on uses a separate thread to listen for incoming connections and process commands, ensuring that NVDA remains responsive.

---

## How to Use

### 1. **Install the Add-on**
   - Download the `NVDAControlEx` add-on from the [GitHub repository](https://github.com/m1maker/NVDAControlEx).
   - Install it in NVDA.

### 2. **Enable the Add-on**
   - Ensure the add-on is enabled in NVDA's Add-on Manager.

### 3. **Send Commands via Named Pipe**
   - External applications can send commands to NVDA by writing to the named pipe (`\\.\pipe\NVDAControlPipe`).
   - Commands are sent as strings in the following format:
     ```
     command_name arg1 arg2 ...
     ```
   - Example: To make NVDA speak "Hello, World!", send the following command:
     ```
     speak "Hello, World!" 0 -1
     ```

### 4. **Supported Commands and Arguments**

| Command         | Arguments                                                                 | Description                                                                 |
|-----------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `speak`         | `text`, `reason (unused)`, `symbolLevel`                                           | Speaks the provided text.                                                   |
| `speakSpelling` | `text`, `locale`, `useCharacterDescriptions`                              | Spells out the provided text.                                               |
| `speakSsml`     | `ssml`, `markCallback (unused)`, `symbolLevel`                                     | Speaks SSML content.                                                        |
| `pauseSpeech`   | `switch`                                                                  | Pauses or resumes speech.                                                   |
| `cancelSpeech`  | None                                                                      | Cancels the current speech output.                                          |
| `braille`       | `text`                                                                    | Displays the provided text on the braille display.                          |
| `active`        | None                                                                      | Responds with "NVDA" to confirm the add-on is active.                       |

---

## Example Usage

### Sending a Command from an External Application
To send a command to NVDA, you can use any programming language that supports Windows named pipes. Below is an example in C:
I will use interface from [this repo](https://github.com/m1maker/SRAL)
These files can be found in Dep directory, nvda_control.h and nvda_control.c

```c
#include <nvda_control.h>

int main() {
    // Step 1: Connect to the NVDA named pipe
    if (nvda_connect() != 0) {
        fprintf(stderr, "Failed to connect to NVDA.\n");
        return -1;
    }

    // Step 2: Send a command to speak some text
    const char* textToSpeak = "Hello, this is a test of the NVDA control interface.";
    int symbolLevel = NVDA_SYMBOL_LEVEL_ALL; // Use all punctuation

    if (nvda_speak(textToSpeak, symbolLevel) != 0) {
        fprintf(stderr, "Failed to send speak command to NVDA.\n");
        nvda_disconnect();
        return -1;
    }

    // Optional: Pause speech for demonstration
    if (nvda_pause_speech(1) != 0) {
        fprintf(stderr, "Failed to pause speech.\n");
    }

    // Wait for a few seconds (this is just for demonstration purposes)
    Sleep(3000); // Sleep for 3 seconds

    // Resume speech
    if (nvda_pause_speech(0) != 0) {
        fprintf(stderr, "Failed to unpause speech.\n");
    }

    // Step 3: Disconnect from NVDA
    nvda_disconnect();

    return 0;
}


```

---

## Troubleshooting

1. **Add-on Not Responding**:
   - Ensure the `NVDAControlEx` add-on is installed and enabled in NVDA.
   - Restart NVDA after installing the add-on.

2. **Named Pipe Connection Issues**:
   - Ensure the external application has the correct permissions to access the named pipe.
   - Check for errors in the NVDA log (accessible via NVDA's Log Viewer).

3. **Command Execution Errors**:
   - Verify that the command and arguments are correctly formatted.
   - Check the NVDA log for any error messages related to command execution.

---

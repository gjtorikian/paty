// Minimal macOS speech-to-text using Apple's Speech framework.
// Compiles with: swiftc -o transcribe transcribe.swift
// Usage: ./transcribe /path/to/audio.wav

import Foundation
import Speech

guard CommandLine.arguments.count > 1 else {
    fputs("usage: transcribe <audio-file>\n", stderr)
    exit(1)
}

let path = CommandLine.arguments[1]
let fileURL = URL(fileURLWithPath: path)

guard FileManager.default.fileExists(atPath: path) else {
    fputs("error: file not found: \(path)\n", stderr)
    exit(1)
}

var finished = false
var exitCode: Int32 = 0
let deadline = Date().addingTimeInterval(30)

// Check current authorization without blocking
let authStatus = SFSpeechRecognizer.authorizationStatus()

func doTranscribe() {
    guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US")),
          recognizer.isAvailable else {
        fputs("error: speech recognizer not available\n", stderr)
        exit(3)
    }

    let request = SFSpeechURLRecognitionRequest(url: fileURL)
    request.shouldReportPartialResults = false

    recognizer.recognitionTask(with: request) { result, error in
        if let error = error {
            fputs("error: \(error.localizedDescription)\n", stderr)
            exitCode = 4
            finished = true
            return
        }
        guard let result = result, result.isFinal else { return }
        print(result.bestTranscription.formattedString)
        finished = true
    }
}

switch authStatus {
case .authorized:
    doTranscribe()
case .notDetermined:
    SFSpeechRecognizer.requestAuthorization { status in
        if status == .authorized {
            doTranscribe()
        } else {
            fputs("error: speech recognition not authorized (check System Settings > Privacy > Speech Recognition)\n", stderr)
            exit(2)
        }
    }
default:
    fputs("error: speech recognition not authorized (check System Settings > Privacy > Speech Recognition)\n", stderr)
    exit(2)
}

// Pump the run loop instead of blocking with a semaphore
while !finished && Date() < deadline {
    RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.1))
}

if !finished {
    fputs("error: transcription timed out\n", stderr)
    exit(5)
}

exit(exitCode)

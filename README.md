# Money Under Pressure Studio

An Android-first production workspace for the Money Under Pressure YouTube channel.

## Current foundation

- Kotlin + Jetpack Compose Android app
- Dark navy interface with cyan and violet accents
- Video project creation form
- Script → visuals → render production pipeline
- GitHub Actions workflow to build a debug APK

## Build

Requires JDK 17 and Android SDK 35.

```bash
gradle assembleDebug
```

The debug APK is created at `app/build/outputs/apk/debug/app-debug.apk`.

## Product direction

The intended workflow is topic and research → script → storyboard → animated 2D scenes, charts and kinetic typography → MP4 export.

The current app is the interface foundation only. Rendering, project persistence, asset generation and export will be added in subsequent milestones.

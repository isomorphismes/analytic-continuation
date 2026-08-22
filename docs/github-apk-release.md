# GitHub APK release boundary

GitHub prereleases open directly into the live native convergence-disc explorer.
The direct-install APK also carries the two guided movies so CI can exercise the
same Android decoder path that previously produced blank playback; the launcher
still resolves to `ExplorerActivity`, not the movie viewer.

Before publication, CI renders and re-encodes both guided movies for Android,
builds all native ABIs, confirms the launcher resolves to `ExplorerActivity`,
installs the exact APK in an Android emulator, plays and captures both guided
movies, then launches the native explorer, captures a visibly rendered
EGL/OpenGL ES frame, touches the continuation view, and requires the resulting
native interaction log. Publication depends on that emulator job succeeding.

The APK is signed with the repository's public, test-only key so a later GitHub
APK can update an earlier one. Google Play uses a separate private upload key.

The public key alias and password are both `analytic-continuation-test`. Never
use `android/app/analytic-continuation-github-test.p12` for Google Play.

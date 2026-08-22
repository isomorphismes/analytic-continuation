# GitHub APK release boundary

GitHub prereleases open directly into the live native convergence-disc explorer.
The direct-install APK contains no guided movies and does not depend on Android
video playback. Google Play may package guided movies through its separate
workflow.

Before publication, CI builds all native ABIs, confirms the launcher resolves
to `ExplorerActivity`, installs the exact APK in an Android emulator, captures a
visibly rendered EGL/OpenGL ES frame, touches the continuation view, and checks
the resulting native log and screen.

The APK is signed with the repository's public, test-only key so a later GitHub
APK can update an earlier one. Google Play uses a separate private upload key.

The public key alias and password are both `analytic-continuation-test`. Never
use `android/app/analytic-continuation-github-test.p12` for Google Play.

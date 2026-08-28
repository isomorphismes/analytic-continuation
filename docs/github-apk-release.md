# GitHub APK release boundary

GitHub prereleases open directly into the live holomorphic-random explorer.
The direct-install APK contains no generated movies, and the launcher resolves
to `ExplorerActivity`.

Before publication, CI builds all native ABIs, confirms there are no MP4 movie
assets and that the launcher resolves to `ExplorerActivity`, installs the exact
APK in an Android emulator, captures a visibly rendered EGL/OpenGL ES frame,
exercises the flowing field, and requires the resulting native interaction log.
Publication depends on that emulator job succeeding.

The APK is signed with the repository's public, test-only key so a later GitHub
APK can update an earlier one. Google Play uses a separate private upload key.

The public key alias and password are both `analytic-continuation-test`. Never
use `android/app/analytic-continuation-github-test.p12` for Google Play.

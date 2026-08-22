# GitHub APK release boundary

GitHub prereleases open directly into the live native convergence-disc explorer
and contain two offline guided movies. The APK is signed with the repository's public,
test-only key so a later GitHub APK can update an earlier one. Google Play uses
a separate private upload key.

The guided movies are transcoded after ManimGL renders them. Direct-install APKs
require H.264 Constrained Baseline, level 3.0, 640×360, `yuv420p`, no B-frames,
and a fast-start MP4 index. These conservative settings target Android's
mandatory decoder rather than assuming optional High Profile support.

Before publication, CI checks that both source movies contain visible pixels,
builds all native ABIs, installs the APK, waits for Android to report the first
rendered video frame from each movie, captures both screens, launches and
touches the GLES explorer, and verifies the resulting native log and screen.

The public key alias and password are both `analytic-continuation-test`. Never
use `android/app/analytic-continuation-github-test.p12` for Google Play.

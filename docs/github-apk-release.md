# GitHub APK release boundary

The `apk-release` branch produces an installable prerelease for direct testing
on a phone or tablet. It renders the two bundled ManimGL movies, packages them
into the offline Android viewer, installs and starts the APK in an emulator,
then attaches the APK and its SHA-256 checksum to a GitHub prerelease.

The APK is signed with
`android/app/analytic-continuation-github-test.p12`. This is deliberately a
public, test-only key so later GitHub test APKs can update earlier ones without
depending on private Google Play credentials. Its alias is
`analytic-continuation-test`; its password is `analytic-continuation-test`.

Never use that key for Google Play. The Play workflow restores a separate
private upload key from the protected `google-play` environment and builds an
Android App Bundle. The two publication paths share the permanent package ID
`org.isomorphisms.analyticcontinuation`, but they do not share signing keys.

The initial push of the workflow publishes `v0.1.0`. Later versions can be
published by manually running `Build and publish APK` with a new semantic
version and increasing Android version code.

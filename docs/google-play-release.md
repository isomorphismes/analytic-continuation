# Google Play release boundary

ManimGL is a desktop Python renderer, not an Android runtime. The Android app in
this repository therefore does not claim to run Manim on a phone. CI renders the
named smoke movies on Linux and packages those MP4 files into a small offline
Android viewer.

The viewer's permanent package ID is
`org.isomorphisms.analyticcontinuation`, and it targets Android API 36. A later
interactive Android renderer can replace the viewer without changing that
package identity, but it should preserve the mathematical contracts in this
repository rather than embedding Python expression evaluation.

## GitHub environment and secrets

Create a protected environment named `google-play` with:

- `ANDROID_UPLOAD_KEYSTORE_BASE64`
- `ANDROID_UPLOAD_KEYSTORE_PASSWORD`
- `ANDROID_UPLOAD_KEY_ALIAS`
- `ANDROID_UPLOAD_KEY_PASSWORD`
- `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`

Enroll the app in Play App Signing. These Android secrets are for the separate
private upload key.

## First and later uploads

Create the Play application with the exact package ID above and complete its
store and policy declarations. Run `Google Play movie viewer` with
`destination: artifact-only`; it renders the two movies and returns a signed
`.aab` for the first manual Play Console upload.

After enabling the Google Play Developer API and granting its service account
access to the app, later runs may select `internal-track`. CI cannot target
production. Each upload needs an unused, increasing integer `version_code`.

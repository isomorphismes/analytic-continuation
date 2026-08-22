# Google Play release boundary

ManimGL is a desktop Python renderer, not an Android runtime. CI renders named
smoke movies on Linux and packages those MP4 files for offline viewing. The same
app also contains a native C/OpenGL ES 3 convergence-disc explorer adapted from
Wegert; it does not embed Python or Manim on the phone.

The app's permanent package ID is `org.isomorphisms.analyticcontinuation`, and
it targets Android API 36. Native builds include ARM64, ARMv7, and x86_64. The
release bundle therefore needs Android NDK r29 and CMake 3.22.1 in addition to
the Java/Android SDK toolchain.

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
store and policy declarations. Run `Android viewer and native convergence
explorer` with `destination: artifact-only`; it renders the two movies and
returns a signed `.aab` containing both the viewer and live explorer for the
first manual Play Console upload.

After enabling the Google Play Developer API and granting its service account
access to the app, later runs may select `internal-track`. CI cannot target
production. Each upload needs an unused, increasing integer `version_code`.

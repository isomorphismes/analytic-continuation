# Third-party and reused material

`LICENSE` applies to copyrightable material in this repository only where the repository's contributors have authority to grant that license. External dependencies, platform components, and separately identified material retain their own licenses.

## Wegert rendering core

The Android shader consumes the renderer-independent Wegert domain-coloring core from the sibling `isomorphisms/wegert` repository. CI compares the vendored build input byte-for-byte with Wegert's exported `code/wegert_color.glsl` so this repository does not silently develop a second palette implementation.

- https://github.com/isomorphisms/wegert

## Platform and toolchain

Android SDK/NDK components, Gradle, CMake, system libraries, and OpenGL ES interfaces are external to this repository and remain under their upstream terms.

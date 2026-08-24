import java.util.Base64

plugins {
    id("com.android.application")
}

val requestedVersionCode = System.getenv("PLAY_VERSION_CODE")
val appVersionCode = when {
    requestedVersionCode == null -> 3
    else -> requestedVersionCode.toIntOrNull()
        ?.takeIf { it in 1..2_100_000_000 }
        ?: error("PLAY_VERSION_CODE must be between 1 and 2100000000")
}
val appVersionName = System.getenv("PLAY_VERSION_NAME") ?: "0.1.2-lasso"

val uploadKeystorePath = System.getenv("ANDROID_UPLOAD_KEYSTORE_PATH")
val uploadKeystorePassword = System.getenv("ANDROID_UPLOAD_KEYSTORE_PASSWORD")
val uploadKeyAlias = System.getenv("ANDROID_UPLOAD_KEY_ALIAS")
val uploadKeyPassword = System.getenv("ANDROID_UPLOAD_KEY_PASSWORD")
val uploadSigningConfigured = listOf(
    uploadKeystorePath,
    uploadKeystorePassword,
    uploadKeyAlias,
    uploadKeyPassword,
).all { !it.isNullOrBlank() }

val sideloadKeystoreSource = file("debug/lasso-dev.p12.b64")
val sideloadKeystoreFile = layout.buildDirectory.file("sideload-signing/lasso-dev.p12").get().asFile
if (!sideloadKeystoreFile.exists()) {
    sideloadKeystoreFile.parentFile.mkdirs()
    sideloadKeystoreFile.writeBytes(
        Base64.getDecoder().decode(sideloadKeystoreSource.readText().trim())
    )
}

val wegertColorMarker = "/*__WEGERT_COLOR_CORE__*/"
val generatedWegertAssets = layout.buildDirectory.dir("generated/wegert-assets")
val assembleContinuationShader = tasks.register("assembleContinuationShader") {
    val template = file("src/main/assets/continuation.frag.in")
    val colorCore = file("src/main/assets/wegert_color.glsl")
    val output = generatedWegertAssets.map { it.file("continuation.frag") }

    inputs.files(template, colorCore)
    outputs.file(output)

    doLast {
        val templateText = template.readText()
        check(templateText.contains(wegertColorMarker)) {
            "Continuation fragment template is missing the Wegert coloring-core marker"
        }
        check(templateText.indexOf(wegertColorMarker) == templateText.lastIndexOf(wegertColorMarker)) {
            "Continuation fragment template must contain exactly one Wegert coloring-core marker"
        }

        val outputFile = output.get().asFile
        outputFile.parentFile.mkdirs()
        outputFile.writeText(templateText.replace(wegertColorMarker, colorCore.readText()))
    }
}

android {
    namespace = "org.isomorphisms.analyticcontinuation"
    compileSdk = 36
    ndkVersion = "29.0.14206865"

    defaultConfig {
        // Mainline/Play keeps the established application identity.
        applicationId = "org.isomorphisms.analyticcontinuation"
        minSdk = 26
        targetSdk = 36
        versionCode = appVersionCode
        versionName = appVersionName
        manifestPlaceholders["appLabel"] = "Analytic Continuation — Lasso"

        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")
        }

        externalNativeBuild {
            cmake {
                arguments += listOf("-DANDROID_STL=none")
            }
        }
    }

    signingConfigs {
        // This key is intentionally checked in and non-secret. It signs only
        // sideload/debug builds so every CI artifact can update the previous
        // sideload build in place. Play/release signing remains separate.
        create("sideloadDev") {
            storeFile = sideloadKeystoreFile
            storePassword = "lasso-dev"
            keyAlias = "lasso-dev"
            keyPassword = "lasso-dev"
        }

        if (uploadSigningConfigured) {
            create("playUpload") {
                storeFile = file(uploadKeystorePath!!)
                storePassword = uploadKeystorePassword
                keyAlias = uploadKeyAlias
                keyPassword = uploadKeyPassword
            }
        }
    }

    buildTypes {
        getByName("debug") {
            // Preserve the permanent Lasso Dev sideload/update channel while
            // release builds keep the established Play package name.
            applicationIdSuffix = ".lasso.dev"
            versionNameSuffix = "-dev"
            manifestPlaceholders["appLabel"] = "Analytic Continuation — Lasso Dev"
            signingConfig = signingConfigs.getByName("sideloadDev")
        }

        getByName("release") {
            isMinifyEnabled = false
            signingConfigs.findByName("playUpload")?.let {
                signingConfig = it
            }
        }
    }

    sourceSets {
        getByName("main") {
            // AGP source sets cannot consume Provider objects directly; the
            // explicit preBuild dependency below preserves generation order.
            assets.srcDir(generatedWegertAssets.get().asFile)
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}

tasks.named("preBuild").configure {
    dependsOn(assembleContinuationShader)
}

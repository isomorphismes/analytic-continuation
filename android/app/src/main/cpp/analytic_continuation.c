#include <android/asset_manager.h>
#include <android/input.h>
#include <android/log.h>
#include <android/native_activity.h>
#include <android_native_app_glue.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define LOG_TAG "AnalyticContinuation"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define MAX_ZEROS 32

static const float TAU = 6.28318530717958647692f;

static const char *VERTEX_SHADER =
    "#version 300 es\n"
    "precision highp float;\n"
    "layout(location = 0) in vec2 a_position;\n"
    "out vec2 v_ndc;\n"
    "void main() {\n"
    "    v_ndc = a_position;\n"
    "    gl_Position = vec4(a_position, 0.0, 1.0);\n"
    "}\n";

struct engine {
    struct android_app *app;

    EGLDisplay display;
    EGLSurface surface;
    EGLContext context;
    int32_t width;
    int32_t height;

    GLuint program;
    GLuint vao;
    GLuint vbo;
    GLint resolution_location;
    GLint zero_count_location;
    GLint zeros_location;
    GLint phase_location;
    GLint paused_location;

    float zeros[MAX_ZEROS][2];
    int zero_count;

    float phase;
    float phase_velocity;
    uint32_t random_state;
    double last_animation_time;
    bool paused;

    int candidate_zero;
    bool dragging_zero;
    bool moved;
    float down_x;
    float down_y;

    bool dirty;
    bool logged_first_frame;
};

static double monotonic_seconds(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (double)now.tv_sec + 1.0e-9 * (double)now.tv_nsec;
}

static float random_signed(struct engine *engine) {
    uint32_t value = engine->random_state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    engine->random_state = value;
    return 2.0f * ((float)(value & 0x00ffffffu) / 16777215.0f) - 1.0f;
}

static void initialize_lasso(struct engine *engine) {
    engine->zero_count = 3;
    engine->zeros[0][0] = -0.46f;
    engine->zeros[0][1] = 0.16f;
    engine->zeros[1][0] = 0.28f;
    engine->zeros[1][1] = 0.37f;
    engine->zeros[2][0] = 0.14f;
    engine->zeros[2][1] = -0.43f;

    engine->phase = 0.0f;
    engine->phase_velocity = 0.48f;
    engine->random_state = 0xa341316cu;
    engine->last_animation_time = monotonic_seconds();
    engine->paused = false;
    engine->candidate_zero = -1;
    engine->dragging_zero = false;
    engine->moved = false;
    engine->dirty = true;
}

static char *load_asset_text(AAssetManager *manager, const char *name) {
    AAsset *asset = AAssetManager_open(manager, name, AASSET_MODE_BUFFER);
    if (asset == NULL) {
        LOGE("could not open asset %s", name);
        return NULL;
    }

    off64_t length = AAsset_getLength64(asset);
    char *text = malloc((size_t)length + 1u);
    if (text == NULL) {
        AAsset_close(asset);
        return NULL;
    }

    off64_t offset = 0;
    while (offset < length) {
        int amount = AAsset_read(asset, text + offset, (size_t)(length - offset));
        if (amount <= 0) {
            free(text);
            AAsset_close(asset);
            LOGE("could not read asset %s", name);
            return NULL;
        }
        offset += amount;
    }

    text[length] = '\0';
    AAsset_close(asset);
    return text;
}

static GLuint compile_shader(GLenum type, const char *source) {
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, NULL);
    glCompileShader(shader);

    GLint compiled = GL_FALSE;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &compiled);
    if (compiled == GL_TRUE) {
        return shader;
    }

    GLint length = 0;
    glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &length);
    char *log = length > 0 ? malloc((size_t)length) : NULL;
    if (log != NULL) {
        glGetShaderInfoLog(shader, length, NULL, log);
        LOGE("shader compilation failed: %s", log);
        free(log);
    } else {
        LOGE("shader compilation failed");
    }
    glDeleteShader(shader);
    return 0;
}

static GLuint link_program(GLuint vertex_shader, GLuint fragment_shader) {
    GLuint program = glCreateProgram();
    glAttachShader(program, vertex_shader);
    glAttachShader(program, fragment_shader);
    glLinkProgram(program);

    GLint linked = GL_FALSE;
    glGetProgramiv(program, GL_LINK_STATUS, &linked);
    if (linked == GL_TRUE) {
        return program;
    }

    GLint length = 0;
    glGetProgramiv(program, GL_INFO_LOG_LENGTH, &length);
    char *log = length > 0 ? malloc((size_t)length) : NULL;
    if (log != NULL) {
        glGetProgramInfoLog(program, length, NULL, log);
        LOGE("program link failed: %s", log);
        free(log);
    } else {
        LOGE("program link failed");
    }
    glDeleteProgram(program);
    return 0;
}

static bool create_renderer(struct engine *engine) {
    static const GLfloat fullscreen_triangle[] = {
        -1.0f, -1.0f,
         3.0f, -1.0f,
        -1.0f,  3.0f
    };

    char *fragment_source = load_asset_text(
        engine->app->activity->assetManager,
        "continuation.frag"
    );
    if (fragment_source == NULL) {
        return false;
    }

    GLuint vertex_shader = compile_shader(GL_VERTEX_SHADER, VERTEX_SHADER);
    GLuint fragment_shader = compile_shader(GL_FRAGMENT_SHADER, fragment_source);
    free(fragment_source);

    if (vertex_shader == 0 || fragment_shader == 0) {
        if (vertex_shader != 0) glDeleteShader(vertex_shader);
        if (fragment_shader != 0) glDeleteShader(fragment_shader);
        return false;
    }

    engine->program = link_program(vertex_shader, fragment_shader);
    glDeleteShader(vertex_shader);
    glDeleteShader(fragment_shader);
    if (engine->program == 0) {
        return false;
    }

    engine->resolution_location = glGetUniformLocation(engine->program, "u_resolution");
    engine->zero_count_location = glGetUniformLocation(engine->program, "u_zero_count");
    engine->zeros_location = glGetUniformLocation(engine->program, "u_zeros[0]");
    engine->phase_location = glGetUniformLocation(engine->program, "u_phase");
    engine->paused_location = glGetUniformLocation(engine->program, "u_paused");

    if (
        engine->resolution_location < 0 ||
        engine->zero_count_location < 0 ||
        engine->zeros_location < 0 ||
        engine->phase_location < 0 ||
        engine->paused_location < 0
    ) {
        LOGE("lasso shader uniforms unavailable");
        return false;
    }

    glGenVertexArrays(1, &engine->vao);
    glBindVertexArray(engine->vao);

    glGenBuffers(1, &engine->vbo);
    glBindBuffer(GL_ARRAY_BUFFER, engine->vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(fullscreen_triangle), fullscreen_triangle, GL_STATIC_DRAW);
    glVertexAttribPointer(
        0,
        2,
        GL_FLOAT,
        GL_FALSE,
        2 * (GLsizei)sizeof(GLfloat),
        (const void *)0
    );
    glEnableVertexAttribArray(0);

    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
    glDisable(GL_SCISSOR_TEST);
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);

    LOGI("lasso renderer ready: GL_VERSION=%s GL_RENDERER=%s", glGetString(GL_VERSION), glGetString(GL_RENDERER));
    return true;
}

static bool initialize_display(struct engine *engine) {
    if (engine->app->window == NULL) {
        return false;
    }

    const EGLint config_attributes[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    const EGLint context_attributes[] = {
        EGL_CONTEXT_CLIENT_VERSION, 3,
        EGL_NONE
    };

    EGLDisplay display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (display == EGL_NO_DISPLAY || !eglInitialize(display, NULL, NULL)) {
        LOGE("eglInitialize failed: 0x%x", eglGetError());
        return false;
    }

    EGLConfig config = NULL;
    EGLint config_count = 0;
    if (
        !eglChooseConfig(display, config_attributes, &config, 1, &config_count) ||
        config_count != 1
    ) {
        LOGE("could not choose GLES3 EGL config: 0x%x", eglGetError());
        eglTerminate(display);
        return false;
    }

    EGLint format = 0;
    eglGetConfigAttrib(display, config, EGL_NATIVE_VISUAL_ID, &format);
    ANativeWindow_setBuffersGeometry(engine->app->window, 0, 0, format);

    EGLSurface surface = eglCreateWindowSurface(display, config, engine->app->window, NULL);
    EGLContext context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attributes);
    if (surface == EGL_NO_SURFACE || context == EGL_NO_CONTEXT) {
        LOGE("could not create EGL surface/context: 0x%x", eglGetError());
        if (surface != EGL_NO_SURFACE) eglDestroySurface(display, surface);
        if (context != EGL_NO_CONTEXT) eglDestroyContext(display, context);
        eglTerminate(display);
        return false;
    }

    if (!eglMakeCurrent(display, surface, surface, context)) {
        LOGE("eglMakeCurrent failed: 0x%x", eglGetError());
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        return false;
    }

    engine->display = display;
    engine->surface = surface;
    engine->context = context;
    eglQuerySurface(display, surface, EGL_WIDTH, &engine->width);
    eglQuerySurface(display, surface, EGL_HEIGHT, &engine->height);

    if (!create_renderer(engine)) {
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        eglDestroyContext(display, context);
        eglDestroySurface(display, surface);
        eglTerminate(display);
        engine->display = EGL_NO_DISPLAY;
        engine->surface = EGL_NO_SURFACE;
        engine->context = EGL_NO_CONTEXT;
        return false;
    }

    glViewport(0, 0, engine->width, engine->height);
    engine->last_animation_time = monotonic_seconds();
    engine->dirty = true;
    LOGI("lasso ready: surface=%dx%d zeros=%d", engine->width, engine->height, engine->zero_count);
    return true;
}

static void terminate_display(struct engine *engine) {
    if (engine->display == EGL_NO_DISPLAY) {
        return;
    }

    if (engine->vbo != 0) {
        glDeleteBuffers(1, &engine->vbo);
        engine->vbo = 0;
    }
    if (engine->vao != 0) {
        glDeleteVertexArrays(1, &engine->vao);
        engine->vao = 0;
    }
    if (engine->program != 0) {
        glDeleteProgram(engine->program);
        engine->program = 0;
    }

    eglMakeCurrent(engine->display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    if (engine->context != EGL_NO_CONTEXT) {
        eglDestroyContext(engine->display, engine->context);
    }
    if (engine->surface != EGL_NO_SURFACE) {
        eglDestroySurface(engine->display, engine->surface);
    }
    eglTerminate(engine->display);

    engine->display = EGL_NO_DISPLAY;
    engine->surface = EGL_NO_SURFACE;
    engine->context = EGL_NO_CONTEXT;
}

static void update_surface_size(struct engine *engine) {
    if (engine->display == EGL_NO_DISPLAY || engine->surface == EGL_NO_SURFACE) {
        return;
    }
    eglQuerySurface(engine->display, engine->surface, EGL_WIDTH, &engine->width);
    eglQuerySurface(engine->display, engine->surface, EGL_HEIGHT, &engine->height);
    glViewport(0, 0, engine->width, engine->height);
    engine->dirty = true;
}

static void draw_frame(struct engine *engine) {
    if (
        engine->display == EGL_NO_DISPLAY ||
        engine->program == 0 ||
        engine->width <= 0 ||
        engine->height <= 0
    ) {
        return;
    }

    glUseProgram(engine->program);
    glUniform2f(
        engine->resolution_location,
        (float)engine->width,
        (float)engine->height
    );
    glUniform1i(engine->zero_count_location, engine->zero_count);
    glUniform2fv(engine->zeros_location, MAX_ZEROS, &engine->zeros[0][0]);
    glUniform1f(engine->phase_location, engine->phase);
    glUniform1i(engine->paused_location, engine->paused ? 1 : 0);

    glBindVertexArray(engine->vao);
    glDrawArrays(GL_TRIANGLES, 0, 3);

    if (!engine->logged_first_frame) {
        GLubyte pixel[4] = {0, 0, 0, 0};
        glReadPixels(
            engine->width / 2,
            engine->height / 2,
            1,
            1,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            pixel
        );
        LOGI("lasso first frame: center rgba=%u,%u,%u,%u", pixel[0], pixel[1], pixel[2], pixel[3]);
        engine->logged_first_frame = true;
    }

    if (!eglSwapBuffers(engine->display, engine->surface)) {
        LOGE("eglSwapBuffers failed: 0x%x", eglGetError());
    }
    engine->dirty = false;
}

static float disk_pixel_radius(const struct engine *engine) {
    return 0.42f * fminf((float)engine->width, (float)engine->height);
}

static void screen_to_disk(
    const struct engine *engine,
    float x,
    float y,
    float output[2]
) {
    float scale = disk_pixel_radius(engine);
    output[0] = (x - 0.5f * (float)engine->width) / scale;
    output[1] = (0.5f * (float)engine->height - y) / scale;
}

static float control_radius(const struct engine *engine) {
    float radius = 0.052f * fminf((float)engine->width, (float)engine->height);
    if (radius < 28.0f) radius = 28.0f;
    if (radius > 42.0f) radius = 42.0f;
    return radius;
}

static bool pause_control_contains(const struct engine *engine, float x, float y) {
    float radius = control_radius(engine);
    float center_x = radius + 16.0f;
    float center_y = radius + 16.0f;
    return hypotf(x - center_x, y - center_y) <= radius;
}

static bool clear_control_contains(const struct engine *engine, float x, float y) {
    float radius = control_radius(engine);
    float center_x = (float)engine->width - radius - 16.0f;
    float center_y = radius + 16.0f;
    return hypotf(x - center_x, y - center_y) <= radius;
}

static int nearest_zero(const struct engine *engine, float x, float y) {
    if (engine->zero_count == 0 || engine->width <= 0 || engine->height <= 0) {
        return -1;
    }

    float point[2];
    screen_to_disk(engine, x, y, point);
    float scale = disk_pixel_radius(engine);
    float best_distance = 38.0f;
    int best_index = -1;

    for (int index = 0; index < engine->zero_count; ++index) {
        float dx = (point[0] - engine->zeros[index][0]) * scale;
        float dy = (point[1] - engine->zeros[index][1]) * scale;
        float distance = hypotf(dx, dy);
        if (distance < best_distance) {
            best_distance = distance;
            best_index = index;
        }
    }
    return best_index;
}

static void clamp_inside_disk(float point[2]) {
    float radius = hypotf(point[0], point[1]);
    const float limit = 0.965f;
    if (radius > limit && radius > 0.0f) {
        float scale = limit / radius;
        point[0] *= scale;
        point[1] *= scale;
    }
}

static void move_zero(struct engine *engine, int index, float x, float y) {
    if (index < 0 || index >= engine->zero_count) {
        return;
    }
    float point[2];
    screen_to_disk(engine, x, y, point);
    clamp_inside_disk(point);
    engine->zeros[index][0] = point[0];
    engine->zeros[index][1] = point[1];
    engine->dirty = true;
}

static void add_zero(struct engine *engine, float x, float y) {
    if (engine->zero_count >= MAX_ZEROS) {
        LOGI("zero ignored: limit=%d", MAX_ZEROS);
        return;
    }

    float point[2];
    screen_to_disk(engine, x, y, point);
    if (hypotf(point[0], point[1]) >= 0.965f) {
        return;
    }

    engine->zeros[engine->zero_count][0] = point[0];
    engine->zeros[engine->zero_count][1] = point[1];
    engine->zero_count += 1;
    engine->dirty = true;
    LOGI("zero added: %.6g%+.6gi count=%d", point[0], point[1], engine->zero_count);
}

static void clear_zeros(struct engine *engine) {
    engine->zero_count = 0;
    engine->dirty = true;
    LOGI("lasso zeros cleared");
}

static void toggle_pause(struct engine *engine) {
    engine->paused = !engine->paused;
    engine->last_animation_time = monotonic_seconds();
    engine->dirty = true;
    LOGI("lasso phase walk %s", engine->paused ? "paused" : "running");
}

static void advance_phase(struct engine *engine) {
    double now = monotonic_seconds();
    float dt = (float)(now - engine->last_animation_time);
    engine->last_animation_time = now;

    if (dt <= 0.0f) {
        return;
    }
    if (dt > 0.05f) {
        dt = 0.05f;
    }

    // Smooth stochastic motion on S^1: random acceleration with mild damping.
    // The phase itself is the single unconstrained real parameter modulo 2*pi.
    float noise = random_signed(engine);
    engine->phase_velocity += 1.15f * sqrtf(dt) * noise;
    engine->phase_velocity *= expf(-0.85f * dt);
    if (engine->phase_velocity > 1.6f) engine->phase_velocity = 1.6f;
    if (engine->phase_velocity < -1.6f) engine->phase_velocity = -1.6f;

    engine->phase += engine->phase_velocity * dt;
    if (engine->phase >= TAU || engine->phase <= -TAU) {
        engine->phase = fmodf(engine->phase, TAU);
    }
    engine->dirty = true;
}

static int32_t handle_input(struct android_app *app, AInputEvent *event) {
    struct engine *engine = app->userData;
    if (AInputEvent_getType(event) != AINPUT_EVENT_TYPE_MOTION) {
        return 0;
    }

    int32_t action = AMotionEvent_getAction(event);
    int32_t masked_action = action & AMOTION_EVENT_ACTION_MASK;
    size_t pointer_count = AMotionEvent_getPointerCount(event);

    switch (masked_action) {
        case AMOTION_EVENT_ACTION_DOWN: {
            float x = AMotionEvent_getX(event, 0);
            float y = AMotionEvent_getY(event, 0);

            if (pause_control_contains(engine, x, y)) {
                toggle_pause(engine);
                engine->candidate_zero = -1;
                engine->moved = true;
                return 1;
            }
            if (clear_control_contains(engine, x, y)) {
                clear_zeros(engine);
                engine->candidate_zero = -1;
                engine->moved = true;
                return 1;
            }

            engine->down_x = x;
            engine->down_y = y;
            engine->candidate_zero = nearest_zero(engine, x, y);
            engine->dragging_zero = false;
            engine->moved = false;
            return 1;
        }

        case AMOTION_EVENT_ACTION_POINTER_DOWN:
            engine->candidate_zero = -1;
            engine->dragging_zero = false;
            engine->moved = true;
            return 1;

        case AMOTION_EVENT_ACTION_MOVE: {
            if (pointer_count != 1) {
                return 1;
            }

            float x = AMotionEvent_getX(event, 0);
            float y = AMotionEvent_getY(event, 0);
            float distance = hypotf(x - engine->down_x, y - engine->down_y);
            if (distance > 10.0f) {
                engine->moved = true;
            }

            if (engine->moved && engine->candidate_zero >= 0) {
                engine->dragging_zero = true;
                move_zero(engine, engine->candidate_zero, x, y);
            }
            return 1;
        }

        case AMOTION_EVENT_ACTION_UP: {
            float x = AMotionEvent_getX(event, 0);
            float y = AMotionEvent_getY(event, 0);
            if (!engine->moved && !engine->dragging_zero) {
                // Tapping an existing marker intentionally adds another factor
                // at essentially the same point, giving a repeated zero.
                add_zero(engine, x, y);
            } else if (engine->dragging_zero && engine->candidate_zero >= 0) {
                LOGI(
                    "zero moved: index=%d to %.6g%+.6gi",
                    engine->candidate_zero,
                    engine->zeros[engine->candidate_zero][0],
                    engine->zeros[engine->candidate_zero][1]
                );
            }

            engine->candidate_zero = -1;
            engine->dragging_zero = false;
            engine->moved = false;
            return 1;
        }

        case AMOTION_EVENT_ACTION_CANCEL:
        case AMOTION_EVENT_ACTION_POINTER_UP:
            engine->candidate_zero = -1;
            engine->dragging_zero = false;
            engine->moved = false;
            return 1;

        default:
            return 0;
    }
}

static void handle_command(struct android_app *app, int32_t command) {
    struct engine *engine = app->userData;

    switch (command) {
        case APP_CMD_INIT_WINDOW:
            if (app->window != NULL && engine->display == EGL_NO_DISPLAY) {
                initialize_display(engine);
            }
            break;

        case APP_CMD_TERM_WINDOW:
            terminate_display(engine);
            break;

        case APP_CMD_WINDOW_RESIZED:
        case APP_CMD_CONTENT_RECT_CHANGED:
        case APP_CMD_CONFIG_CHANGED:
            update_surface_size(engine);
            break;

        case APP_CMD_GAINED_FOCUS:
            engine->last_animation_time = monotonic_seconds();
            engine->dirty = true;
            break;

        default:
            break;
    }
}

void android_main(struct android_app *app) {
    struct engine engine = {
        .app = app,
        .display = EGL_NO_DISPLAY,
        .surface = EGL_NO_SURFACE,
        .context = EGL_NO_CONTEXT,
        .candidate_zero = -1,
        .dirty = true,
        .logged_first_frame = false
    };
    initialize_lasso(&engine);

    app->userData = &engine;
    app->onAppCmd = handle_command;
    app->onInputEvent = handle_input;

    while (true) {
        int events = 0;
        struct android_poll_source *source = NULL;
        bool can_animate = engine.display != EGL_NO_DISPLAY && !engine.paused;
        int timeout = can_animate ? 16 : (engine.dirty ? 0 : -1);
        int ident = ALooper_pollOnce(timeout, NULL, &events, (void **)&source);

        if (ident >= 0 && source != NULL) {
            source->process(app, source);
        }

        if (app->destroyRequested != 0) {
            terminate_display(&engine);
            return;
        }

        if (engine.display != EGL_NO_DISPLAY && !engine.paused) {
            advance_phase(&engine);
        }

        if (engine.dirty) {
            draw_frame(&engine);
        }
    }
}

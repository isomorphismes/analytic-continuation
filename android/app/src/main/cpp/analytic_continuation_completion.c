#define android_main analytic_continuation_base_android_main
#include "analytic_continuation.c"
#undef android_main

#include "completion_state.h"

static struct completion_state COMPLETION;

static GLuint completion_program = 0;
static GLint completion_center_location = -1;
static GLint completion_half_height_location = -1;
static GLint completion_aspect_location = -1;
static GLint completion_resolution_location = -1;
static GLint completion_coefficients_location = -1;
static GLint completion_constraint_count_location = -1;
static GLint completion_constraint_domains_location = -1;

static bool create_completion_renderer(struct engine *engine) {
    char *fragment_source = load_asset_text(
        engine->app->activity->assetManager,
        "completion.frag"
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

    completion_program = link_program(vertex_shader, fragment_shader);
    glDeleteShader(vertex_shader);
    glDeleteShader(fragment_shader);
    if (completion_program == 0) {
        return false;
    }

    completion_center_location =
        glGetUniformLocation(completion_program, "u_center");
    completion_half_height_location =
        glGetUniformLocation(completion_program, "u_half_height");
    completion_aspect_location =
        glGetUniformLocation(completion_program, "u_aspect");
    completion_resolution_location =
        glGetUniformLocation(completion_program, "u_resolution");
    completion_coefficients_location =
        glGetUniformLocation(completion_program, "u_completion_coefficients[0]");
    completion_constraint_count_location =
        glGetUniformLocation(completion_program, "u_constraint_count");
    completion_constraint_domains_location =
        glGetUniformLocation(completion_program, "u_constraint_domains[0]");

    LOGI(
        "vibrating completion renderer ready: program=%u coefficients=%d constraints=%d",
        completion_program,
        completion_coefficients_location,
        completion_constraint_domains_location
    );
    return true;
}

static void destroy_completion_renderer(void) {
    if (completion_program != 0) {
        glDeleteProgram(completion_program);
        completion_program = 0;
    }
}

static void draw_completion_frame(struct engine *engine) {
    if (
        engine->display == EGL_NO_DISPLAY ||
        completion_program == 0 ||
        engine->width <= 0 ||
        engine->height <= 0
    ) {
        return;
    }

    float aspect = (float)engine->width / (float)engine->height;

    glUseProgram(completion_program);
    glUniform2f(
        completion_center_location,
        engine->center[0],
        engine->center[1]
    );
    glUniform1f(completion_half_height_location, engine->half_height);
    glUniform1f(completion_aspect_location, aspect);
    glUniform2f(
        completion_resolution_location,
        (float)engine->width,
        (float)engine->height
    );
    glUniform2fv(
        completion_coefficients_location,
        MAX_COMPLETION_COEFFICIENTS,
        &COMPLETION.coefficients[0][0]
    );
    glUniform1i(
        completion_constraint_count_location,
        COMPLETION.constraint_count
    );
    glUniform2fv(
        completion_constraint_domains_location,
        MAX_VALUE_CONSTRAINTS,
        &COMPLETION.constraint_domains[0][0]
    );

    glBindVertexArray(engine->vao);
    glDrawArrays(GL_TRIANGLES, 0, 3);

    if (!eglSwapBuffers(engine->display, engine->surface)) {
        LOGE("completion eglSwapBuffers failed: 0x%x", eglGetError());
    }
    engine->dirty = false;
}

static void reset_completion_experiment(struct engine *engine) {
    uint32_t next_seed = COMPLETION.random_state ^ 0x9e3779b9u;
    completion_state_initialize(&COMPLETION, next_seed);
    engine->center[0] = 0.0f;
    engine->center[1] = 0.0f;
    engine->half_height = 3.5f;
    engine->dirty = true;
    LOGI("vibrating completion reset");
}

static int32_t handle_completion_input(
    struct android_app *app,
    AInputEvent *event
) {
    struct engine *engine = app->userData;
    if (AInputEvent_getType(event) != AINPUT_EVENT_TYPE_MOTION) {
        return 0;
    }

    int32_t action = AMotionEvent_getAction(event);
    int32_t masked_action = action & AMOTION_EVENT_ACTION_MASK;
    size_t pointer_count = AMotionEvent_getPointerCount(event);

    switch (masked_action) {
        case AMOTION_EVENT_ACTION_DOWN:
            engine->gesture = GESTURE_SINGLE;
            engine->moved = false;
            engine->down_x = AMotionEvent_getX(event, 0);
            engine->down_y = AMotionEvent_getY(event, 0);
            engine->last_x = engine->down_x;
            engine->last_y = engine->down_y;
            return 1;

        case AMOTION_EVENT_ACTION_POINTER_DOWN:
            if (gesture_pointer_down_resets(engine->gesture, (int)pointer_count)) {
                reset_completion_experiment(engine);
                engine->gesture = GESTURE_BLOCKED;
                return 1;
            }
            if (gesture_pointer_down_starts_pinch(engine->gesture, (int)pointer_count)) {
                engine->gesture = GESTURE_PINCH;
                engine->moved = false;
                engine->pinch_last_distance = pointer_distance(event);
                pointer_midpoint(
                    event,
                    &engine->pinch_last_mid_x,
                    &engine->pinch_last_mid_y
                );
                return 1;
            }
            return 0;

        case AMOTION_EVENT_ACTION_MOVE:
            if (engine->gesture == GESTURE_SINGLE && pointer_count == 1) {
                float x = AMotionEvent_getX(event, 0);
                float y = AMotionEvent_getY(event, 0);
                float from_down_x = x - engine->down_x;
                float from_down_y = y - engine->down_y;
                if (hypotf(from_down_x, from_down_y) > 12.0f) {
                    engine->moved = true;
                }
                if (engine->moved) {
                    pan_by_pixels(
                        engine,
                        x - engine->last_x,
                        y - engine->last_y
                    );
                }
                engine->last_x = x;
                engine->last_y = y;
                return 1;
            }

            if (engine->gesture == GESTURE_PINCH && pointer_count >= 2) {
                float midpoint_x = 0.0f;
                float midpoint_y = 0.0f;
                pointer_midpoint(event, &midpoint_x, &midpoint_y);
                float distance = pointer_distance(event);

                pan_by_pixels(
                    engine,
                    midpoint_x - engine->pinch_last_mid_x,
                    midpoint_y - engine->pinch_last_mid_y
                );

                if (distance > 1.0f && engine->pinch_last_distance > 1.0f) {
                    engine->half_height *=
                        engine->pinch_last_distance / distance;
                    if (engine->half_height < 0.01f) {
                        engine->half_height = 0.01f;
                    }
                    if (engine->half_height > 100000.0f) {
                        engine->half_height = 100000.0f;
                    }
                    engine->dirty = true;
                }

                engine->pinch_last_distance = distance;
                engine->pinch_last_mid_x = midpoint_x;
                engine->pinch_last_mid_y = midpoint_y;
                return 1;
            }
            return engine->gesture == GESTURE_BLOCKED ? 1 : 0;

        case AMOTION_EVENT_ACTION_POINTER_UP:
            if (engine->gesture == GESTURE_PINCH && pointer_count == 2) {
                engine->gesture = GESTURE_BLOCKED;
                return 1;
            }
            return engine->gesture == GESTURE_BLOCKED ? 1 : 0;

        case AMOTION_EVENT_ACTION_UP:
            if (engine->gesture == GESTURE_SINGLE && !engine->moved) {
                float domain[2];
                screen_to_complex(
                    engine,
                    AMotionEvent_getX(event, 0),
                    AMotionEvent_getY(event, 0),
                    domain
                );

                if (completion_lock_current_value(&COMPLETION, domain)) {
                    LOGI(
                        "completion point %d locked at %.6g%+.6gi; %d complex dimensions remain",
                        COMPLETION.constraint_count,
                        domain[0],
                        domain[1],
                        completion_remaining_complex_dimensions(&COMPLETION)
                    );
                } else {
                    LOGI("completion point ignored: family already fixed or point repeated");
                }
                engine->dirty = true;
            }
            engine->gesture = GESTURE_NONE;
            engine->moved = false;
            return 1;

        case AMOTION_EVENT_ACTION_CANCEL:
            engine->gesture = GESTURE_NONE;
            engine->moved = false;
            return 1;

        default:
            return 0;
    }
}

static void handle_completion_command(
    struct android_app *app,
    int32_t command
) {
    struct engine *engine = app->userData;

    if (command == APP_CMD_TERM_WINDOW) {
        destroy_completion_renderer();
        handle_command(app, command);
        return;
    }

    handle_command(app, command);

    if (
        command == APP_CMD_INIT_WINDOW &&
        engine->display != EGL_NO_DISPLAY &&
        completion_program == 0
    ) {
        if (!create_completion_renderer(engine)) {
            LOGE("vibrating completion renderer unavailable; using base explorer");
        }
        engine->dirty = true;
    }
}

void android_main(struct android_app *app) {
    struct engine engine = {
        .app = app,
        .display = EGL_NO_DISPLAY,
        .surface = EGL_NO_SURFACE,
        .context = EGL_NO_CONTEXT,
        .gesture = GESTURE_NONE,
        .dirty = true,
        .logged_first_frame = false
    };

    initialize_function(&engine);
    completion_state_initialize(&COMPLETION, 0x2f6e2b1du);

    app->userData = &engine;
    app->onAppCmd = handle_completion_command;
    app->onInputEvent = handle_completion_input;

    while (true) {
        bool can_animate =
            engine.display != EGL_NO_DISPLAY &&
            completion_program != 0 &&
            completion_remaining_complex_dimensions(&COMPLETION) > 0;

        int events = 0;
        struct android_poll_source *source = NULL;
        int timeout = can_animate
            ? 16
            : (engine.dirty && engine.display != EGL_NO_DISPLAY ? 0 : -1);
        int ident = ALooper_pollOnce(
            timeout,
            NULL,
            &events,
            (void **)&source
        );

        if (ident >= 0 && source != NULL) {
            source->process(app, source);
        }

        if (app->destroyRequested != 0) {
            if (engine.display != EGL_NO_DISPLAY) {
                destroy_completion_renderer();
            }
            terminate_display(&engine);
            return;
        }

        if (can_animate) {
            completion_step(&COMPLETION);
            engine.dirty = true;
        }

        if (engine.dirty) {
            if (completion_program != 0) {
                draw_completion_frame(&engine);
            } else {
                draw_frame(&engine);
            }
        }
    }
}

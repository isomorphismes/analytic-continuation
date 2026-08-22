#include "../android/app/src/main/cpp/perturbation_workers.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <time.h>

static void sleep_milliseconds(long milliseconds) {
    struct timespec duration = {
        .tv_sec = milliseconds / 1000,
        .tv_nsec = (milliseconds % 1000) * 1000000L
    };
    nanosleep(&duration, NULL);
}

int main(void) {
    struct perturbation_system *system = NULL;
    assert(perturbation_system_start(&system));
    assert(system != NULL);

    perturbation_system_set_view(system, 1.25f, -0.75f, 3.5f, 0.5f);

    struct perturbation_snapshot snapshot = {0};
    for (int attempt = 0; attempt < 20 && snapshot.count == 0; ++attempt) {
        sleep_milliseconds(16);
        perturbation_system_copy_snapshot(system, &snapshot);
    }

    assert(snapshot.count > 0);
    assert(snapshot.count <= PERTURBATION_WORKER_COUNT);

    for (int index = 0; index < snapshot.count; ++index) {
        const struct perturbation_descriptor *item = &snapshot.items[index];
        assert(isfinite(item->disk_center[0]));
        assert(isfinite(item->disk_center[1]));
        assert(isfinite(item->inverse_radius));
        assert(isfinite(item->anchor[0]));
        assert(isfinite(item->anchor[1]));
        assert(isfinite(item->kernel_scale));
        assert(isfinite(item->phase_amplitude));
        assert(item->inverse_radius > 0.0f);

        float anchor_squared = item->anchor[0] * item->anchor[0]
            + item->anchor[1] * item->anchor[1];
        assert(anchor_squared < 1.0f);

        float one_minus_anchor_squared = 1.0f - anchor_squared;
        float expected_scale = one_minus_anchor_squared * one_minus_anchor_squared;
        assert(fabsf(item->kernel_scale - expected_scale) < 1.0e-5f);
        assert(fabsf(item->phase_amplitude) < 0.14f);
    }

    perturbation_system_stop(system);
    puts("perturbation workers: ok");
    return 0;
}

package org.isomorphisms.analyticcontinuation;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.SystemClock;
import android.test.InstrumentationTestCase;
import android.view.InputDevice;
import android.view.MotionEvent;

public final class PinchInstrumentationTest extends InstrumentationTestCase {
    private static MotionEvent.PointerProperties pointer(int id) {
        MotionEvent.PointerProperties properties = new MotionEvent.PointerProperties();
        properties.id = id;
        properties.toolType = MotionEvent.TOOL_TYPE_FINGER;
        return properties;
    }

    private static MotionEvent.PointerCoords coordinates(float x, float y) {
        MotionEvent.PointerCoords coordinates = new MotionEvent.PointerCoords();
        coordinates.x = x;
        coordinates.y = y;
        coordinates.pressure = 1.0f;
        coordinates.size = 1.0f;
        return coordinates;
    }

    private static MotionEvent motion(
        long downTime,
        int action,
        MotionEvent.PointerProperties[] properties,
        MotionEvent.PointerCoords[] coordinates
    ) {
        return MotionEvent.obtain(
            downTime,
            SystemClock.uptimeMillis(),
            action,
            properties.length,
            properties,
            coordinates,
            0,
            0,
            1.0f,
            1.0f,
            0,
            0,
            InputDevice.SOURCE_TOUCHSCREEN,
            0
        );
    }

    private static void send(Instrumentation instrumentation, MotionEvent event) {
        instrumentation.sendPointerSync(event);
        event.recycle();
    }

    private static void drag(
        Instrumentation instrumentation,
        float startX,
        float startY,
        float endX,
        float endY
    ) {
        long downTime = SystemClock.uptimeMillis();
        MotionEvent.PointerProperties[] onePointer = {pointer(0)};

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_DOWN,
                onePointer,
                new MotionEvent.PointerCoords[] {coordinates(startX, startY)}
            )
        );
        SystemClock.sleep(40);
        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_MOVE,
                onePointer,
                new MotionEvent.PointerCoords[] {coordinates(endX, endY)}
            )
        );
        SystemClock.sleep(40);
        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_UP,
                onePointer,
                new MotionEvent.PointerCoords[] {coordinates(endX, endY)}
            )
        );
    }

    public void testPinchThenDragExistingZeroAtZoomedScale() throws Exception {
        Instrumentation instrumentation = getInstrumentation();
        Intent intent = new Intent();
        intent.setClassName(
            instrumentation.getTargetContext().getPackageName(),
            "org.isomorphisms.analyticcontinuation.ExplorerActivity"
        );
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);

        Activity activity = instrumentation.startActivitySync(intent);
        instrumentation.waitForIdleSync();
        SystemClock.sleep(1200);

        int width = activity.getWindow().getDecorView().getWidth();
        int height = activity.getWindow().getDecorView().getHeight();
        assertTrue("activity width", width > 0);
        assertTrue("activity height", height > 0);

        float centerX = 0.5f * width;
        float centerY = 0.5f * height;
        float startHalfDistance = 80.0f;
        float finishHalfDistance = 180.0f;
        float expectedZoom = finishHalfDistance / startHalfDistance;

        long downTime = SystemClock.uptimeMillis();
        MotionEvent.PointerProperties first = pointer(0);
        MotionEvent.PointerProperties second = pointer(1);

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_DOWN,
                new MotionEvent.PointerProperties[] {first},
                new MotionEvent.PointerCoords[] {
                    coordinates(centerX - startHalfDistance, centerY)
                }
            )
        );
        SystemClock.sleep(40);

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_POINTER_DOWN |
                    (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT),
                new MotionEvent.PointerProperties[] {first, second},
                new MotionEvent.PointerCoords[] {
                    coordinates(centerX - startHalfDistance, centerY),
                    coordinates(centerX + startHalfDistance, centerY)
                }
            )
        );
        SystemClock.sleep(40);

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_MOVE,
                new MotionEvent.PointerProperties[] {first, second},
                new MotionEvent.PointerCoords[] {
                    coordinates(centerX - finishHalfDistance, centerY),
                    coordinates(centerX + finishHalfDistance, centerY)
                }
            )
        );
        SystemClock.sleep(60);

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_POINTER_UP |
                    (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT),
                new MotionEvent.PointerProperties[] {first, second},
                new MotionEvent.PointerCoords[] {
                    coordinates(centerX - finishHalfDistance, centerY),
                    coordinates(centerX + finishHalfDistance, centerY)
                }
            )
        );
        SystemClock.sleep(40);

        send(
            instrumentation,
            motion(
                downTime,
                MotionEvent.ACTION_UP,
                new MotionEvent.PointerProperties[] {first},
                new MotionEvent.PointerCoords[] {
                    coordinates(centerX - finishHalfDistance, centerY)
                }
            )
        );
        SystemClock.sleep(200);

        // The random-Lasso mode starts with a zero at z=-0.34. After the
        // pinch, its screen coordinate must use the zoomed view radius. If
        // input conversion ignores zoom, this drag will miss the zero.
        float viewRadius = 0.42f * Math.min(width, height) * expectedZoom;
        float zeroX = centerX - 0.34f * viewRadius;
        drag(instrumentation, zeroX, centerY, zeroX + 54.0f, centerY - 28.0f);
        SystemClock.sleep(250);

        activity.finish();
        instrumentation.waitForIdleSync();
    }
}

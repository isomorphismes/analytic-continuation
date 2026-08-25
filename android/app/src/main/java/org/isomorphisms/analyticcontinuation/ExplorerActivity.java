package org.isomorphisms.analyticcontinuation;

import android.app.NativeActivity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

/** Hosts the native EGL/OpenGL ES lasso explorer. */
public final class ExplorerActivity extends NativeActivity {
    private static final String LOG_TAG = "AnalyticContinuation";
    private static final String CI_TOUCH_SELF_TEST = "ci_touch_self_test";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        FormulaOverlayView formula = new FormulaOverlayView(this);
        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            dp(112),
            Gravity.TOP
        );
        addContentView(formula, layout);

        if (BuildConfig.DEBUG && getIntent().getBooleanExtra(CI_TOUCH_SELF_TEST, false)) {
            View decor = getWindow().getDecorView();
            decor.postDelayed(() -> runCiTouchSelfTest(decor), 1800L);
        }
    }

    private int dp(float value) {
        return Math.round(TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            value,
            getResources().getDisplayMetrics()
        ));
    }

    @Override
    public void onBackPressed() {
        Log.i(LOG_TAG, "lasso back requested");
        finish();
    }

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

    private void sendCiMotion(
        long downTime,
        int action,
        MotionEvent.PointerProperties[] properties,
        MotionEvent.PointerCoords[] coordinates
    ) {
        MotionEvent event = MotionEvent.obtain(
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
        dispatchTouchEvent(event);
        event.recycle();
    }

    /**
     * Debug-only release gate: route a real two-pointer MotionEvent sequence
     * through this activity, then drag the initial zero at its zoomed screen
     * coordinate. Native logs prove both pinch scaling and zoom-aware hit tests.
     */
    private void runCiTouchSelfTest(View decor) {
        int width = decor.getWidth();
        int height = decor.getHeight();
        if (width <= 0 || height <= 0) {
            Log.e(LOG_TAG, "ci touch self-test: decor has no size");
            return;
        }

        Log.i(LOG_TAG, "ci touch self-test: surface=" + width + "x" + height);

        float centerX = 0.5f * width;
        float centerY = 0.5f * height;
        float startHalfDistance = 80.0f;
        float finishHalfDistance = 180.0f;
        float expectedZoom = finishHalfDistance / startHalfDistance;
        float viewRadius = 0.42f * Math.min(width, height) * expectedZoom;
        float zeroX = centerX - 0.34f * viewRadius;

        MotionEvent.PointerProperties first = pointer(0);
        MotionEvent.PointerProperties second = pointer(1);
        long pinchDown = SystemClock.uptimeMillis();

        sendCiMotion(
            pinchDown,
            MotionEvent.ACTION_DOWN,
            new MotionEvent.PointerProperties[] {first},
            new MotionEvent.PointerCoords[] {
                coordinates(centerX - startHalfDistance, centerY)
            }
        );

        decor.postDelayed(() -> sendCiMotion(
            pinchDown,
            MotionEvent.ACTION_POINTER_DOWN |
                (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT),
            new MotionEvent.PointerProperties[] {first, second},
            new MotionEvent.PointerCoords[] {
                coordinates(centerX - startHalfDistance, centerY),
                coordinates(centerX + startHalfDistance, centerY)
            }
        ), 60L);

        decor.postDelayed(() -> sendCiMotion(
            pinchDown,
            MotionEvent.ACTION_MOVE,
            new MotionEvent.PointerProperties[] {first, second},
            new MotionEvent.PointerCoords[] {
                coordinates(centerX - finishHalfDistance, centerY),
                coordinates(centerX + finishHalfDistance, centerY)
            }
        ), 120L);

        decor.postDelayed(() -> sendCiMotion(
            pinchDown,
            MotionEvent.ACTION_POINTER_UP |
                (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT),
            new MotionEvent.PointerProperties[] {first, second},
            new MotionEvent.PointerCoords[] {
                coordinates(centerX - finishHalfDistance, centerY),
                coordinates(centerX + finishHalfDistance, centerY)
            }
        ), 180L);

        decor.postDelayed(() -> sendCiMotion(
            pinchDown,
            MotionEvent.ACTION_UP,
            new MotionEvent.PointerProperties[] {first},
            new MotionEvent.PointerCoords[] {
                coordinates(centerX - finishHalfDistance, centerY)
            }
        ), 240L);

        long dragDown = pinchDown + 520L;
        decor.postDelayed(() -> sendCiMotion(
            dragDown,
            MotionEvent.ACTION_DOWN,
            new MotionEvent.PointerProperties[] {first},
            new MotionEvent.PointerCoords[] {coordinates(zeroX, centerY)}
        ), 520L);

        decor.postDelayed(() -> sendCiMotion(
            dragDown,
            MotionEvent.ACTION_MOVE,
            new MotionEvent.PointerProperties[] {first},
            new MotionEvent.PointerCoords[] {coordinates(zeroX + 54.0f, centerY - 28.0f)}
        ), 590L);

        decor.postDelayed(() -> sendCiMotion(
            dragDown,
            MotionEvent.ACTION_UP,
            new MotionEvent.PointerProperties[] {first},
            new MotionEvent.PointerCoords[] {coordinates(zeroX + 54.0f, centerY - 28.0f)}
        ), 660L);
    }

    /**
     * A compact, touch-transparent description of the function that the native
     * renderer is actually evaluating. It deliberately stays structural: the
     * random holomorphic walk continuously changes the lasso coefficients, so
     * pretending rounded decimal coefficients were exact would be misleading.
     */
    private static final class FormulaOverlayView extends View {
        private static final String[] LINES = {
            "w = φ⁻¹(z)",
            "φ(w) = w + c₂w² + c₃w³ + c₄w⁴ + c₅w⁵ + c₆w⁶",
            "f(z) = eⁱᵗ (∏ᵢ B(aᵢ,w)) ÷ (∏ⱼ B(pⱼ,w))",
            "B(a,w) = (w−a) ÷ (1−āw)"
        };

        private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint boxPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final float density;

        FormulaOverlayView(Context context) {
            super(context);
            density = context.getResources().getDisplayMetrics().density;
            setClickable(false);
            setFocusable(false);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);

            textPaint.setColor(Color.rgb(246, 243, 232));
            textPaint.setTextSize(TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_SP,
                14.0f,
                context.getResources().getDisplayMetrics()
            ));
            textPaint.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));

            boxPaint.setColor(Color.argb(188, 18, 18, 18));
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            return false;
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);

            float lineHeight = 20.0f * density;
            float padding = 8.0f * density;
            float left = Math.max(132.0f * density, 0.16f * getWidth());
            float maxTextWidth = 0.0f;
            for (String line : LINES) {
                maxTextWidth = Math.max(maxTextWidth, textPaint.measureText(line));
            }

            float right = Math.min(
                getWidth() - 14.0f * density,
                left + maxTextWidth + 2.0f * padding
            );
            float top = 8.0f * density;
            float bottom = top + LINES.length * lineHeight + 2.0f * padding;
            RectF box = new RectF(left, top, right, bottom);
            canvas.drawRoundRect(box, 7.0f * density, 7.0f * density, boxPaint);

            float x = left + padding;
            float baseline = top + padding - textPaint.ascent();
            for (String line : LINES) {
                canvas.drawText(line, x, baseline, textPaint);
                baseline += lineHeight;
            }
        }
    }
}

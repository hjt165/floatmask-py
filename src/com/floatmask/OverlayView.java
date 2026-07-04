package com.floatmask;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;

public class OverlayView extends View {
    private WindowManager wm;
    private WindowManager.LayoutParams params;
    private Paint paint;
    private RectF rect = new RectF();
    private float cornerRadius = 20f;

    private int overlayColor = 0x80757575;
    private float posX = 100, posY = 100;
    private int viewWidth = 400, viewHeight = 300;
    private float overlayAlpha = 1.0f;
    private int screenWidth = 1080;

    // Touch state (read by Python via Pyjnius)
    public static int touchAction = -1;  // 0=down, 1=move, 2=up, 3=double-tap, 4=slide-end
    public static float touchX, touchY;
    public static float touchDX, touchDY;
    public static float touchStartX, touchStartY;
    public static long lastTapTime = 0;
    public static boolean inResizeArea = false;
    public static float slideAlpha = 1.0f;

    private float lastRawX, lastRawY;
    private boolean dragging = false;
    private boolean isSlide = false;
    private float slideStartAlpha = 1.0f;

    public OverlayView(Context context) {
        super(context);
        wm = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        paint = new Paint();
        paint.setAntiAlias(true);
        paint.setStyle(Paint.Style.FILL);
        android.util.DisplayMetrics dm = context.getResources().getDisplayMetrics();
        screenWidth = dm.widthPixels;
        screenHeight = dm.heightPixels;
        updatePaintColor();
    }

    private int screenHeight = 1920;

    private void updatePaintColor() {
        int a = (int) ((Color.alpha(overlayColor) / 255.0f) * 255);
        int r = Color.red(overlayColor);
        int g = Color.green(overlayColor);
        int b = Color.blue(overlayColor);
        paint.setColor(Color.argb(a, r, g, b));
    }

    private void applyAlphaToColor(float alpha) {
        int r = Color.red(overlayColor);
        int g = Color.green(overlayColor);
        int b = Color.blue(overlayColor);
        overlayColor = Color.argb((int)(alpha * 255), r, g, b);
        overlayAlpha = alpha;
        updatePaintColor();
    }

    public void show(int x, int y, int w, int h) {
        posX = x; posY = y;
        viewWidth = w; viewHeight = h;

        params = new WindowManager.LayoutParams(
            w, h,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        );
        params.gravity = Gravity.TOP | Gravity.START;
        params.x = x;
        params.y = y;

        final WindowManager.LayoutParams p = params;
        new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> {
            wm.addView(this, p);
        });
    }

    public void hide() {
        new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> {
            try { wm.removeView(this); } catch (Exception e) {}
        });
    }

    public void moveTo(float x, float y) {
        posX = x; posY = y;
        params.x = (int) x;
        params.y = (int) y;
        new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> {
            try { wm.updateViewLayout(this, params); } catch (Exception e) {}
        });
    }

    public void resizeTo(int w, int h) {
        viewWidth = w; viewHeight = h;
        params.width = w;
        params.height = h;
        new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> {
            try { wm.updateViewLayout(this, params); } catch (Exception e) {}
        });
    }

    public void setColor(int color) {
        overlayColor = color;
        updatePaintColor();
        postInvalidate();
    }

    public void setOverlayAlpha(float alpha) {
        int r = Color.red(overlayColor);
        int g = Color.green(overlayColor);
        int b = Color.blue(overlayColor);
        overlayColor = Color.argb((int)(alpha * 255), r, g, b);
        overlayAlpha = alpha;
        updatePaintColor();
        postInvalidate();
    }

    public float getPosX() { return posX; }
    public float getPosY() { return posY; }
    public int getOverlayWidth() { return viewWidth; }
    public int getOverlayHeight() { return viewHeight; }
    public int getOverlayColor() { return overlayColor; }
    public float getOverlayAlpha() { return overlayAlpha; }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        rect.set(0, 0, viewWidth, viewHeight);
        canvas.drawRoundRect(rect, cornerRadius, cornerRadius, paint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float rawX = event.getRawX();
        float rawY = event.getRawY();

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                lastRawX = rawX;
                lastRawY = rawY;
                touchStartX = rawX;
                touchStartY = rawY;
                dragging = true;
                isSlide = false;

                float localX = rawX - posX;
                float localY = rawY - posY;
                inResizeArea = (localX > viewWidth - 80 && localY > viewHeight - 80);

                touchAction = 0;
                touchX = rawX;
                touchY = rawY;
                touchDX = 0;
                touchDY = 0;
                slideStartAlpha = overlayAlpha;
                return true;

            case MotionEvent.ACTION_MOVE:
                if (dragging) {
                    touchDX = rawX - lastRawX;
                    touchDY = rawY - lastRawY;
                    lastRawX = rawX;
                    lastRawY = rawY;

                    float totalDY = rawY - touchStartY;
                    float totalDX = rawX - touchStartX;
                    float distFromStart = (float) Math.sqrt(totalDX * totalDX + totalDY * totalDY);

                    // Detect vertical slide: fast vertical movement with little horizontal movement
                    if (!isSlide && !inResizeArea && distFromStart > 30
                        && Math.abs(totalDY) > Math.abs(totalDX) * 2
                        && Math.abs(totalDY) > 30) {
                        isSlide = true;
                    }

                    if (isSlide) {
                        // Vertical slide → adjust alpha
                        float newAlpha = slideStartAlpha - totalDY / (screenHeight * 0.5f);
                        newAlpha = Math.max(0.1f, Math.min(1.0f, newAlpha));
                        applyAlphaToColor(newAlpha);
                        slideAlpha = newAlpha;
                        postInvalidate();
                    } else if (inResizeArea) {
                        int newW = Math.max(150, viewWidth + (int) touchDX);
                        int newH = Math.max(150, viewHeight - (int) touchDY);
                        resizeTo(newW, newH);
                    } else {
                        float newX = posX + touchDX;
                        float newY = posY + touchDY;
                        moveTo(newX, newY);
                    }

                    touchAction = 1;
                    touchX = rawX;
                    touchY = rawY;
                }
                return true;

            case MotionEvent.ACTION_UP:
                dragging = false;

                if (isSlide) {
                    touchAction = 4;  // slide end
                    isSlide = false;
                    touchX = rawX;
                    touchY = rawY;
                    touchDX = 0;
                    touchDY = 0;
                    return true;
                }

                long now = System.currentTimeMillis();
                float distX = Math.abs(rawX - touchStartX);
                float distY = Math.abs(rawY - touchStartY);
                long elapsed = now - lastTapTime;

                if (elapsed < 400 && distX < 20 && distY < 20) {
                    touchAction = 3;
                    lastTapTime = 0;
                } else {
                    touchAction = 2;
                    lastTapTime = now;
                }

                touchX = rawX;
                touchY = rawY;
                touchDX = 0;
                touchDY = 0;
                return true;
        }
        return super.onTouchEvent(event);
    }
}

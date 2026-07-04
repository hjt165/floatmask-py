package com.floatmask;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;

public class OverlayView extends View {
    private WindowManager wm;
    private WindowManager.LayoutParams params;
    private Paint paint;
    private Paint toolbarPaint;
    private Paint iconPaint;
    private Paint textPaint;
    private RectF rect = new RectF();
    private RectF toolbarRect = new RectF();
    private RectF lockRect = new RectF();
    private RectF dragRect = new RectF();
    private RectF closeRect = new RectF();
    private float cornerRadius = 20f;

    private int overlayColor = 0x80757575;
    private float posX = 100, posY = 100;
    private int viewWidth = 400, viewHeight = 300;
    private float overlayAlpha = 1.0f;
    private int screenWidth = 1080;
    private int screenHeight = 1920;

    // Toolbar
    private static final int TOOLBAR_HEIGHT = 80;
    private static final int ICON_SIZE = 56;
    private static final int ICON_MARGIN = 12;
    private static final int ICON_TOTAL = ICON_SIZE + ICON_MARGIN * 2;

    // Touch state (read by Python via Pyjnius)
    public static int touchAction = -1;
    public static float touchX, touchY;
    public static float touchDX, touchDY;
    public static float touchStartX, touchStartY;
    public static long lastTapTime = 0;
    public static boolean inResizeArea = false;
    public static float slideAlpha = 1.0f;
    public static boolean isLocked = false;

    private float lastRawX, lastRawY;
    private boolean dragging = false;
    private boolean isSlide = false;
    private boolean isDragHandle = false;
    private boolean toolbarButtonTapped = false;
    private float slideStartAlpha = 1.0f;

    public OverlayView(Context context) {
        super(context);
        wm = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);

        paint = new Paint();
        paint.setAntiAlias(true);
        paint.setStyle(Paint.Style.FILL);
        updatePaintColor();

        toolbarPaint = new Paint();
        toolbarPaint.setAntiAlias(true);
        toolbarPaint.setStyle(Paint.Style.FILL);
        toolbarPaint.setColor(0xCC222222);

        iconPaint = new Paint();
        iconPaint.setAntiAlias(true);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(3f);
        iconPaint.setStrokeCap(Paint.Cap.ROUND);
        iconPaint.setStrokeJoin(Paint.Join.ROUND);

        textPaint = new Paint();
        textPaint.setAntiAlias(true);
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(28);
        textPaint.setTextAlign(Paint.Align.CENTER);
        textPaint.setTypeface(Typeface.DEFAULT_BOLD);

        android.util.DisplayMetrics dm = context.getResources().getDisplayMetrics();
        screenWidth = dm.widthPixels;
        screenHeight = dm.heightPixels;
    }

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
            w, h + TOOLBAR_HEIGHT,
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
        params.height = h + TOOLBAR_HEIGHT;
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

    public void setLocked(boolean locked) {
        isLocked = locked;
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

        int totalH = viewHeight + TOOLBAR_HEIGHT;

        // Draw toolbar background (top bar)
        toolbarRect.set(0, 0, viewWidth, TOOLBAR_HEIGHT);
        canvas.drawRoundRect(toolbarRect, cornerRadius, cornerRadius, toolbarPaint);
        // Fill bottom corners of toolbar
        canvas.drawRect(0, cornerRadius, viewWidth, TOOLBAR_HEIGHT, toolbarPaint);

        // Draw overlay body
        rect.set(0, TOOLBAR_HEIGHT, viewWidth, totalH);
        canvas.drawRoundRect(rect, cornerRadius, cornerRadius, paint);
        // Fill top corners of body to connect with toolbar
        canvas.drawRect(0, TOOLBAR_HEIGHT, viewWidth, TOOLBAR_HEIGHT + cornerRadius, paint);

        // Calculate icon positions
        float cy = TOOLBAR_HEIGHT / 2f;
        float lockCx = ICON_MARGIN + ICON_SIZE / 2f;
        float closeCx = viewWidth - ICON_MARGIN - ICON_SIZE / 2f;
        float dragCx = viewWidth / 2f;

        // Lock icon hit area
        lockRect.set(lockCx - ICON_SIZE / 2f - ICON_MARGIN, 0,
                     lockCx + ICON_SIZE / 2f + ICON_MARGIN, TOOLBAR_HEIGHT);

        // Close icon hit area
        closeRect.set(closeCx - ICON_SIZE / 2f - ICON_MARGIN, 0,
                      closeCx + ICON_SIZE / 2f + ICON_MARGIN, TOOLBAR_HEIGHT);

        // Drag handle hit area
        dragRect.set(dragCx - 30, 0, dragCx + 30, TOOLBAR_HEIGHT);

        // Draw lock icon (left)
        iconPaint.setColor(isLocked ? 0xFFFF6B6B : 0xFF4CAF50);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(4f);
        float lx = lockCx - 12;
        float ly = cy - 10;
        // Lock body
        canvas.drawRoundRect(lx - 8, ly + 4, lx + 12, ly + 18, 3, 3, iconPaint);
        // Lock shackle
        RectF shackle = new RectF(lx - 4, ly - 6, lx + 8, ly + 8);
        canvas.drawArc(shackle, 180, 180, false, iconPaint);

        // Draw drag handle (center) - 3 horizontal lines
        iconPaint.setColor(0xAAFFFFFF);
        iconPaint.setStrokeWidth(3.5f);
        for (int i = -1; i <= 1; i++) {
            float lineY = cy + i * 10;
            canvas.drawLine(dragCx - 16, lineY, dragCx + 16, lineY, iconPaint);
        }

        // Draw close icon (right) - X mark
        iconPaint.setColor(0xFFFF6B6B);
        iconPaint.setStrokeWidth(4f);
        float cx = closeCx;
        canvas.drawLine(cx - 12, cy - 12, cx + 12, cy + 12, iconPaint);
        canvas.drawLine(cx + 12, cy - 12, cx - 12, cy + 12, iconPaint);
    }

    private boolean isInToolbar(float localY) {
        return localY < TOOLBAR_HEIGHT;
    }

    private boolean isInLockArea(float localX, float localY) {
        return isInToolbar(localY) && localX < viewWidth * 0.33f;
    }

    private boolean isInCloseArea(float localX, float localY) {
        return isInToolbar(localY) && localX > viewWidth * 0.67f;
    }

    private boolean isInDragArea(float localX, float localY) {
        return isInToolbar(localY) && !isInLockArea(localX, localY) && !isInCloseArea(localX, localY);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float rawX = event.getRawX();
        float rawY = event.getRawY();
        float localX = rawX - posX;
        float localY = rawY - posY;

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                lastRawX = rawX;
                lastRawY = rawY;
                touchStartX = rawX;
                touchStartY = rawY;
                dragging = true;
                isSlide = false;
                isDragHandle = false;
                toolbarButtonTapped = false;

                // Check toolbar buttons
                if (isInLockArea(localX, localY)) {
                    isLocked = !isLocked;
                    postInvalidate();
                    touchAction = 5; // lock toggle
                    dragging = false;
                    toolbarButtonTapped = true;
                    return true;
                }

                if (isInCloseArea(localX, localY)) {
                    touchAction = 6; // close
                    dragging = false;
                    toolbarButtonTapped = true;
                    return true;
                }

                if (isInDragArea(localX, localY)) {
                    isDragHandle = true;
                }

                // Resize area check (bottom-right corner of body)
                inResizeArea = !isLocked && !isInToolbar(localY)
                    && localX > viewWidth - 80 && (localY - TOOLBAR_HEIGHT) > viewHeight - 80;

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

                    if (!isSlide && !isDragHandle && !inResizeArea && distFromStart > 30
                        && Math.abs(totalDY) > Math.abs(totalDX) * 2
                        && Math.abs(totalDY) > 30) {
                        isSlide = true;
                    }

                    if (isDragHandle) {
                        float newX = posX + touchDX;
                        float newY = posY + touchDY;
                        moveTo(newX, newY);
                    } else if (isSlide) {
                        float newAlpha = slideStartAlpha - totalDY / (screenHeight * 0.5f);
                        newAlpha = Math.max(0.1f, Math.min(1.0f, newAlpha));
                        applyAlphaToColor(newAlpha);
                        slideAlpha = newAlpha;
                        postInvalidate();
                    } else if (inResizeArea) {
                        int newW = Math.max(150, viewWidth + (int) touchDX);
                        int newH = Math.max(150, viewHeight - (int) touchDY);
                        resizeTo(newW, newH);
                    } else if (!isLocked || isDragHandle) {
                        float newX = posX + touchDX;
                        float newY = posY + touchDY;
                        moveTo(newX, newY);
                    }

                    touchAction = 1;
                    touchX = rawX;
                    touchY = rawY;
                } else if (isDragHandle) {
                    // Drag handle movement (even when locked)
                    touchDX = rawX - lastRawX;
                    touchDY = rawY - lastRawY;
                    lastRawX = rawX;
                    lastRawY = rawY;
                    float newX = posX + touchDX;
                    float newY = posY + touchDY;
                    moveTo(newX, newY);
                    touchAction = 1;
                    touchX = rawX;
                    touchY = rawY;
                }
                return true;

            case MotionEvent.ACTION_UP:
                dragging = false;
                isDragHandle = false;

                if (toolbarButtonTapped) {
                    toolbarButtonTapped = false;
                    return true;
                }

                if (isSlide) {
                    touchAction = 4;
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
